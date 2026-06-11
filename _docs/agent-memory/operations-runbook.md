# Operations Runbook

## Creating A Handoff

Trigger: The user wants to save compact current-task context for a new session.

Sequence:

1. Use the `handoff` skill.
2. Write the file to `_docs/handoff/<topic>-YYYYMMDD-HHMMSS.md`.
3. Separate confirmed facts, assumptions, open questions, recommendations, and next actions.
4. Omit sensitive values and say only that sensitive material must be re-supplied securely if needed.
5. Tell the next session to read only the handoff first and wait for user confirmation before acting.

Verification:

- The file explains the objective, success criteria, relevant files, completed work, current state, blockers, and next action.
- The final response gives the absolute path and the read-first instruction.

Known traps:

- Do not turn a temporary handoff into a durable rule.
- Do not claim tests passed unless the conversation or command output proves it.

## Curating Project Memory

Trigger: The user wants historical conversations, notes, or task outcomes turned into durable project memory.

Sequence:

1. Prefer compact sources first: handoff files, thread summaries, exported summaries, and existing project docs.
2. Use raw chat or tool outputs only when necessary.
3. Classify each useful item as a long-term rule, historical issue, decision/change, runbook, data/domain guidance, source index, temporary status, or sensitive content.
4. Keep `AGENTS.md` short and put details in `_docs/agent-memory/`.
5. Record source IDs and titles in `thread-index.md`, not raw chat turns.
6. Scan written memory files for obvious secrets before finishing.

Verification:

- New entries are useful without the original chat.
- Facts, assumptions, and recommendations are not mixed together.
- No passwords, tokens, cookies, private server credentials, API keys, or authorization headers are present.

Known traps:

- Do not scrape fragile local chat databases unless the user explicitly asks and accepts the privacy and schema risks.
- Do not copy unrelated thread previews into memory just because they appeared in a thread list.

## Calibrating The Codex Stop Hook

Source: `_docs/handoff/token阈值调整-20260611-153545.md`; `_docs/handoff/token治理hook-20260611-152817.md`
Date captured: 2026-06-11
Applies to: `/Users/gujiangfei/.codex/hooks.json`, `/Users/gujiangfei/.codex/hooks/session_guard.py`
Confidence: medium
Last verified: validation commands listed in handoff files, 2026-06-11
Expires or revisit when: reminder noise increases, Codex transcript schema changes, or a larger token report is available

Trigger: The Codex context guard is too noisy, too late, or appears to miscount long sessions.

Sequence:

1. Prefer existing summarized reports and handoff files before reading raw session logs.
2. If historical validation is needed, sample specific session paths from a report instead of scanning all of `/Users/gujiangfei/.codex/sessions`.
3. Keep the Stop hook command in `/Users/gujiangfei/.codex/hooks.json` aligned with the intended thresholds.
4. Keep default constants in `/Users/gujiangfei/.codex/hooks/session_guard.py` aligned with the configured command unless there is a deliberate override.
5. Count long sessions by real user messages, not `token_count` events.
6. Make the hook output a clear next action: ask for `handoff` skill generation and then start a new session.

Verification:

- `python3 -m json.tool /Users/gujiangfei/.codex/hooks.json`
- `python3 -m py_compile /Users/gujiangfei/.codex/hooks/session_guard.py`
- Run `session_guard.py --no-state --debug` with the active thresholds.
- When using a historical transcript, verify that high-consumption sessions trigger `hard_input` and that `turn_count` reflects real user messages.

Known traps:

- Do not use `token_count` event count as a proxy for user turns.
- Do not recursively scan `.codex/sessions`; it can pull large and sensitive history into the current context.
- Do not ask the hook script to generate handoff content from raw transcripts.
