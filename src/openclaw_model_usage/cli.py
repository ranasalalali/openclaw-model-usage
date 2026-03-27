#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_ROOT = Path.home() / ".openclaw" / "agents"


@dataclass
class UsageRow:
    timestamp: str
    agent: str
    session_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    total_tokens: int
    cost_input_usd: float
    cost_output_usd: float
    cost_cache_read_usd: float
    cost_cache_write_usd: float
    cost_total_usd: float


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Summarize local OpenClaw model usage from session JSONL files.")
    p.add_argument("command", choices=["summary", "current", "recent", "rows", "agents", "daily"], nargs="?", default="summary")
    p.add_argument("--root", default=str(DEFAULT_ROOT), help="OpenClaw agents root (default: ~/.openclaw/agents)")
    p.add_argument("--agent", action="append", help="Limit to one or more agents")
    p.add_argument("--provider", action="append", help="Limit to one or more providers")
    p.add_argument("--model", action="append", help="Limit to one or more models")
    p.add_argument("--since-days", type=int, default=30, help="Look back N days (default: 30, 0 = all)")
    p.add_argument("--limit", type=int, default=10, help="Limit rows for recent/rows/daily output")
    p.add_argument("--json", action="store_true", help="Emit JSON output")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return p


def iter_session_files(root: Path, agents: set[str] | None) -> Iterable[tuple[str, Path]]:
    if not root.exists():
        return
    for agent_dir in sorted(root.iterdir()):
        if not agent_dir.is_dir():
            continue
        agent = agent_dir.name
        if agents and agent not in agents:
            continue
        sessions_dir = agent_dir / "sessions"
        if not sessions_dir.exists():
            continue
        for path in sorted(sessions_dir.glob("*.jsonl")):
            yield agent, path


def parse_timestamp(value: str) -> datetime | None:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def load_rows(root: Path, agents: set[str] | None, providers: set[str] | None, models: set[str] | None, since_days: int) -> list[UsageRow]:
    rows: list[UsageRow] = []
    cutoff = None
    if since_days and since_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    for agent, path in iter_session_files(root, agents):
        session_id = path.stem
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") != "message":
                        continue
                    message = obj.get("message") or {}
                    if message.get("role") != "assistant":
                        continue
                    usage = message.get("usage") or {}
                    provider = message.get("provider")
                    model = message.get("model")
                    ts = obj.get("timestamp")
                    if not isinstance(provider, str) or not isinstance(model, str) or not isinstance(ts, str):
                        continue
                    dt = parse_timestamp(ts)
                    if cutoff and (dt is None or dt < cutoff):
                        continue
                    if providers and provider not in providers:
                        continue
                    if models and model not in models:
                        continue
                    cost = usage.get("cost") or {}
                    rows.append(
                        UsageRow(
                            timestamp=ts,
                            agent=agent,
                            session_id=session_id,
                            provider=provider,
                            model=model,
                            input_tokens=int(usage.get("input") or 0),
                            output_tokens=int(usage.get("output") or 0),
                            cache_read_tokens=int(usage.get("cacheRead") or 0),
                            cache_write_tokens=int(usage.get("cacheWrite") or 0),
                            total_tokens=int(usage.get("totalTokens") or 0),
                            cost_input_usd=float(cost.get("input") or 0.0),
                            cost_output_usd=float(cost.get("output") or 0.0),
                            cost_cache_read_usd=float(cost.get("cacheRead") or 0.0),
                            cost_cache_write_usd=float(cost.get("cacheWrite") or 0.0),
                            cost_total_usd=float(cost.get("total") or 0.0),
                        )
                    )
        except OSError:
            continue
    rows.sort(key=lambda r: r.timestamp)
    return rows


def summarise_by_model(rows: list[UsageRow]) -> dict[str, Any]:
    by_model: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "cost_total_usd": 0.0,
        "agents": set(),
        "last_timestamp": None,
    })
    for row in rows:
        key = (row.provider, row.model)
        item = by_model[key]
        item["calls"] += 1
        item["input_tokens"] += row.input_tokens
        item["output_tokens"] += row.output_tokens
        item["cache_read_tokens"] += row.cache_read_tokens
        item["cache_write_tokens"] += row.cache_write_tokens
        item["total_tokens"] += row.total_tokens
        item["cost_total_usd"] += row.cost_total_usd
        item["agents"].add(row.agent)
        item["last_timestamp"] = row.timestamp
    models = []
    for (provider, model), item in sorted(by_model.items(), key=lambda kv: kv[1]["cost_total_usd"], reverse=True):
        models.append({
            "provider": provider,
            "model": model,
            "calls": item["calls"],
            "input_tokens": item["input_tokens"],
            "output_tokens": item["output_tokens"],
            "cache_read_tokens": item["cache_read_tokens"],
            "cache_write_tokens": item["cache_write_tokens"],
            "total_tokens": item["total_tokens"],
            "cost_total_usd": round(item["cost_total_usd"], 6),
            "agents": sorted(item["agents"]),
            "last_timestamp": item["last_timestamp"],
        })
    return {"rows": len(rows), "models": models}


