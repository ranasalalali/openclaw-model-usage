#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_ROOT = Path.home() / ".openclaw" / "agents"


@dataclass
class SessionMeta:
    agent: str
    session_id: str
    session_key: str | None = None
    display_name: str | None = None
    label: str | None = None
    channel: str | None = None
    group_channel: str | None = None
    group_id: str | None = None
    space: str | None = None
    chat_type: str | None = None
    status: str | None = None
    model_provider: str | None = None
    model: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    spawned_by: str | None = None
    spawned_by_session_id: str | None = None
    spawn_depth: int | None = None
    subagent_role: str | None = None
    session_file: str | None = None
    cwd: str | None = None


@dataclass
class UsageRow:
    timestamp: str
    agent: str
    session_id: str
    session_key: str | None
    session_label: str | None
    parent_session_key: str | None
    parent_session_id: str | None
    spawn_depth: int | None
    subagent_role: str | None
    channel: str | None
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
    p.add_argument(
        "command",
        choices=["summary", "current", "recent", "rows", "agents", "daily", "sessions", "subagents", "session-tree"],
        nargs="?",
        default="summary",
    )
    p.add_argument("--root", default=str(DEFAULT_ROOT), help="OpenClaw agents root (default: ~/.openclaw/agents)")
    p.add_argument("--agent", action="append", help="Limit to one or more agents")
    p.add_argument("--provider", action="append", help="Limit to one or more providers")
    p.add_argument("--model", action="append", help="Limit to one or more models")
    p.add_argument("--session-id", action="append", help="Limit to one or more session IDs")
    p.add_argument("--channel", action="append", help="Limit to one or more channels")
    p.add_argument("--since-days", type=int, default=30, help="Look back N days (default: 30, 0 = all)")
    p.add_argument("--limit", type=int, default=10, help="Limit rows for recent/rows/daily/session listings")
    p.add_argument("--json", action="store_true", help="Emit JSON output")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return p


def iter_agent_dirs(root: Path, agents: set[str] | None) -> Iterable[tuple[str, Path]]:
    if not root.exists():
        return
    for agent_dir in sorted(root.iterdir()):
        if not agent_dir.is_dir():
            continue
        agent = agent_dir.name
        if agents and agent not in agents:
            continue
        yield agent, agent_dir


def iter_session_files(root: Path, agents: set[str] | None) -> Iterable[tuple[str, Path]]:
    for agent, agent_dir in iter_agent_dirs(root, agents):
        sessions_dir = agent_dir / "sessions"
        if not sessions_dir.exists():
            continue
        for path in sorted(sessions_dir.glob("*.jsonl")):
            yield agent, path


