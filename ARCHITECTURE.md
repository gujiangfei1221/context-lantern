# Context Lantern Architecture

## Overview

Context Lantern 是一个面向 AI coding / agent 工具的会话上下文提醒器。它在会话逐渐变重时提醒用户把关键上下文交接到新会话，避免 token 浪费和响应质量下降。

### 设计原则

- **Core 一次，Adapter 极薄**：核心策略只写一次，适配器只翻译边界。
- **只提醒，不自动生成 handoff**：不调用大模型、MCP、LSP 等昂贵工具。
- **分层诊断**：执行层、策略层、展示层的问题分开查，不混在一起。
- **新工具 = 新 Adapter + 新 Transport 配方**：不需要 fork Core。

## 四层架构

```
+-----------------------------------------------------------+
|  Host (Codex / Cursor / Windsurf / Copilot)               |
|  hooks.json、事件语义、宿主 UI                              |
+-----------------------------------------------------------+
        | stdin payload / transcript path
        v
+-----------------------------------------------------------+
|  Transport (OS x Host)                                    |
|  启动方式 (.cmd / python3)、stdin 处理、超时、工作目录      |
+-----------------------------------------------------------+
        | 标准化的输入
        v
+-----------------------------------------------------------+
|  Adapter (thin)                                           |
|  读 payload -> TokenSnapshot + dedup_key                  |
|  ReminderDecision -> 宿主 JSON                            |
+-----------------------------------------------------------+
        | MeasureResult / ReminderDecision
        v
+-----------------------------------------------------------+
|  Core (thick, single)                                     |
|  阈值判断 / 去重 / 文案 / 状态管理                          |
+-----------------------------------------------------------+
```

### 层间职责边界

判定标准：**同一个宿主在不同 OS 上会变的归 Transport；不变的归 Adapter。**

| 层 | 职责 | 禁止 |
|---|---|---|
| Host | 定义事件触发时机和输入格式 | 不包含任何 Lantern 逻辑 |
| Transport | 让进程在特定 OS 上跑完（启动命令、stdin 传递、超时） | 不做业务判断 |
| Adapter | payload 解析 -> 标准结构；标准决策 -> 宿主 JSON | 不做文件 I/O、不管阈值 |
| Core | 阈值、去重、文案、状态 | 不知道宿主是谁、OS 是什么 |

## Core 层：数据模型

Core 只认识三个核心概念，不知道 Codex 还是 Cursor。

### TokenSnapshot

一次 token 测量的标准化快照。所有宿主差异在 Adapter 层抹平后，交付给 Core 的就是这个结构。

```python
@dataclass(frozen=True)
class TokenSnapshot:
    input_tokens: int                          # 非缓存 input tokens
    cached_input_tokens: int = 0               # 缓存 input tokens
    total_tokens: int = 0
    model_context_window: int = 0
    source: str = "unknown"                    # 数据来源标记
```

`source` 是一等字段，取值如 `"transcript"`, `"payload"`, `"payload_cache"`, `"byte_estimate"`。调试时可以直接看到 token 数从哪来的。

### MeasureResult

Adapter 向 Core 交付的完整测量结果，不只是 token 数。

```python
@dataclass(frozen=True)
class MeasureResult:
    snapshot: TokenSnapshot
    dedup_key: str                             # 去重键（Adapter 算，Core 用）
    loop_prevention: bool = False              # 宿主防循环标志
    meta: dict = field(default_factory=dict)   # 调试用附加信息
```

`dedup_key` 由 Adapter 根据宿主特性生成：Codex 从 transcript 文件名提取 rollout id，Cursor 用 conversation_id 或 transcript stem。Core 只拿它做去重，不关心怎么算出来的。

`loop_prevention` 是宿主特有的"本轮不提醒"标志的标准化表达：Codex 的 `stop_hook_active`、Cursor 的 `loop_count > 0` 等，都在 Adapter 层归一化为这个布尔值。

### ReminderDecision

Core 的输出，决策结果。

```python
class Decision(Enum):
    SILENT = "silent"           # 不提醒
    WARN_ONCE = "warn_once"     # 提醒一次

@dataclass(frozen=True)
class ReminderDecision:
    decision: Decision
    snapshot: TokenSnapshot
    threshold: int
    message: str = ""          # 人类可读的提醒文案
    already_reminded: bool = False
```

Core 只管做出决策、生成文案。至于这个决策怎么变成 Codex 的 `{"decision":"block"}` 还是 Cursor 的 `{"followup_message":...}`，是 Encoder 的事。

## Core 层：流水线

无论哪个宿主，内部固定三步：

```
stdin + env
    |
    v
[1] measure  (Adapter 提供)
    |  MeasureResult
    v
[2] decide   (Core 统一逻辑)
    |  ReminderDecision
    v
[3] encode   (Adapter 提供)
    |  bytes on stdout
    v
宿主消费
```

