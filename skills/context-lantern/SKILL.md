---
name: context-lantern
description: Use when installing, checking, debugging, or adjusting Context Lantern, a session context reminder tool whose Codex adapter warns once when the latest input tokens exceed the handoff threshold.
---

# Context Lantern

## Purpose

Context Lantern helps keep long AI coding sessions from silently becoming too heavy. Its current adapter is a Codex Stop hook that reads the active Codex transcript, checks the latest `last_token_usage.input_tokens`, and reminds the user to run `session-handoff` when the configured threshold is reached.

Use this skill when the user asks about:

- Context Lantern.
- Codex token handoff reminders.
- Installing or checking the Codex Stop hook.
- The `codex_stop_hook.py` or installed `session_guard.py` script.
- Avoiding repeated reminders for the same transcript.
- Preparing this project for more AI tool adapters.

## Constraints

- Keep the hook reminder-only. Do not auto-run `session-handoff`.
- Do not call a model, MCP server, LSP, RTK, or any expensive tool from the hook.
- Keep one formal threshold unless the user explicitly asks for another mode.
- Use `120000` as the default formal threshold.
- Do not include `[Session Guard]` in the user-visible reminder.
- Treat forked transcripts as separate reminder targets.
- Do not rely on hook payload `session_id` for deduplication when a transcript filename is available.
- Do not claim non-Codex adapters exist until they are implemented and verified.

## Files

- Project script: `scripts/codex_stop_hook.py`
- Project skill: `skills/context-lantern/SKILL.md`
- Installed hook script: `/Users/gujiangfei/.codex/hooks/session_guard.py`
- Hook config: `/Users/gujiangfei/.codex/hooks.json`
- State file: `/Users/gujiangfei/.codex/session_guard_state.json`
- Transcript roots:
  - `/Users/gujiangfei/.codex/sessions`
  - `/Users/gujiangfei/.codex/archived_sessions`
- Handoff skill: `/Users/gujiangfei/.codex/skills/session-handoff/SKILL.md`

## Workflow

1. Inspect before editing:

   ```bash
   sed -n '1,220p' scripts/codex_stop_hook.py
   python3 -m json.tool /Users/gujiangfei/.codex/hooks.json
   ```

2. Verify current behavior:

   ```bash
   /usr/bin/python3 scripts/codex_stop_hook.py --threshold 120000 --debug
   ```

3. If installing the Codex adapter from this project, copy the script without changing global config unless the user asked:

   ```bash
   mkdir -p /Users/gujiangfei/.codex/hooks
   cp scripts/codex_stop_hook.py /Users/gujiangfei/.codex/hooks/session_guard.py
   chmod +x /Users/gujiangfei/.codex/hooks/session_guard.py
   ```

4. Confirm hook config uses:

   ```bash
   /usr/bin/python3 /Users/gujiangfei/.codex/hooks/session_guard.py --threshold 120000
   ```

5. Test a known transcript with `--debug` before relying on Desktop behavior.

## Expected Behavior

- Below threshold: no hook output.
- First threshold crossing per transcript: output `{"decision":"block","reason":"..."}`.
- Already reminded transcript: no hook output.
- Forked transcript with a new rollout id: can remind again.
- `stop_hook_active=true`: no hook output.

## Global Skill Install

Install this skill by symlinking the project skill directory:

```bash
ln -s /Users/gujiangfei/Code/funny/context-lantern/skills/context-lantern /Users/gujiangfei/.codex/skills/context-lantern
```

After installation, trigger it with:

```text
[$context-lantern](/Users/gujiangfei/.codex/skills/context-lantern/SKILL.md)
```

## Debugging Notes

If Codex Desktop reminds below `120000`, first check whether Desktop is using stale hook configuration. Ask the user to refresh `/hooks`, toggle the hook off and on, or restart Codex.

Old state entries created with a lower test threshold should not block formal reminders if the script checks that the saved `input_tokens` is at least the active threshold.