def parse_timestamp(value: str | None) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def epoch_ms_to_iso(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def load_sessions_index(root: Path, agents: set[str] | None) -> dict[tuple[str, str], SessionMeta]:
    by_session: dict[tuple[str, str], SessionMeta] = {}
    key_to_session_id: dict[tuple[str, str], str] = {}

    for agent, agent_dir in iter_agent_dirs(root, agents):
        index_path = agent_dir / "sessions" / "sessions.json"
        if not index_path.exists():
            continue
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue

        for session_key, item in data.items():
            if not isinstance(item, dict):
                continue
            session_id = item.get("sessionId")
            if not isinstance(session_id, str):
                continue
            meta = SessionMeta(
                agent=agent,
                session_id=session_id,
                session_key=session_key if isinstance(session_key, str) else None,
                display_name=item.get("displayName") if isinstance(item.get("displayName"), str) else None,
                label=item.get("label") if isinstance(item.get("label"), str) else None,
                channel=item.get("channel") if isinstance(item.get("channel"), str) else None,
                group_channel=item.get("groupChannel") if isinstance(item.get("groupChannel"), str) else None,
                group_id=item.get("groupId") if isinstance(item.get("groupId"), str) else None,
                space=item.get("space") if isinstance(item.get("space"), str) else None,
                chat_type=item.get("chatType") if isinstance(item.get("chatType"), str) else None,
                status=item.get("status") if isinstance(item.get("status"), str) else None,
                model_provider=item.get("modelProvider") if isinstance(item.get("modelProvider"), str) else None,
                model=item.get("model") if isinstance(item.get("model"), str) else None,
                started_at=epoch_ms_to_iso(item.get("startedAt")),
                updated_at=epoch_ms_to_iso(item.get("updatedAt")),
                spawned_by=item.get("spawnedBy") if isinstance(item.get("spawnedBy"), str) else None,
                spawned_by_session_id=None,
                spawn_depth=int(item.get("spawnDepth")) if isinstance(item.get("spawnDepth"), int) else None,
                subagent_role=item.get("subagentRole") if isinstance(item.get("subagentRole"), str) else None,
                session_file=item.get("sessionFile") if isinstance(item.get("sessionFile"), str) else None,
                cwd=item.get("spawnedWorkspaceDir") if isinstance(item.get("spawnedWorkspaceDir"), str) else None,
            )
            by_session[(agent, session_id)] = meta
            if meta.session_key:
                key_to_session_id[(agent, meta.session_key)] = session_id

    for meta in by_session.values():
        if meta.spawned_by:
            meta.spawned_by_session_id = key_to_session_id.get((meta.agent, meta.spawned_by))

    return by_session


def load_session_headers(root: Path, agents: set[str] | None) -> dict[tuple[str, str], dict[str, Any]]:
    headers: dict[tuple[str, str], dict[str, Any]] = {}
    for agent, path in iter_session_files(root, agents):
        session_id = path.stem
        try:
            with path.open("r", encoding="utf-8") as handle:
                first_line = handle.readline().strip()
        except OSError:
            continue
        if not first_line:
            continue
        try:
            obj = json.loads(first_line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "session":
            continue
        headers[(agent, session_id)] = obj
    return headers


def merge_session_meta(index_meta: SessionMeta | None, header: dict[str, Any] | None, agent: str, session_id: str) -> SessionMeta:
    meta = index_meta or SessionMeta(agent=agent, session_id=session_id)
    if header:
        if isinstance(header.get("timestamp"), str) and not meta.started_at:
            meta.started_at = header["timestamp"]
        if isinstance(header.get("cwd"), str) and not meta.cwd:
            meta.cwd = header["cwd"]
    if not meta.session_file:
        meta.session_file = str(DEFAULT_ROOT / agent / "sessions" / f"{session_id}.jsonl")
    return meta


def load_rows(
    root: Path,
    agents: set[str] | None,
    providers: set[str] | None,
    models: set[str] | None,
    session_ids: set[str] | None,
    channels: set[str] | None,
    since_days: int,
) -> tuple[list[UsageRow], dict[tuple[str, str], SessionMeta]]:
    rows: list[UsageRow] = []
    cutoff = None
    if since_days and since_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    session_index = load_sessions_index(root, agents)
    session_headers = load_session_headers(root, agents)
    session_meta: dict[tuple[str, str], SessionMeta] = {}

    for agent, path in iter_session_files(root, agents):
        session_id = path.stem
        meta = merge_session_meta(session_index.get((agent, session_id)), session_headers.get((agent, session_id)), agent, session_id)
        session_meta[(agent, session_id)] = meta
        if session_ids and session_id not in session_ids:
            continue
        if channels and (meta.channel not in channels):
            continue
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
                            session_key=meta.session_key,
                            session_label=meta.label or meta.display_name,
                            parent_session_key=meta.spawned_by,
                            parent_session_id=meta.spawned_by_session_id,
                            spawn_depth=meta.spawn_depth,
                            subagent_role=meta.subagent_role,
                            channel=meta.channel,
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
    return rows, session_meta


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
        "sessions": set(),
        "last_timestamp": None,
    })
    for row in rows:
        item = by_model[(row.provider, row.model)]
        item["calls"] += 1
        item["input_tokens"] += row.input_tokens
        item["output_tokens"] += row.output_tokens
        item["cache_read_tokens"] += row.cache_read_tokens
        item["cache_write_tokens"] += row.cache_write_tokens
        item["total_tokens"] += row.total_tokens
        item["cost_total_usd"] += row.cost_total_usd
        item["agents"].add(row.agent)
        item["sessions"].add(row.session_id)
        item["last_timestamp"] = row.timestamp
    models_out = []
    for (provider, model), item in sorted(by_model.items(), key=lambda kv: kv[1]["cost_total_usd"], reverse=True):
        models_out.append({
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
            "sessions": len(item["sessions"]),
            "last_timestamp": item["last_timestamp"],
        })
    return {"rows": len(rows), "models": models_out}


