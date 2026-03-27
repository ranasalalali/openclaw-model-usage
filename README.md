# openclaw-model-usage

A portable AgentSkill and Python CLI for inspecting local OpenClaw model usage directly from session logs.

## Overview

`openclaw-model-usage` summarizes local model usage from OpenClaw session JSONL files.

It can answer questions such as:
- what model is currently being used?
- what models have been used recently?
- how much token and cost usage is attributed to each model?
- which agents are using which models?
- what does usage look like by day?

## Why it exists

Some model-usage workflows depend on external tooling such as CodexBar.

This project is a local-first alternative that reads OpenClaw session logs directly, making it useful when direct session-log inspection is preferred or when external tooling is unavailable.

## One canonical repo, two interfaces

This repo is intended to serve both as:
- a **portable AgentSkill** via `SKILL.md`
- a **small Python CLI** via the packaged `openclaw-model-usage` command

That keeps the implementation, local usage, and published skill aligned in one canonical place.

## Features

- current / most recent model
- usage summary by provider/model
- token totals by model
- cost totals by model when available
- per-agent usage summary
- daily usage summary
- JSON output for scripting

## Data source

Primary source:

```bash
~/.openclaw/agents/*/sessions/*.jsonl
```

See `references/discovery.md` for the field inventory and reliability notes.

## Repo structure

- `SKILL.md` — instructions for agent use
- `scripts/model_usage.py` — bundled script used by the skill
- `src/openclaw_model_usage/cli.py` — packaged CLI entrypoint
- `references/discovery.md` — local data source notes
- `tests/smoke_test.py` — minimal fixture-based smoke test

## CLI usage

Run with uv:

```bash
uv run --project . openclaw-model-usage current
uv run --project . openclaw-model-usage summary
uv run --project . openclaw-model-usage agents
uv run --project . openclaw-model-usage daily --limit 20
uv run --project . openclaw-model-usage summary --json --pretty
```

## Script usage

Run the bundled script directly:

```bash
python scripts/model_usage.py current
python scripts/model_usage.py summary
python scripts/model_usage.py agents
python scripts/model_usage.py daily --limit 20
```

## Example output

```text
Rows: 3
Models:
- openai-codex / gpt-5.4: $0.0099, 2,500 tokens, 2 calls
- ollama / kimi-k2.5:cloud: $0.0000, 600 tokens, 1 calls
```

## Testing

Smoke test:

```bash
python tests/smoke_test.py
```

CI also checks:
- CLI help
- smoke test execution
- package build

## Design goals

- portable
- local-first
- small and pragmatic
- no CodexBar dependency
- one canonical repo for both skill and CLI