### measure（Adapter 职责）

每个宿主有不同的 token 来源优先级。Adapter 按优先级尝试，返回第一个成功的结果：

| 优先级 | Codex | Cursor | Windsurf | Copilot |
|-------|-------|--------|----------|---------|
| 1 | transcript token_count | payload cache_* | 待确认 | 待确认 |
| 2 | — | payload input_tokens | 待确认 | 待确认 |
| 3 | — | transcript fallback | 待确认 | 待确认 |

`source` 字段记录实际使用了哪个来源。

### decide（Core 统一逻辑）

```
should_warn = (
    input_tokens >= threshold
    AND NOT already_reminded
    AND NOT loop_prevention
)
```

三行规则，对所有宿主通用。任何新增策略（如渐进式提醒）只在 Core 层加，Adapter 不动。

### encode（Adapter 职责）

每个宿主一个 Encoder，5~15 行，禁止在这里再算 token。stdout 只放宿主认的 JSON；人类可读日志一律 stderr。

## Adapter 注册

使用注册表模式，新宿主只需实现接口并注册：

```python
class Adapter(Protocol):
    @property
    def host_name(self) -> str: ...

    def measure(self, payload: dict, args: argparse.Namespace) -> MeasureResult | None: ...

    def encode(self, decision: ReminderDecision) -> str: ...
```

注册表：

```python
_ADAPTERS: dict[str, type[Adapter]] = {}

def register_adapter(adapter_cls: type[Adapter]) -> type[Adapter]:
    instance = adapter_cls()
    _ADAPTERS[instance.host_name] = adapter_cls
    return adapter_cls

def get_adapter(name: str) -> Adapter: ...
def list_adapters() -> list[str]: ...
```

新增宿主：实现 Adapter + Encoder，加 `@register_adapter` 装饰器。完事。

## 宿主能力表 (Capability Matrix)

| 能力 | Codex | Cursor | Windsurf | Copilot |
|-----|-------|--------|----------|---------|
| 事件类型 | Stop | stop | 待确认 | 待确认 |
| 主 token 来源 | transcript token_count | payload cache_* | 待确认 | 待确认 |
| 备 token 来源 | — | payload input_tokens | 待确认 | 待确认 |
| 防循环标志 | stop_hook_active | loop_count > 0 | 待确认 | 待确认 |
| 提醒输出 schema | decision + reason | followup_message | 待确认 | 待确认 |
| 去重键 | rollout id (文件名) | conversation_id | 待确认 | 待确认 |
| Windows 启动 | 直调 python | .cmd + stdin 落盘 | 待确认 | 待确认 |
| stdin payload | 有 | 有 | 待确认 | 待确认 |
| transcript 位置 | ~/.codex/sessions | ~/.cursor/... | 待确认 | 待确认 |

"待确认"的格子在实际接入时通过调研宿主文档和实测补齐。架构不需要等它们填完才能开始。

## Transport 层

Transport 解决"让脚本在特定 OS x 宿主组合上正常跑完"的问题，和业务逻辑无关。

### Windows .cmd 包装

Windows 上部分宿主（如 Cursor）通过 cmd.exe 执行 hook 命令，带来几个问题：嵌套引号、stdin 传递、Python 路径。统一用一个参数化的 .cmd 模板解决：

```batch
@echo off
setlocal
set "TMPFILE=%TEMP%\cl_payload_%RANDOM%.json"
more > "%TMPFILE%"
"C:\Path\To\python.exe" -m context_lantern run --adapter {adapter} --stdin-file "%TMPFILE%"
del "%TMPFILE%" 2>nul
endlocal
```

模板参数化，不为每个宿主重复写。

### Transport 配方

每个宿主 x OS 组合一份安装配方（YAML 或文档），包含：

- command 模板
- cwd 要求
- timeout 建议值
- stdin 处理方式
- 是否需要 .cmd 包装

## State 管理

### 存储位置

默认 `~/.codex/session_guard_state.json`（Codex 向后兼容），迁移后统一为 `~/.context-lantern/state.json`。

### 存储格式

```json
{
  "<dedup_key>": {
    "reminded": true,
    "input_tokens": 125000,
    "threshold": 120000,
    "source": "transcript",
    "line": 42,
    "at": "2026-06-01T12:00:00Z"
  }
}
```

### 去重规则

同一个 `dedup_key`，如果 `reminded == true` 且记录的 `input_tokens >= 当前 threshold`，则不再提醒。这保证了：用低阈值测试产生的旧记录不会阻止正式阈值的提醒。

分叉产生的新 transcript 有不同的 `dedup_key`，自然可以重新提醒。

## CLI 设计

```
context_lantern run     --adapter <name> [--threshold N] [--debug] [--no-state]
context_lantern doctor  [--adapter <name>]
context_lantern status  [--adapter <name>]
context_lantern install --adapter <name> [--dry-run]
```

