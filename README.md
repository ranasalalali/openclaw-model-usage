# openclaw-model-usage

A portable AgentSkill for inspecting local OpenClaw model usage directly from session logs.

## What it does

This skill helps an agent answer questions like:
- what model is currently being used?
- what models have been used recently?
- how much token/cost usage is attributed to each model?
- which agents are using which models?
- what does usage look like by day?

## Why it exists

Some model-usage workflows depend on external tooling such as CodexBar.

This skill is a local-first alternative that reads OpenClaw session JSONL logs directly and can work without that dependency.

## Structure

- `SKILL.md` — instructions for when/how an agent should use the skill
- `scripts/model_usage.py` — deterministic Python CLI for parsing local usage data
- `references/discovery.md` — notes on available local data sources and reliable fields

## Primary data source

```bash
~/.openclaw/agents/*/sessions/*.jsonl
```

## Example commands

```bash
python scripts/model_usage.py current
python scripts/model_usage.py summary
python scripts/model_usage.py agents
python scripts/model_usage.py daily --limit 20
python scripts/model_usage.py summary --json --pretty
```

## Design goals

- portable
- local-first
- small and pragmatic
- no CodexBar dependency
- suitable for publication as an AgentSkill
