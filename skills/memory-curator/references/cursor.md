# Cursor Memory Guidance

Use this reference only when the memory-curation task involves Cursor chats, Cursor rules, or Cursor-specific project behavior.

## Sources

Cursor project memory can come from three places:

- Exported chats: ask the user to export relevant Cursor chats as Markdown, then read those files as the primary conversation source.
- Project rules: inspect `.cursor/rules/` and legacy `.cursorrules` if present.
- Agent instructions: inspect `AGENTS.md` when present; Cursor can use it as a simple cross-tool rule file.

Cursor chat history may exist locally, but the database location and schema are implementation details. Do not rely on scraping Cursor's local SQLite history by default. Only inspect it if the user explicitly asks, provides the location, and accepts the fragility and privacy risk.

## Write-Back Guidance

- Put cross-tool, repo-wide durable memory in `AGENTS.md` plus `_docs/agent-memory/`.
- Put Cursor-only behavior in `.cursor/rules/`, preferably as a small rule pointing to `_docs/agent-memory/` instead of duplicating long content.
- Keep `.cursorrules` as legacy input if it exists, but prefer `.cursor/rules/` for new Cursor rules.
- If Background Agent chats are relevant, ask the user to open or export them separately; they are not the same as regular local chat history.

## Suggested Cursor Rule

```markdown
---
description: Project memory index
alwaysApply: true
---

Before working on historical issues, repeated debugging patterns, operations, or project-specific conventions, inspect `_docs/agent-memory/` and follow the durable rules in `AGENTS.md`.
Do not copy secrets from exported chats or local Cursor history into project memory.
```
