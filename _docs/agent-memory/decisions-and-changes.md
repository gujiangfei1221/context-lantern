# Decisions And Changes

## Split Reasoning From Execution

Decision: Use high-reasoning AI sessions for understanding, clarification, task decomposition, architecture decisions, and review. Use execution-focused AI sessions for narrow code changes, command running, and mechanical implementation.

Why: Long conversations become expensive and hard to steer when one session carries every detail. A written task handoff, spec, and `git diff` are more stable shared context than full chat history.

Tradeoff: This adds a small amount of documentation overhead, but reduces context bloat and makes review boundaries clearer.

Applies when: The work involves feature changes, multi-file edits, formal behavior changes, or work that may cross between Codex, Cursor, DeepSeek, or similar tools.

Does not apply when: The task is a tiny one-off command, a simple answer, or a local change where one session can safely finish and verify the work.

## Keep AGENTS.md As An Entry Point

Decision: Keep `AGENTS.md` focused on durable rules and pointers. Store detailed retrospectives, procedures, and historical notes under `_docs/agent-memory/`.

Why: Future agents need a small set of high-signal rules first, not a large pasted conversation history.

Tradeoff: Agents must inspect `_docs/agent-memory/` for richer context when the task touches history, handoffs, repeated issues, or project workflow.

Applies when: Adding project memory, recurring cautions, runbooks, or source indexes.

Does not apply when: Capturing temporary task status. Temporary state belongs in `_docs/handoff/`.

## Use Handoff Files For Temporary State

Decision: Use `_docs/handoff/<topic>-YYYYMMDD-HHMMSS.md` for current task state and next-session context.

Why: Handoffs let a new session understand the goal, constraints, completed work, blockers, and suggested next steps without inheriting the entire chat.

Tradeoff: Handoffs can become stale, so they should not be treated as durable project facts after the task ends.

Applies when: The user wants to continue an unfinished task in a new AI session.

Does not apply when: The content is a long-lived rule or retrospective. Curate that into `_docs/agent-memory/`.

## Codex Stop Hook Should Prompt Handoff, Not Generate It

Source: `_docs/handoff/token治理hook-20260611-152817.md`; Codex thread `019eb585-635f-7df1-8b49-ed90bbad889e`
Date captured: 2026-06-11
Applies to: Codex Stop hook design, `handoff` skill, `memory-curator` skill
Confidence: high
Last verified: handoff records Stop hook returned a blocking reminder JSON and a later real Stop hook prompt appeared, 2026-06-11
Expires or revisit when: Codex hook APIs expose safe model-mediated handoff generation or transcript summarization behavior changes

Decision: The Stop hook should act as a strong reminder with a clear next-message instruction. It should not automatically generate a handoff file.

Why: The hook script can inspect transcript signals, but it does not have the model's compressed working understanding. Having the hook read and summarize raw transcripts directly risks privacy leakage, noisy summaries, and large context/tool-output amplification.

Tradeoff: The user must explicitly ask for the `handoff` skill when the hook fires, but the handoff is higher quality and safer.

Applies when: A Codex session crosses configured context, long-session, or tool-output thresholds.

Does not apply when: The user explicitly asks for an automation that can safely create a file from known structured state.

## Calibrated Codex Context Guard Thresholds

Source: `_docs/handoff/token阈值调整-20260611-153545.md`
Date captured: 2026-06-11
Applies to: `/Users/gujiangfei/.codex/hooks/session_guard.py`, `/Users/gujiangfei/.codex/hooks.json`
Confidence: medium
Last verified: JSON parse, Python compile, current-session debug, and one historical high-consumption session debug were recorded as passing in the handoff, 2026-06-11
Expires or revisit when: a larger session distribution is analyzed, Codex token accounting changes, or reminders become noisy again

Decision: Use `50k` soft input, `120k` hard input, `8k` soft tool output, `25k` hard tool output, and `8` real user turns for the Codex Stop hook thresholds.

Why: Earlier `15k / 30k` input thresholds were too noisy after reviewing token reports. Top high-consumption sessions had latest input p25 around `112k`, p50 around `149k`, and p75 around `205k`; `50k` warns earlier without flagging every medium session, while `120k` marks real replay-risk territory.

Tradeoff: A session around `70k` input may still trigger a soft reminder. That is intentional because it is above the warning line, but below the hard stop.

Applies when: Maintaining or recalibrating the global Codex Stop hook.

Does not apply when: A project wants stricter local thresholds for very short or security-sensitive work.

## Count Real User Turns For Long-Session Detection

Source: `_docs/handoff/token阈值调整-20260611-153545.md`
Date captured: 2026-06-11
Applies to: `/Users/gujiangfei/.codex/hooks/session_guard.py`
Confidence: high
Last verified: historical session debug showed `turn_count=63` using the corrected `user_message` signal, 2026-06-11
Expires or revisit when: Codex transcript schema changes

Decision: Long-session detection should count transcript records where `payload.type == "user_message"`, not `token_count` events.

Why: `token_count` events are accounting records, not user turns. Using them overstates or distorts conversation length.

Tradeoff: This depends on the current transcript schema.

Applies when: Updating session guard logic or interpreting its `turn_count` debug output.

Does not apply when: The transcript source lacks `payload.type` records; then the counting method must be revalidated.
