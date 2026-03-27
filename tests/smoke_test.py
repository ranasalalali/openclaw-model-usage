#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "model_usage.py"
FIXTURE_ROOT = ROOT / "tests" / "fixtures_root"
SESSION_DIR = FIXTURE_ROOT / "sample-agent" / "sessions"
FIXTURE_FILE = SESSION_DIR / "sample.jsonl"
SOURCE_FIXTURE = ROOT / "tests" / "fixtures" / "sample_usage.jsonl"


def run(*args: str) -> str:
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.check_output(cmd, text=True)


def main() -> int:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURE_FILE.write_text(SOURCE_FIXTURE.read_text())

    summary = json.loads(run("summary", "--root", str(FIXTURE_ROOT), "--json"))
    assert summary["rows"] == 3
    assert summary["models"][0]["model"] == "gpt-5.4"
    assert summary["models"][0]["total_tokens"] == 2500

    current = json.loads(run("current", "--root", str(FIXTURE_ROOT), "--json"))
    assert current["model"] == "kimi-k2.5:cloud"

    agents = json.loads(run("agents", "--root", str(FIXTURE_ROOT), "--json"))
    assert agents["agents"][0]["agent"] == "sample-agent"

    daily = json.loads(run("daily", "--root", str(FIXTURE_ROOT), "--json"))
    assert len(daily["daily"]) >= 2

    print("smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