def summarise_by_agent(rows: list[UsageRow]) -> dict[str, Any]:
    by_agent: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "calls": 0,
        "total_tokens": 0,
        "cost_total_usd": 0.0,
        "models": set(),
        "sessions": set(),
        "last_timestamp": None,
    })
    for row in rows:
        item = by_agent[row.agent]
        item["calls"] += 1
        item["total_tokens"] += row.total_tokens
        item["cost_total_usd"] += row.cost_total_usd
        item["models"].add(f"{row.provider}/{row.model}")
        item["sessions"].add(row.session_id)
        item["last_timestamp"] = row.timestamp
    agents_out = []
    for agent, item in sorted(by_agent.items(), key=lambda kv: kv[1]["cost_total_usd"], reverse=True):
        agents_out.append({
            "agent": agent,
            "calls": item["calls"],
            "sessions": len(item["sessions"]),
            "total_tokens": item["total_tokens"],
            "cost_total_usd": round(item["cost_total_usd"], 6),
            "models": sorted(item["models"]),
            "last_timestamp": item["last_timestamp"],
        })
    return {"rows": len(rows), "agents": agents_out}


def summarise_daily(rows: list[UsageRow]) -> dict[str, Any]:
    by_day: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(lambda: {"calls": 0, "total_tokens": 0, "cost_total_usd": 0.0})
    for row in rows:
        key = (row.timestamp[:10], row.provider, row.model)
        item = by_day[key]
        item["calls"] += 1
        item["total_tokens"] += row.total_tokens
        item["cost_total_usd"] += row.cost_total_usd
    daily_out = []
    for (day, provider, model), item in sorted(by_day.items(), key=lambda kv: (kv[0][0], kv[1]["cost_total_usd"]), reverse=True):
        daily_out.append({
            "date": day,
            "provider": provider,
            "model": model,
            "calls": item["calls"],
            "total_tokens": item["total_tokens"],
            "cost_total_usd": round(item["cost_total_usd"], 6),
        })
    return {"rows": len(rows), "daily": daily_out}


def summarise_by_session(rows: list[UsageRow], session_meta: dict[tuple[str, str], SessionMeta]) -> dict[str, Any]:
    by_session: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "calls": 0,
        "total_tokens": 0,
        "cost_total_usd": 0.0,
        "models": set(),
        "first_timestamp": None,
        "last_timestamp": None,
    })
    for row in rows:
        key = (row.agent, row.session_id)
        item = by_session[key]
        item["calls"] += 1
        item["total_tokens"] += row.total_tokens
        item["cost_total_usd"] += row.cost_total_usd
        item["models"].add(f"{row.provider}/{row.model}")
        item["first_timestamp"] = item["first_timestamp"] or row.timestamp
        item["last_timestamp"] = row.timestamp
    sessions_out = []
    for key, item in sorted(by_session.items(), key=lambda kv: (kv[1]["cost_total_usd"], kv[1]["last_timestamp"] or ""), reverse=True):
        meta = session_meta.get(key) or SessionMeta(agent=key[0], session_id=key[1])
        sessions_out.append({
            "agent": key[0],
            "session_id": key[1],
            "session_key": meta.session_key,
            "label": meta.label or meta.display_name,
            "channel": meta.channel,
            "spawn_depth": meta.spawn_depth,
            "subagent_role": meta.subagent_role,
            "parent_session_key": meta.spawned_by,
            "parent_session_id": meta.spawned_by_session_id,
            "calls": item["calls"],
            "total_tokens": item["total_tokens"],
            "cost_total_usd": round(item["cost_total_usd"], 6),
            "models": sorted(item["models"]),
            "started_at": meta.started_at or item["first_timestamp"],
            "last_timestamp": item["last_timestamp"],
            "status": meta.status,
        })
    return {"rows": len(rows), "sessions": sessions_out}


