---
name: memory-curator
description: Use only when the user explicitly asks to curate historical conversations, handoff files, thread summaries, exported chats, or prior debugging notes into durable project memory such as AGENTS.md guidance, _docs/agent-memory notes, decisions, runbooks, or issue retrospectives. Do not use for ordinary task handoff, temporary status, or one-off summaries.
---

# Memory Curator

## Purpose

Turn messy historical conversation context into useful long-lived project memory. The output should help future AI sessions understand repeated issues, important decisions, proven fixes, validation habits, and project-specific cautions without rereading full chat history.

This skill is for durable memory, not for handing off an unfinished task. Use `handoff` instead when the user wants a compact current-state file for the next session.

Use this skill manually and sparingly. It should usually trigger only when the user asks to "沉淀记忆", "整理历史会话", "更新 agent memory", "生成 runbook", "整理复盘", or similar durable-memory work.

Think of this as a lightweight memory-curation layer inspired by spec-driven workflows: extract durable artifacts from historical context, keep them small, make their scope explicit, and verify they are safe to reuse.

## Core Rule

Do not dump chat history into `AGENTS.md`. Curate it.

- `AGENTS.md`: long-lived rules, indexes, and high-frequency cautions future agents must notice.
- `_docs/agent-memory/`: categorized historical knowledge, issue retrospectives, decisions, runbooks, and source indexes.
- `_docs/handoff/`: current task state, next actions, blockers, and temporary context.

## Workflow

### 1. Identify Sources

Look for the smallest source set that can answer the user's request:

- Codex thread tools, if available, for recent project conversations.
- `_docs/handoff/` for compact task histories.
- User-provided exported chat files.
- Existing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or project docs.
- Relevant local notes under `_docs/`, `docs/`, or similar folders.

Prefer summaries and handoff files before reading huge raw logs. If using thread tools, avoid including tool outputs unless the user specifically needs them.

### Source Adapters

Use the adapter that matches the environment. If the relevant tool is unavailable, say so and ask for exported chat files or the tool-specific history location.

#### Codex

- Prefer Codex thread tools when available: list project threads first, then read only relevant thread summaries.
- Read `_docs/handoff/` before raw thread history when handoff files exist.
- Avoid `includeOutputs` unless command output is necessary; outputs often contain secrets, noise, or large logs.
- Record thread IDs and titles in `thread-index.md`, but do not copy raw chat turns into memory files.

#### Cursor

- Prefer exported Cursor chats, `.cursor/rules/`, legacy `.cursorrules`, and `AGENTS.md`.
- Do not scrape Cursor's local SQLite history by default.
- For detailed Cursor guidance, read `references/cursor.md` only when the task involves Cursor memory or rules.

#### Unknown or Other Tools

- Do not claim access to hidden conversation history.
- Ask the user for exported chats, transcript files, handoff files, or the tool's documented history location.
- Continue with local project memory files if no chat history is available.

### 2. Apply Promotion Criteria

Promote content to durable memory only when it passes at least one criterion:

- It has recurred or is likely to recur across future sessions.
- It affects future implementation, validation, data handling, security, or architecture choices.
- It records a decision, tradeoff, root cause, proven fix, or repeatable procedure.
- It prevents a costly repeated mistake.
- The user explicitly asks to preserve it as durable project memory.

Do not promote:

- One-off task status, next actions, or blockers; use `_docs/handoff/`.
- Raw chat excerpts, long transcripts, or full tool output.
- Speculative notes that cannot be tied to a source or explicit assumption.
- Secrets, credentials, cookies, tokens, or full authorization headers.

### 3. Classify Content

For each useful item, classify it into one of these buckets:

- **Long-term rule**: belongs in `AGENTS.md` after strong compression.
- **Historical issue**: problem, root cause, fix, verification, and "do not repeat" notes.
- **Decision/change**: important design choice, tradeoff, code path, or architecture note.
- **Runbook**: repeatable operational or verification procedure.
- **Data/domain guidance**: data cleaning rules, source-system requirements, schema notes, prompt/data conventions.
- **Thread/source index**: what was analyzed and where it came from.
- **Temporary status**: belongs in `_docs/handoff/`, not durable memory.
- **Sensitive or unsafe content**: omit concrete values and mention only that secrets existed if relevant.

