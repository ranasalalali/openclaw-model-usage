# Changelog

All notable changes to `openclaw-model-usage` will be documented in this file.

## 1.1.0

- add Phase 1 session-aware attribution by joining usage rows with OpenClaw session metadata
- add `sessions`, `subagents`, and `session-tree` views
- enrich row output with session/subagent metadata such as session key, label, parent linkage, channel, and spawn depth
- improve fallback attribution from session-log subagent context when index metadata is incomplete
- update docs and smoke coverage for session/subagent analysis