def summarise_subagents(rows: list[UsageRow], session_meta: dict[tuple[str, str], SessionMeta]) -> dict[str, Any]:
    session_summary = summarise_by_session(rows, session_meta)["sessions"]
    subagents = [item for item in session_summary if item.get("spawn_depth") is not None or item.get("parent_session_id") or item.get("parent_session_key")]
    return {"rows": len(rows), "subagents": subagents}


def summarise_session_tree(rows: list[UsageRow], session_meta: dict[tuple[str, str], SessionMeta]) -> dict[str, Any]:
    sessions = summarise_by_session(rows, session_meta)["sessions"]
    nodes = {item["session_id"]: {**item, "children": []} for item in sessions}
    roots: list[dict[str, Any]] = []
    for item in nodes.values():
        parent_id = item.get("parent_session_id")
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(item)
        else:
            roots.append(item)

    def rollup(node: dict[str, Any]) -> tuple[int, float, int]:
        total_tokens = int(node.get("total_tokens") or 0)
        total_cost = float(node.get("cost_total_usd") or 0.0)
        total_calls = int(node.get("calls") or 0)
        for child in node["children"]:
            child_tokens, child_cost, child_calls = rollup(child)
            total_tokens += child_tokens
            total_cost += child_cost
            total_calls += child_calls
        node["tree_total_tokens"] = total_tokens
        node["tree_cost_total_usd"] = round(total_cost, 6)
        node["tree_calls"] = total_calls
        node["children"].sort(key=lambda item: (item.get("tree_cost_total_usd") or 0.0, item.get("last_timestamp") or ""), reverse=True)
        return total_tokens, total_cost, total_calls

    for root in roots:
        rollup(root)
    roots.sort(key=lambda item: (item.get("tree_cost_total_usd") or 0.0, item.get("last_timestamp") or ""), reverse=True)
    return {"rows": len(rows), "trees": roots}


def fmt_money(value: float) -> str:
    return f"${value:,.4f}"


def render_text_summary(data: dict[str, Any]) -> str:
    lines = [f"Usage records: {data['rows']}", "Models:"]
    for item in data["models"]:
        lines.append(f"- {item['provider']} / {item['model']}: {fmt_money(item['cost_total_usd'])}, {item['total_tokens']:,} tokens, {item['calls']} calls across {item['sessions']} sessions")
    return "\n".join(lines)


def render_text_agents(data: dict[str, Any]) -> str:
    lines = [f"Usage records: {data['rows']}", "Agents:"]
    for item in data["agents"]:
        lines.append(f"- {item['agent']}: {fmt_money(item['cost_total_usd'])}, {item['total_tokens']:,} tokens, {item['calls']} calls across {item['sessions']} sessions")
    return "\n".join(lines)


def render_text_daily(data: dict[str, Any], limit: int) -> str:
    lines = [f"Usage records: {data['rows']}", "Daily:"]
    for item in data["daily"][:limit]:
        lines.append(f"- {item['date']} | {item['provider']}/{item['model']}: {fmt_money(item['cost_total_usd'])}, {item['total_tokens']:,} tokens, {item['calls']} calls")
    return "\n".join(lines)


