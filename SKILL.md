---
name: openclaw-model-usage
description: Local-first OpenClaw model usage inspection without CodexBar. Use when asked for current model, recent model usage, usage breakdown by model, token totals, cost summaries, or per-agent/daily model usage from local OpenClaw session logs.
---

# OpenClaw Model Usage

Use this skill to inspect local OpenClaw model usage directly from session JSONL files.

## When to use

Use this skill when the user asks for:
- the current / most recent model in use
- usage summaries by provider/model
- token totals by model
- cost summaries by model when available
- recent usage rows
- per-agent model usage
- daily model usage summaries

## Why this skill exists

This skill is a portable, local-first replacement for CodexBar-dependent model usage workflows.

It reads OpenClaw session logs directly and does not depend on external usage tools.

## Script

Run the bundled script:

```bash
python {baseDir}/scripts/model_usage.py current
python {baseDir}/scripts/model_usage.py summary
python {baseDir}/scripts/model_usage.py agents
python {baseDir}/scripts/model_usage.py daily --limit 20
```

## JSON output

```bash
python {baseDir}/scripts/model_usage.py summary --json --pretty
python {baseDir}/scripts/model_usage.py agents --json --pretty
```

## Inputs

Default source:

```bash
~/.openclaw/agents/*/sessions/*.jsonl
```

Override with:

```bash
python {baseDir}/scripts/model_usage.py summary --root /path/to/.openclaw/agents
```

## References

If you need field-level sourcing details, read:

- `references/discovery.md`
