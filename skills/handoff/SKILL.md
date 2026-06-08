---
name: handoff
description: Use when the user wants a compact copy-pasteable handoff for a new AI session so the next session can understand the current context before taking action.
---

# Handoff

## Purpose

Generate a copy-pasteable handoff prompt for a new AI session. The handoff should help the next session understand the current context, decisions, constraints, and suggested next steps without carrying the full chat history.

## Behavior

- Output only the handoff prompt unless the user asks for explanation.
- Use the user's language by default.
- Be compact but complete. Prefer precise bullets over narrative.
- Do not invent context. Mark unknowns as `Unknown` or `None known`.
- Separate confirmed facts from assumptions, open questions, and recommendations.
- Do not write files, run commands, or inspect the repository unless the user explicitly asks or essential facts are missing and local inspection can recover them.
- If the conversation includes sensitive values, secrets, tokens, or personal data, omit them and mention only that sensitive material was present and should be re-supplied securely if needed.

Before writing the prompt, silently identify:

1. The current objective.
2. User constraints, preferences, scope limits, and explicit instructions.
3. Decisions already made and the reasoning that still matters.
4. Work completed, work in progress, and current blockers.
5. Files, commands, tools, links, or artifacts mentioned.
6. Failed attempts or paths the next session should not repeat.
7. The best next action after the user confirms the receiving session may proceed.

Use this structure unless the user requests a different format:

```markdown
请接手下面这个已经进行过一段时间的任务。你的第一步只是理解上下文并复述，不要修改文件、运行命令、调用工具或执行任何推进动作，等待用户确认后再继续。

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
- 先理解上下文，并用简短文字复述你对任务的理解。
- 在用户确认前，不要修改文件、运行命令、调用工具或执行任何推进动作。
- 明确区分事实、假设和建议。
- 不要扩大范围，不要补做用户没要求的功能。
```

Quality checks before responding:

- The output can be pasted as the first message in a new chat.
- The next session can answer: "what is the goal, what is done, what remains, what should I inspect first after confirmation?"
- There is no unsupported claim such as "tests passed" unless the conversation contains that evidence.
- The handoff does not include obsolete ideas as current instructions.
- Recommended next steps are actionable, ordered, and gated behind user confirmation.
