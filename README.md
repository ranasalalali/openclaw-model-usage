# openclaw-model-usage

[![CI](https://github.com/ranasalalali/openclaw-model-usage/actions/workflows/ci.yml/badge.svg)](https://github.com/ranasalalali/openclaw-model-usage/actions/workflows/ci.yml)

A portable AgentSkill and Python CLI for inspecting local OpenClaw model usage directly from session logs.

## Overview

`openclaw-model-usage` summarizes local model usage from OpenClaw session JSONL files and, in Phase 1, joins those usage rows with pragmatic session metadata from local OpenClaw session indexes.

It can answer questions such as:
- what model is currently being used?
- what models have been used recently?
- how much token and cost usage is attributed to each model?
- which agents are using which models?
- what does usage look like by day?
- which sessions and subagents consumed the usage?
- how does usage roll up from parent sessions to subagents?

## Quick start

```bash
uv run --project . openclaw-model-usage current
uv run --project . openclaw-model-usage summary
uv run --project . openclaw-model-usage sessions
uv run --project . openclaw-model-usage session-tree
uv run --project . openclaw-model-usage summary --json --pretty
```

## Why this exists

Some model-usage workflows depend on external tooling such as CodexBar.

This project is a local-first alternative that reads OpenClaw session logs directly, making it useful when direct session-log inspection is preferred or when external tooling is unavailable.

## One canonical repo, two interfaces

This repo serves both as:
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
- session-aware usage attribution
- subagent usage attribution using `sessions.json`, with fallback inference from subagent prompts in session logs when index metadata is missing
- parent/child session tree rollups when parent linkage metadata is available
- JSON output for scripting

## Data sources

Primary usage source:

```bash
~/.openclaw/agents/*/sessions/*.jsonl
```

Session metadata source:

```bash
~/.openclaw/agents/*/sessions/sessions.json
```

The tool joins assistant usage rows from JSONL files with available session metadata from `sessions.json` plus the JSONL session header line.

See `references/discovery.md` for the field inventory and reliability notes.

## Usage

### CLI

Run with uv:

```bash
uv run --project . openclaw-model-usage current
uv run --project . openclaw-model-usage summary
uv run --project . openclaw-model-usage agents
uv run --project . openclaw-model-usage sessions
uv run --project . openclaw-model-usage subagents
uv run --project . openclaw-model-usage session-tree
uv run --project . openclaw-model-usage daily --limit 20
uv run --project . openclaw-model-usage summary --json --pretty
```

### Bundled script

Run the bundled script directly:

```bash
python3 scripts/model_usage.py current
python3 scripts/model_usage.py summary
python3 scripts/model_usage.py sessions
python3 scripts/model_usage.py subagents
python3 scripts/model_usage.py session-tree
```

## Useful filters

```bash
uv run --project . openclaw-model-usage sessions --agent tars-code --since-days 7
uv run --project . openclaw-model-usage subagents --channel discord --json --pretty
uv run --project . openclaw-model-usage rows --session-id 8ce56106-1712-45c7-a2b4-93fcafe86315 --json --pretty
```

## Repo structure

- `SKILL.md` — instructions for agent use
- `scripts/model_usage.py` — bundled script used by the skill
- `src/openclaw_model_usage/cli.py` — packaged CLI implementation
- `references/discovery.md` — local data source notes
- `tests/smoke_test.py` — fixture-based smoke test covering session attribution

## Example output

```text
Usage records: 3
Sessions:
- sample-agent | parent-session: $0.0099, 2,500 tokens, 2 calls
- sample-agent | child-session | sample-subagent-task | parent parent-session | depth 1: $0.0000, 600 tokens, 1 calls
```

## Testing

Smoke test:

```bash
python3 tests/smoke_test.py
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
- reliable session/subagent attribution from observed local metadata
- one canonical repo for both skill and CLI

## Current limitations

- attribution is only as good as local metadata written by OpenClaw
- parent-child rollups rely on `sessions.json` `spawnedBy` linkage; missing index data means no tree link
- repo/project attribution is intentionally out of scope for Phase 1 unless the logs say it explicitly
- only assistant message usage rows are counted, matching the existing tool design
