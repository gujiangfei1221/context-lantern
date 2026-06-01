# Context Lantern

Context Lantern 是一个面向 AI coding / agent 工具的会话上下文提醒工具。它在会话逐渐变重时点一盏灯，提醒用户把关键上下文交接到新会话，避免长会话持续膨胀带来的 token 浪费和响应质量下降。

当前首个适配器是 Codex Stop hook。它会读取 Codex 当前 transcript，解析最新 `token_count.info.last_token_usage.input_tokens`，当本轮 input tokens 达到阈值时，提醒用户显式运行 `session-handoff` skill 并开新会话继续。

## 设计原则

- 只提醒，不自动生成 handoff。
- 不调用大模型、MCP、LSP、RTK 或其他昂贵工具。
- 一个正式阈值，默认 `120000`。
- 同一个 transcript 只提醒一次，避免刷屏。
- 分叉后的新 transcript 可以重新提醒。
- 当前先把 Codex 跑稳，后续再增加其他工具适配器。

## 当前文件

- `scripts/codex_stop_hook.py`：Codex Stop hook 适配器脚本。
- `skills/context-lantern/SKILL.md`：Context Lantern 的 Codex skill，用于检查、安装和调试该工具。

## Codex 适配器

已验证的 Codex 方案：

- Hook 类型：Stop hook
- 生效脚本：`/Users/gujiangfei/.codex/hooks/session_guard.py`
- 生效配置：`/Users/gujiangfei/.codex/hooks.json`
- 状态文件：`/Users/gujiangfei/.codex/session_guard_state.json`
- transcript 目录：
  - `/Users/gujiangfei/.codex/sessions`
  - `/Users/gujiangfei/.codex/archived_sessions`
- 提醒输出：`{"decision":"block","reason":"..."}`

## 安装到 Codex hooks

如需从本项目版本安装 Codex hook：

```bash
mkdir -p /Users/gujiangfei/.codex/hooks
cp scripts/codex_stop_hook.py /Users/gujiangfei/.codex/hooks/session_guard.py
chmod +x /Users/gujiangfei/.codex/hooks/session_guard.py
```

然后确认 `/Users/gujiangfei/.codex/hooks.json` 包含：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 /Users/gujiangfei/.codex/hooks/session_guard.py --threshold 120000",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Codex 还需要启用 hooks feature flags：

```toml
[features]
hooks = true
codex_hooks = true
```

## 安装 Skill

本项目的 skill 可以软链接到全局 Codex skills：

```bash
ln -s /Users/gujiangfei/Code/funny/context-lantern/skills/context-lantern /Users/gujiangfei/.codex/skills/context-lantern
```

安装后可用下面的入口触发：

```text
[$context-lantern](/Users/gujiangfei/.codex/skills/context-lantern/SKILL.md)
```

## 验证

检查当前最新 transcript：

```bash
/usr/bin/python3 scripts/codex_stop_hook.py --threshold 120000 --debug
```

指定 transcript 测试：

```bash
/usr/bin/python3 scripts/codex_stop_hook.py \
  --threshold 120000 \
  --transcript-path /path/to/rollout-xxx.jsonl \
  --debug
```

忽略 state 验证提醒输出：

```bash
/usr/bin/python3 scripts/codex_stop_hook.py \
  --threshold 120000 \
  --transcript-path /path/to/rollout-xxx.jsonl \
  --no-state
```

预期行为：

- 低于 `120000`：静默。
- 第一次达到或超过 `120000`：输出 `decision: block` 的可见提醒。
- 同一个 transcript 已提醒过：静默。
- 分叉产生新 transcript：可重新提醒。
- `stop_hook_active=true`：静默，避免 hook continuation 循环。

## 提醒文案

超过阈值时，提醒会包含可直接复制发送的 handoff 入口：

```text
[$session-handoff](/Users/gujiangfei/.codex/skills/session-handoff/SKILL.md)
```
