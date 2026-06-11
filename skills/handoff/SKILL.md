---
name: handoff
description: Use when the user wants to save a compact handoff file for a new AI session so the next session can understand the current context before taking action.
---

# Handoff

## Purpose

Generate a handoff file for a new AI session. The handoff should help the next session understand the current context, decisions, constraints, and suggested next steps without carrying the full chat history.

## Behavior

- Write the handoff content to `cwd/_docs/handoff/<topic>-YYYYMMDD-HHMMSS.md`.
- Use a short topic in the filename that summarizes the handoff content in about 10 Chinese characters, or 3-6 English words.
- Keep the filename topic readable but filesystem-safe: remove spaces and punctuation; use `handoff` if no clear topic exists.
- After writing the file, output only the absolute file path and one short instruction for the next session to read that file first.
- Use the user's language by default.
- Be compact but complete. Prefer precise bullets over narrative.
- Do not invent context. Mark unknowns as `Unknown` or `None known`.
- Separate confirmed facts from assumptions, open questions, and recommendations.
- Do not inspect the repository unless the user explicitly asks or essential facts are missing and local inspection can recover them.
- If the conversation includes sensitive values, secrets, tokens, or personal data, omit them and mention only that sensitive material was present and should be re-supplied securely if needed.

Before writing the prompt, silently identify:

1. The current objective.
2. User constraints, preferences, scope limits, and explicit instructions.
3. Decisions already made and the reasoning that still matters.
4. Work completed, work in progress, and current blockers.
5. Verification commands already run, their results, and checks that were not run.
6. Files, commands, tools, links, or artifacts mentioned.
7. Failed attempts or paths the next session should not repeat.
8. The best next action after the user confirms the receiving session may proceed.

Use this file content structure unless the user requests a different format:

```markdown
请接手下面这个已经进行过一段时间的任务。你的第一步只是理解上下文并复述。允许只读读取本交接文件；除此之外，在用户确认前不要修改文件、运行命令、调用工具或执行任何推进动作。

## 当前目标
- ...

## 成功标准
- ...

## 用户明确要求 / 偏好
- ...

## 已确认上下文
- ...

## 已完成工作
- ...

## 当前状态
- ...

## 验证命令 / 结果
- 已运行：...
- 结果：...
- 未运行 / 待验证：...

## 相关文件 / 目录 / 工具
- ...

## 已做决策
- ...

## 不要重复的尝试
- ...

## 未决问题
- ...

## 建议下一步
1. ...
2. ...
3. ...

## 给新会话的要求
- 允许只读读取本交接文件，并用简短文字复述你对任务的理解。
- 除读取本交接文件外，在用户确认前不要修改文件、运行命令、调用工具或执行任何推进动作。
- 明确区分事实、假设和建议。
- 不要扩大范围，不要补做用户没要求的功能。
```

Quality checks before responding:

- The saved file can be read by a new session as its first context source.
- The response is concise and includes the absolute file path.
- The next session can answer: "what is the goal, what is done, what remains, what should I inspect first after confirmation?"
- There is no unsupported claim such as "tests passed" unless the conversation contains that evidence.
- Verification is explicit: commands that were run, commands that were not run, and unknown results are clearly separated.
- The handoff does not include obsolete ideas as current instructions.
- Recommended next steps are actionable, ordered, and gated behind user confirmation.

Final response format:

```text
已生成交接文件：<absolute-path>

请只读读取这个文件并复述上下文；除此之外，在用户确认前不要修改文件、运行命令、调用工具或执行任何推进动作。
```