### 4. Create or Update Files

Use this default structure unless the project already has a better convention:

```text
_docs/agent-memory/
  README.md
  thread-index.md
  historical-issues.md
  decisions-and-changes.md
  operations-runbook.md
```

Add domain-specific files only when they remove real clutter, for example:

```text
_docs/agent-memory/faq-governance.md
_docs/agent-memory/search-and-rerank.md
_docs/agent-memory/deployment-notes.md
```

Keep file names simple, lowercase, and stable. Do not create many tiny files unless the project already uses that style.

### 5. Write Useful Entries

Use small durable artifacts. Every substantial entry should be useful without the original chat and should make its lifecycle clear:

```markdown
Source: handoff/thread/export path or user-provided note
Date captured: YYYY-MM-DD
Applies to: project area, workflow, command, or file family
Confidence: high | medium | low
Last verified: command/date or Unknown
Expires or revisit when: condition, version change, or Unknown
```

Historical issue entries should usually include:

```markdown
## Short Problem Title

Problem: ...

Root cause: ...

Solution: ...

Key paths:

- `path/to/file`

Verification:

- ...

Do not repeat:

- ...
```

Decision entries should usually include:

```markdown
## Short Decision Title

Decision: ...

Why: ...

Tradeoff: ...

Applies when: ...

Does not apply when: ...
```

Runbook entries should be concrete but not secret-bearing:

- What situation triggers the runbook.
- Minimal safe sequence.
- Verification checks.
- Cleanup.
- Known traps.

### 6. Handle Conflicts and Staleness

When new memory conflicts with existing memory:

- Do not silently overwrite the old entry.
- Add a decision/change entry that states what changed, why, and which source is newer or more authoritative.
- Mark older guidance as superseded when safe, or add a "Revisit when" condition when uncertain.
- If the conflict affects security, auth, data correctness, deployment, or public APIs, ask the user before writing the final durable rule.

When memory looks stale:

- Prefer adding `Last verified` and `Expires or revisit when` over deleting it.
- Delete or rewrite only when the user asks or the source clearly proves it is obsolete.

### 7. Update AGENTS.md Sparingly

Only add or update `AGENTS.md` when the project has no durable-memory entry point, or the user explicitly wants future agents to discover the memory.

Good `AGENTS.md` additions:

- A short section pointing to `_docs/agent-memory/`.
- A list of the most important high-frequency rules.
- A rule saying temporary handoff state stays in `_docs/handoff/`.
- A rule saying secrets must not be copied from historical conversations.

Bad `AGENTS.md` additions:

- Full retrospectives.
- One-off URLs, session IDs, timestamps, or temporary status.
- Raw chat excerpts.
- Secrets, tokens, passwords, cookies, or API keys.

### 8. De-Sensitize

Before writing or finalizing, scan for common sensitive patterns:

- Passwords and login pairs.
- API keys and bearer tokens.
- Cookies and session IDs.
- Private server credentials.
- Full authorization headers.

Remove concrete values. It is acceptable to write: "historical conversations contained server credentials; ask the user to re-supply them securely if needed."

### 9. Verify

Before final response:

- Confirm new or modified files.
- Check `AGENTS.md` did not become a history dump.
- Search the memory files for obvious secrets.
- Make sure each entry is useful without the original chat.
- Make sure facts, assumptions, and recommendations are not mixed together.

Suggested checks when files were written:

```bash
rg -n "Bearer|Authorization|password|passwd|secret|token|cookie|sessionid|api[_-]?key" AGENTS.md _docs/agent-memory
rg -n "Problem:|Decision:|Source:|Last verified:|Do not repeat:" _docs/agent-memory
```

Treat matches as prompts for review, not automatic proof of a leak; redact concrete secrets before finalizing.

## Output Style

Tell the user:

- Which files were created or updated.
- Whether `AGENTS.md` was updated.
- What source types were analyzed.
- Whether sensitive values were omitted.
- Any known gaps, such as unavailable thread history or unreadable export files.

Keep the final response compact. Do not paste the full generated documents unless the user asks.