### run

主命令。从 stdin 或 --stdin-file 读取 payload，通过指定 Adapter 执行 measure -> decide -> encode 流水线，输出到 stdout。

`--debug` 只跑 measure + decide，不 encode，输出 JSON 调试信息。这样 Transport 问题（Canceled、进程崩溃）和策略问题（阈值判断不对）可以分开查。

### doctor

分层诊断命令。按层逐步检查，每层独立报结果：

| 检查项 | 对应层 | 验证内容 |
|-------|--------|---------|
| Python 版本 >= 3.10 | Transport | 运行环境 |
| stdin 可读性 | Transport | payload 能否读入 |
| payload 解析 | Transport | JSON 格式是否正确 |
| Adapter 加载 | Adapter | 指定适配器是否存在 |
| measure 执行 | Adapter | 能否从 payload 提取 token |
| decide 执行 | Core | 阈值判断是否正确 |
| encode 输出 | Adapter | 输出是否为合法宿主 JSON |
| state 文件读写 | Core | 状态管理是否正常 |
| hooks.json 检查 | Transport | 配置中的 command 是否能执行 |

每步输出 PASS / FAIL / SKIP，让用户看到 Canceled 时跑一下 doctor 就能定位问题层。

### status

读取 state 文件和最新 token 信息，展示当前状态。开发者调试时常用。

### install

生成并执行安装步骤：复制 Adapter、生成 hooks.json、创建 .cmd 包装（Windows）。`--dry-run` 只打印不执行。

## 产品层退路

Hook 天然脆弱（Canceled、超时、schema 变更）。架构上预留不依赖 hook 的路径：

| 通道 | 触发方式 | 可靠性 | 说明 |
|------|---------|-------|------|
| Hook | 宿主自动触发 | 中 | 理想体验，但依赖宿主稳定性 |
| Skill / 规则 | 用户主动 $context-lantern | 高 | 不依赖 hook，用户意识驱动 |
| CLI status | 开发者手动运行 | 高 | 兜底，任何时候都能查 |

新宿主适配的最小可用顺序：CLI status 跑通 -> skill 能用 -> hook 上线。Transport 踩坑不阻塞核心价值。

## 测试策略

| 层级 | 测什么 | 依赖 | 自动化 |
|------|-------|------|-------|
| 单元 | measure / decide 用合成 JSON | 无宿主 | 是 |
| 集成 | echo payload \| adapter 完整 stdout | 无 IDE | 是 |
| 手册 E2E | 真实对话超阈值 | 每宿主 x 每 OS | 否（checklist） |

新宿主上线门槛：集成测试绿 + 一条 E2E checklist。

## 目录结构

```
context-lantern/
  context_lantern/
    __init__.py
    __main__.py          # python -m context_lantern 入口
    cli.py               # argparse + 子命令分发
    core/
      __init__.py
      models.py          # TokenSnapshot, MeasureResult, ReminderDecision, Decision
      state.py           # StateStore
      measure.py         # resolve_tokens 通用工具
      decide.py          # make_decision
      encode.py          # Encoder Protocol + format_k + build_message
    adapters/
      __init__.py        # Adapter Protocol + 注册表
      codex_stop.py      # Codex Stop hook adapter
      cursor_stop.py     # Cursor stop hook adapter
      windsurf_stop.py   # Windsurf adapter (骨架)
      copilot_stop.py    # Copilot adapter (骨架)
    transports/
      __init__.py
      windows_cmd.py     # .cmd 模板生成
      install.py         # 安装配方
    doctor/
      __init__.py
      checks.py          # 分层诊断检查项
  scripts/
    codex_stop_hook.py   # 保留旧版，内部改为调用 Core
  tests/
    test_models.py
    test_decide.py
    test_state.py
    test_codex_adapter.py
    test_cursor_adapter.py
  skills/
    context-lantern/SKILL.md
    session-handoff/SKILL.md
  ARCHITECTURE.md
  README.md
  pyproject.toml
```

## 迁移路径

从现有 `codex_stop_hook.py` 平滑过渡：

1. **Phase 1**：抽取 Core 模块（models + state + decide），旧的 `codex_stop_hook.py` 改为调用 Core 的薄壳。Codex 行为不变。
2. **Phase 2**：实现 Codex Adapter，用新 CLI 跑通 `context_lantern run --adapter codex`。旧脚本保留作为备份。
3. **Phase 3**：实现 Cursor Adapter + Windows Transport。
4. **Phase 4**：实现 doctor 命令。
5. **Phase 5**：实现 Windsurf / Copilot Adapter（补齐能力表中"待确认"项）。
6. **Phase 6**：清理旧脚本，更新 skill 和文档。

每个 Phase 结束后 Codex hook 仍可正常工作，不存在"拆了装不回去"的风险。