def render_text_current(rows: list[UsageRow]) -> str:
    if not rows:
        return "No usage rows found."
    row = rows[-1]
    extra = f"\nSession: {row.session_id}"
    if row.session_label:
        extra += f"\nLabel: {row.session_label}"
    if row.parent_session_id:
        extra += f"\nParent session: {row.parent_session_id}"
    return "\n".join([f"Current model: {row.provider} / {row.model}", f"Agent: {row.agent}", f"Timestamp: {row.timestamp}", f"Tokens: {row.total_tokens:,}", f"Cost: {fmt_money(row.cost_total_usd)}"]) + extra


def render_text_recent(rows: list[UsageRow], limit: int) -> str:
    lines = []
    for row in rows[-limit:][::-1]:
        label = f" [{row.session_label}]" if row.session_label else ""
        lines.append(f"- {row.timestamp} | {row.agent} | {row.session_id}{label} | {row.provider}/{row.model} | {row.total_tokens:,} tokens | {fmt_money(row.cost_total_usd)}")
    return "\n".join(lines) if lines else "No usage rows found."


def render_text_sessions(data: dict[str, Any], limit: int, key: str = "sessions") -> str:
    items = data[key][:limit]
    heading = "Subagents:" if key == "subagents" else "Sessions:"
    lines = [f"Usage records: {data['rows']}", heading]
    for item in items:
        label = f" | {item['label']}" if item.get('label') else ""
        parent = f" | parent {item['parent_session_id']}" if item.get('parent_session_id') else ""
        depth = f" | depth {item['spawn_depth']}" if item.get('spawn_depth') is not None else ""
        lines.append(f"- {item['agent']} | {item['session_id']}{label}{parent}{depth}: {fmt_money(item['cost_total_usd'])}, {item['total_tokens']:,} tokens, {item['calls']} calls")
    return "\n".join(lines)


def render_tree_node(node: dict[str, Any], depth: int = 0) -> list[str]:
    indent = "  " * depth
    label = f" [{node['label']}]" if node.get("label") else ""
    line = f"{indent}- {node['agent']} | {node['session_id']}{label} | direct {fmt_money(node['cost_total_usd'])}/{node['total_tokens']:,} tok | tree {fmt_money(node['tree_cost_total_usd'])}/{node['tree_total_tokens']:,} tok"
    lines = [line]
    for child in node["children"]:
        lines.extend(render_tree_node(child, depth + 1))
    return lines


def render_text_session_tree(data: dict[str, Any], limit: int) -> str:
    lines = [f"Usage records: {data['rows']}", "Session trees:"]
    for root in data["trees"][:limit]:
        lines.extend(render_tree_node(root))
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    rows, session_meta = load_rows(
        root=Path(args.root).expanduser(),
        agents=set(args.agent) if args.agent else None,
        providers=set(args.provider) if args.provider else None,
        models=set(args.model) if args.model else None,
        session_ids=set(args.session_id) if args.session_id else None,
        channels=set(args.channel) if args.channel else None,
        since_days=args.since_days,
    )

    command = args.command
    if command == "summary":
        payload: Any = summarise_by_model(rows)
    elif command == "agents":
        payload = summarise_by_agent(rows)
    elif command == "daily":
        payload = summarise_daily(rows)
    elif command == "sessions":
        payload = summarise_by_session(rows, session_meta)
    elif command == "subagents":
        payload = summarise_subagents(rows, session_meta)
    elif command == "session-tree":
        payload = summarise_session_tree(rows, session_meta)
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
    elif command == "sessions":
        print(render_text_sessions(payload, args.limit))
    elif command == "subagents":
        print(render_text_sessions(payload, args.limit, key="subagents"))
    elif command == "session-tree":
        print(render_text_session_tree(payload, args.limit))
    elif command == "current":
        print(render_text_current(rows))
    else:
        print(render_text_recent(rows, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
