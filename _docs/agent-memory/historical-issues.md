# Historical Issues

## Codex Token Blowup From Replay And Tool Output

Source: Codex thread `019eb585-635f-7df1-8b49-ed90bbad889e`; `_docs/handoff/token治理hook-20260611-152817.md`; `_docs/handoff/token阈值调整-20260611-153545.md`
Date captured: 2026-06-11
Applies to: long Codex sessions, large tool outputs, skill/tool prompt footprint, session handoff workflow
Confidence: medium
Last verified: threshold validation commands recorded in handoff files, 2026-06-11
Expires or revisit when: Codex context accounting, local skill loading, or hook behavior changes

Problem: Long Codex sessions repeatedly replay growing input history. Large command output, broad file reads, and unused skill/tool schema can make later turns expensive even when the user only asks for a small action.

Root cause: The main pressure is replayed input history, not just the newest user message. Broad commands and raw logs become future input. Long sessions also blur task boundaries, so temporary state competes with durable memory.

Solution: Use handoff as the session lifecycle break, keep memory curation separate, restrict reads to precise files or line ranges, use RTK-style compressed command output where appropriate, and calibrate the Stop hook to warn before replay risk becomes extreme.

Key paths:

- `AGENTS.md`
- `_docs/handoff/`
- `_docs/agent-memory/`
- `skills/handoff/SKILL.md`
- `skills/memory-curator/SKILL.md`
- `/Users/gujiangfei/.codex/hooks.json`
- `/Users/gujiangfei/.codex/hooks/session_guard.py`
- `/Users/gujiangfei/.codex/RTK.md`

Verification:

- Handoff records `hooks.json` parsed successfully.
- Handoff records `session_guard.py` compiled successfully.
- Handoff records hook debug output triggered expected reminders.
- Current memory curation ran a secret-pattern scan before completion.

Do not repeat:

- Do not scan all of `/Users/gujiangfei/.codex/sessions` to answer a narrow question.
- Do not copy raw chat history or command logs into `AGENTS.md` or `_docs/agent-memory/`.
- Do not treat `memory-curator` as an ordinary handoff or every-turn summary tool.
- Do not claim verification passed unless the command and result are recorded.
