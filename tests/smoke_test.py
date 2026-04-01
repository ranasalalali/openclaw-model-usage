#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "model_usage.py"
FIXTURE_ROOT = ROOT / "tests" / "fixtures_root"
SESSION_DIR = FIXTURE_ROOT / "sample-agent" / "sessions"
FIXTURE_PARENT = ROOT / "tests" / "fixtures" / "sample_parent_usage.jsonl"
FIXTURE_CHILD = ROOT / "tests" / "fixtures" / "sample_subagent_usage.jsonl"
FIXTURE_SESSIONS = ROOT / "tests" / "fixtures" / "sample_sessions.json"


PYTHON = ROOT / ".venv" / "bin" / "python"


def run(*args: str) -> str:
    python = str(PYTHON if PYTHON.exists() else Path(sys.executable))
    cmd = [python, str(SCRIPT), *args]
    return subprocess.check_output(cmd, text=True)


def main() -> int:
    if FIXTURE_ROOT.exists():
        shutil.rmtree(FIXTURE_ROOT)
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    (SESSION_DIR / "parent-session.jsonl").write_text(FIXTURE_PARENT.read_text())
    (SESSION_DIR / "child-session.jsonl").write_text(FIXTURE_CHILD.read_text())
    (SESSION_DIR / "sessions.json").write_text(FIXTURE_SESSIONS.read_text())

    summary = json.loads(run("summary", "--root", str(FIXTURE_ROOT), "--json"))
    assert summary["rows"] == 3
    assert summary["models"][0]["model"] == "gpt-5.4"
    assert summary["models"][0]["total_tokens"] == 2500
    assert summary["models"][0]["sessions"] == 1

    current = json.loads(run("current", "--root", str(FIXTURE_ROOT), "--json"))
    assert current["model"] == "kimi-k2.5:cloud"
    assert current["parent_session_id"] == "parent-session"
    assert current["session_label"] == "sample-subagent-task"

    agents = json.loads(run("agents", "--root", str(FIXTURE_ROOT), "--json"))
    assert agents["agents"][0]["agent"] == "sample-agent"
    assert agents["agents"][0]["sessions"] == 2

    sessions = json.loads(run("sessions", "--root", str(FIXTURE_ROOT), "--json"))
    assert len(sessions["sessions"]) == 2
    child = next(item for item in sessions["sessions"] if item["session_id"] == "child-session")
    assert child["parent_session_id"] == "parent-session"
    assert child["spawn_depth"] == 1

    subagents = json.loads(run("subagents", "--root", str(FIXTURE_ROOT), "--json"))
    assert len(subagents["subagents"]) == 1
    assert subagents["subagents"][0]["session_id"] == "child-session"

    tree = json.loads(run("session-tree", "--root", str(FIXTURE_ROOT), "--json"))
    assert len(tree["trees"]) == 1
    assert tree["trees"][0]["session_id"] == "parent-session"
    assert tree["trees"][0]["tree_total_tokens"] == 3100
    assert tree["trees"][0]["children"][0]["session_id"] == "child-session"

    daily = json.loads(run("daily", "--root", str(FIXTURE_ROOT), "--json"))
    assert len(daily["daily"]) >= 2

    rows = json.loads(run("rows", "--root", str(FIXTURE_ROOT), "--session-id", "child-session", "--json"))
    assert len(rows) == 1
    assert rows[0]["session_id"] == "child-session"

    print("smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
