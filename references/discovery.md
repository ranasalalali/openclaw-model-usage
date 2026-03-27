# OpenClaw model usage discovery

This skill summarizes model usage directly from local OpenClaw session logs.

## Primary source

```bash
~/.openclaw/agents/*/sessions/*.jsonl
```

These JSONL files are the primary source of truth for local usage summaries.

Observed reliable fields in assistant message events:
- event `type`
- event `timestamp`
- `message.role`
- `message.provider`
- `message.model`
- `message.usage.input`
- `message.usage.output`
- `message.usage.cacheRead`
- `message.usage.cacheWrite`
- `message.usage.totalTokens`
- `message.usage.cost.input`
- `message.usage.cost.output`
- `message.usage.cost.cacheRead`
- `message.usage.cost.cacheWrite`
- `message.usage.cost.total`

## Useful related files

### Session metadata index

```bash
~/.openclaw/agents/*/sessions/sessions.json
```

Useful for:
- session discovery
- mapping session IDs to files
- updated timestamps

### Agent model config

```bash
~/.openclaw/agents/*/agent/models.json
```

Useful for:
- configured providers/models
- static cost metadata where present
- model context windows

## Practical guidance

Build summaries from session JSONL files first.

That supports:
- current model
- usage by provider/model
- token totals
- cost totals when available
- agent breakdowns
- daily breakdowns