def summarise_by_agent(rows: list[UsageRow]) -> dict[str, Any]:
    by_agent: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "calls": 0,
        "total_tokens": 0,
        "cost_total_usd": 0.0,
        "models": set(),
        "last_timestamp": None,
    })
    for row in rows:
        item = by_agent[row.agent]
        item["calls"] += 1
        item["total_tokens"] += row.total_tokens
        item["cost_total_usd"] += row.cost_total_usd
        item["models"].add(f"{row.provider}/{row.model}")
        item["last_timestamp"] = row.timestamp
    agents = []
    for agent, item in sorted(by_agent.items(), key=lambda kv: kv[1]["cost_total_usd"], reverse=True):
        agents.append({
            "agent": agent,
            "calls": item["calls"],
            "total_tokens": item["total_tokens"],
            "cost_total_usd": round(item["cost_total_usd"], 6),
            "models": sorted(item["models"]),
            "last_timestamp": item["last_timestamp"],
        })
    return {"rows": len(rows), "agents": agents}


def summarise_daily(rows: list[UsageRow]) -> dict[str, Any]:
    by_day: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(lambda: {
        "calls": 0,
        "total_tokens": 0,
        "cost_total_usd": 0.0,
    })
    for row in rows:
        day = row.timestamp[:10]
        key = (day, row.provider, row.model)
        item = by_day[key]
        item["calls"] += 1
        item["total_tokens"] += row.total_tokens
        item["cost_total_usd"] += row.cost_total_usd
    days = []
    for (day, provider, model), item in sorted(by_day.items(), key=lambda kv: (kv[0][0], kv[1]["cost_total_usd"]), reverse=True):
        days.append({
            "date": day,
            "provider": provider,
            "model": model,
            "calls": item["calls"],
            "total_tokens": item["total_tokens"],
            "cost_total_usd": round(item["cost_total_usd"], 6),
        })
    return {"rows": len(rows), "daily": days}


def fmt_money(value: float) -> str:
    return f"${value:,.4f}"


def render_text_summary(data: dict[str, Any]) -> str:
    lines = [f"Rows: {data['rows']}", "Models:"]
    for item in data["models"]:
        lines.append(
            f"- {item['provider']} / {item['model']}: {fmt_money(item['cost_total_usd'])}, "
            f"{item['total_tokens']:,} tokens, {item['calls']} calls"
        )
    return "\n".join(lines)


def render_text_agents(data: dict[str, Any]) -> str:
    lines = [f"Rows: {data['rows']}", "Agents:"]
    for item in data["agents"]:
        lines.append(
            f"- {item['agent']}: {fmt_money(item['cost_total_usd'])}, "
            f"{item['total_tokens']:,} tokens, {item['calls']} calls"
        )
    return "\n".join(lines)


def render_text_daily(data: dict[str, Any], limit: int) -> str:
    lines = [f"Rows: {data['rows']}", "Daily:"]
    for item in data['daily'][:limit]:
        lines.append(
            f"- {item['date']} | {item['provider']}/{item['model']}: {fmt_money(item['cost_total_usd'])}, "
            f"{item['total_tokens']:,} tokens, {item['calls']} calls"
        )
    return "\n".join(lines)


def render_text_current(rows: list[UsageRow]) -> str:
    if not rows:
        return "No usage rows found."
    row = rows[-1]
    return "\n".join([
        f"Current model: {row.provider} / {row.model}",
        f"Agent: {row.agent}",
        f"Timestamp: {row.timestamp}",
        f"Tokens: {row.total_tokens:,}",
        f"Cost: {fmt_money(row.cost_total_usd)}",
    ])


def render_text_recent(rows: list[UsageRow], limit: int) -> str:
    lines = []
    for row in rows[-limit:][::-1]:
        lines.append(
            f"- {row.timestamp} | {row.agent} | {row.provider}/{row.model} | "
            f"{row.total_tokens:,} tokens | {fmt_money(row.cost_total_usd)}"
        )
    return "\n".join(lines) if lines else "No usage rows found."


def main() -> int:
    args = build_parser().parse_args()
    rows = load_rows(
        root=Path(args.root).expanduser(),
        agents=set(args.agent) if args.agent else None,
        providers=set(args.provider) if args.provider else None,
        models=set(args.model) if args.model else None,
        since_days=args.since_days,
    )

    command = args.command
    if command == "summary":
        payload: Any = summarise_by_model(rows)
    elif command == "agents":
        payload = summarise_by_agent(rows)
    elif command == "daily":
        payload = summarise_daily(rows)
    elif command == "current":
        payload = asdict(rows[-1]) if rows else None
    elif command == "recent":
        payload = [asdict(r) for r in rows[-args.limit:][::-1]]
    elif command == "rows":
        payload = [asdict(r) for r in rows[-args.limit:]]
    else:
        raise AssertionError("unexpected command")

    if args.json:
        print(json.dumps(payload, indent=2 if args.pretty else None))
        return 0

    if command == "summary":
        print(render_text_summary(payload))
    elif command == "agents":
        print(render_text_agents(payload))
    elif command == "daily":
        print(render_text_daily(payload, args.limit))
    elif command == "current":
        print(render_text_current(rows))
    else:
        print(render_text_recent(rows, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
