---
name: openclaw-model-usage
description: Inspect local OpenClaw model usage directly from session logs. Use when asked for the current model, recent model usage, usage breakdown by model, token totals, cost summaries, per-agent usage, or daily model usage summaries.
---

# OpenClaw Model Usage

Use this skill to inspect local OpenClaw model usage directly from session JSONL files.

## When to use

Use this skill when the user asks for:
- the current / most recent model in use
- recent model usage
- usage summaries by provider/model
- token totals by model
- cost summaries by model when available
- per-agent model usage
- daily model usage summaries

## What it does

This skill provides a local-first replacement for external model-usage workflows.

It reads OpenClaw session logs directly and does not depend on CodexBar.

## Script usage

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
python {baseDir}/scripts/model_usage.py rows --limit 20 --json --pretty
```

## Inputs

Default source:

```bash
~/.openclaw/agents/*/sessions/*.jsonl
```

Override the root if needed:

```bash
python {baseDir}/scripts/model_usage.py summary --root /path/to/.openclaw/agents
```

## References

If you need field-level sourcing details, read:

- `references/discovery.md`
