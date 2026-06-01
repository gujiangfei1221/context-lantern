---
name: session-handoff
description: Use when a long AI coding or planning conversation needs to move into a fresh chat, continue after context compaction, resume work in another AI tool, or produce copy-pasteable handoff context for a new session.
---

# Session Handoff

## Purpose

Generate a copy-pasteable starter prompt for a new AI session. The goal is continuity, not a transcript summary: preserve what the next agent needs to continue accurately, and discard chatter, repeated exploration, stale branches, and irrelevant details.

## Default Behavior

- Output only the handoff prompt unless the user asks for explanation.
- Do not write files, run commands, or inspect the repository unless the user explicitly asks or the current conversation lacks essential facts that local inspection can reasonably recover.
- Use the user's language by default.
- Be compact but complete. Prefer precise bullets over narrative.
- Do not invent context. Mark unknowns as `Unknown` or `None known`.
- Separate confirmed facts from assumptions, open questions, and recommendations.
- If the current conversation includes sensitive values, secrets, tokens, or personal data, omit them and mention only that sensitive material was present and should be re-supplied securely if needed.

## Handoff Construction

Before writing the prompt, silently identify:

1. The current objective and why the user wants a new session.
2. User constraints, preferences, scope limits, and explicit instructions.
3. Decisions already made and the reasoning that still matters.
4. Work completed, work in progress, and current blockers.
5. Files, commands, tools, links, or artifacts mentioned.
6. Failed attempts or paths the next session should not repeat.
7. The best next action for the receiving session.

Only include information supported by the conversation or by explicitly inspected local state.

## Output Template

Use this structure unless the user requests a different format:

```markdown
请接手下面这个已经进行过一段时间的任务。你的目标不是复述历史，而是基于交接信息继续推进。

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

## 给新会话的执行要求
- 先用简短文字复述你对任务的理解。
- 如涉及代码或文件，先检查相关文件，再修改。
- 明确区分事实、假设和建议。
- 不要扩大范围，不要补做用户没要求的功能。
- 完成后说明验证方式和结果。
```

## Quality Checks

Before responding, verify:

- The output can be pasted as the first message in a new chat.
- The next agent can answer: "what is the goal, what is done, what remains, what should I inspect first?"
- There is no unsupported claim such as "tests passed" unless the conversation contains that evidence.
- The handoff does not include obsolete ideas as current instructions.
- The recommended next steps are actionable and ordered.

## Optional Variants

If the user asks for a shorter version, produce:

```markdown
## 新会话交接摘要
- 目标：
- 关键约束：
- 已完成：
- 当前状态：
- 下一步：
- 注意事项：
```

If the user asks for an English handoff, translate the template and keep the same sections.
