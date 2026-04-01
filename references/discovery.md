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

Observed reliable fields in the JSONL session header line:
- session event `type=session`
- session `id`
- session `timestamp`
- session `cwd`

## Session metadata index

```bash
~/.openclaw/agents/*/sessions/sessions.json
```

Useful for:
- session discovery
- mapping session keys to session IDs/files
- updated timestamps
- channel and display metadata
- subagent metadata such as `spawnDepth`, `subagentRole`, and `label`
- parent linkage via `spawnedBy`

## Attribution rules used in Phase 1

1. Build usage rows from assistant message events in `*.jsonl`.
2. Join each row to same-agent session metadata from `sessions.json` using `sessionId`.
3. Use the JSONL session header to fill obvious gaps such as start timestamp and cwd.
4. Derive parent session IDs from `sessions.json` `spawnedBy` session keys when available.
5. Do not infer repo/project attribution unless the logs state it directly.

## Practical guidance

Build summaries from session JSONL files first.

Then layer in `sessions.json` for:
- session summaries
- subagent summaries
- parent/child session trees
- channel-aware filtering

This supports:
- current model
- usage by provider/model
- token totals
- cost totals when available
- agent breakdowns
- daily breakdowns
- session and subagent attribution
