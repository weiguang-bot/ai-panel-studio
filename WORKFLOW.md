# AI Panel Studio — 工作流说明

## 一、开发流程概述

本项目采用 **SDD → DDD → TDD → E2E** 四阶段递进开发模式，每个阶段都有明确的输入、产出和验证标准。

### 阶段 1：SDD（System Design Document）

| 项目 | 内容 |
|------|------|
| **目标** | 完成系统数据建模与 API 契约设计 |
| **输入** | 一句话产品需求：「AI 圆桌讨论」Web 应用 |
| **产出** | `docs/ER.md`（ER 图）、`docs/schema.sql`（DDL）、`docs/api.yaml`（OpenAPI 3.0） |
| **Prompt 示例** | 「请帮我完成数据建模和 API 契约设计，不要生成任何业务逻辑代码」 |
| **验证** | 数据模型覆盖 5 个实体（Session、Expert、Transcript、Consensus、Divergence），API 覆盖 6 个端点 |

**关键决策**：
- 使用 SQLite（嵌入式数据库，零运维）而非 MySQL/PostgreSQL
- SSE 作为实时推送协议而非 WebSocket（原生浏览器支持，无需引入额外依赖）
- `transcript.new` 事件在发言时推送，支持断线重连

### 阶段 2：DDD（Domain-Driven Design）— 前端 UI 生成

| 项目 | 内容 |
|------|------|
| **目标** | 基于设计规范生成完整的 Vue 3 前端页面 |
| **输入** | 视觉规范（深色主题、霓虹蓝紫光效、Glassmorphism）+ 页面结构描述 |
| **产出** | `frontend/src/App.vue`（完整单文件组件，含 2260 行样式+模板+逻辑） |
| **验证** | `npm run build` 无错误，Vite 构建时间 < 1000ms |

**关键决策**：
- 使用 `<style scoped>` 内联样式，零外部 CSS 依赖
- Mock 数据阶段：使用 `EXPERT_POOL` 和 `MOCK_SPEECHES` 模拟全部交互
- 响应式布局：超宽屏 / 桌面 / 平板 / 手机四档适配

### 阶段 3：TDD（Test-Driven Development）

| 项目 | 内容 |
|------|------|
| **目标** | 为每个 API 端点编写测试用例，驱动业务逻辑实现 |
| **流程** | 红（编写失败测试）→ 绿（实现逻辑使通过）→ 重构（优化代码） |
| **产出** | 5 个测试文件、55 个测试用例、7 个 API 端点全部实现 |
| **验证** | `pytest tests/ -v` 55/55 通过 |

**测试文件清单**：

| 测试文件 | 测试端点 | 用例数 |
|----------|----------|--------|
| `tests/test_sessions.py` | POST /api/sessions | 13 |
| `tests/test_sessions_list.py` | GET /api/sessions | 15 |
| `tests/test_sse_events.py` | GET .../events (SSE) | 9 |
| `tests/test_transcripts.py` | GET .../transcript | 10 |
| `tests/test_conclusion.py` | POST .../conclusion | 8 |

### 阶段 4：E2E（End-to-End）

| 项目 | 内容 |
|------|------|
| **目标** | 前后端联调，替换 Mock 数据为真实 API 调用 |
| **关键变更** | 删除 300+ 行 Mock 数据，接入 `fetch` + `EventSource` |
| **新增文件** | `discussion_engine.py`（讨论引擎）、`deepseek_client.py`（DeepSeek API） |
| **验证** | 完整流程：创建会话 → 发言流推送 → 自动生成结论 |

---

## 二、AI 协同中遇到的典型问题及解决路径

### 问题 1：SSE 发言流截断导致 Conclusion API 返回 400

**现象**：前端 watch 检测到 `session.status = 'concluded'` 后调用结论 API，但后端返回 400 `INVALID_STATUS`。

**根因**：`discussion_engine.py` 的 `event_generator` 发送 `session.status: concluded` 作为 SSE 事件到前端，但数据库中的 `sessions.status` 字段从未被更新，始终为 `generating`。结论 API 校验数据库状态时失败。

**解决路径**：
1. 在 SSE 路由中 **同步** 更新数据库状态（`sessions.py:137-141`），在创建流式 Response 之前将状态改为 `discussing`
2. 在讨论引擎生成器内部，发言结束后调用 `Session.update_status()` 将状态改为 `concluded`
3. 简化 `_update_session_status` 函数，移除不必要的 `app_context()` 嵌套

### 问题 2：Env 文件泄露被 GitHub 拦截

**现象**：`.env` 文件包含 `DEEPSEEK_API_KEY`，推送时被 GitHub 的 secret scanner 拦截。

**根因**：初始提交时 `.env` 在 git 跟踪中，未加入 `.gitignore`。

**解决路径**：
1. 从 git 历史中移除 `.env`（`git rm --cached .env`）
2. 创建 `.env.example` 作为模板，填写占位符 `your_api_key_here`
3. 完善 `.gitignore`，明确排除 `.env` 文件
4. 轮换泄露的 API 密钥

### 问题 3：`random.choice()` 在字符串上的错误使用

**现象**：最后一条主持人结语只显示一个汉字（如"次"），发言被严重截断。

**根因**：`HOST_CLOSING` 被定义为字符串而非列表。`random.choice()` 在字符串上迭代字符，返回单个汉字。

```python
# ❌ 错误用法
HOST_CLOSING = '非常感谢各位专家...期待下次再会！'
random.choice(HOST_CLOSING)  # 返回 '次'

# ✅ 正确用法
HOST_CLOSING = [
    '非常感谢各位专家...期待下次再会！',
]
random.choice(HOST_CLOSING)  # 返回完整句子
```

**教训**：Python 的 `random.choice()` 接受任何序列类型（包括字符串）。使用前务必确认输入是预期类型。

---

## 三、对"工程化 AI 开发"的理解

### 3.1 结构化 Prompt 是关键

与传统"一次性 Prompt 生成全部代码"不同，本项目将需求拆解为 4 个独立阶段，每个阶段使用聚焦的 Prompt：

```
❌ 一次性 Prompt：
  "帮我写一个 AI 圆桌讨论的完整应用"

✅ 分阶段 Prompt：
  阶段 1："帮我做数据建模和 API 契约"
  阶段 2："生成前端 UI 组件"
  阶段 3-5："为 X 接口编写测试用例" → "实现 X 逻辑"
```

分阶段的好处：
- 每个 Prompt 的上下文更聚焦，输出质量更高
- 中间产物（ER 图、API 契约）可作为下一阶段的精确输入
- 某阶段出错时只需重新生成该阶段，不影响已完成部分

### 3.2 测试驱动防止 AI 退化

AI 生成的代码存在"越改越差"的风险——一次修复可能引入新问题。TDD 模式提供了安全网：

```
编写测试 → 验证失败（红） → 实现逻辑 → 验证通过（绿） → 重构
```

55 个测试用例覆盖了参数校验、边界条件、幂等性、数据库交互等场景。每次 AI 修改代码后运行测试，可立即发现回归问题。

### 3.3 阶段性拆解避免"黑盒陷阱"

"一键生成"看起来高效，但会产生不可维护的「黑盒代码」。本项目通过以下方式确保可控性：

| 策略 | 应用 |
|------|------|
| **增量构建** | 每次只生成 1 个文件或 1 个函数，构建并测试 |
| **渐进复杂度** | 先 Mock 再真实 API，先预设模板再接入 LLM |
| **测试先行** | 测试定义了"什么是对的"，实现只是让测试变绿 |
| **审查中间产物** | 每个阶段的输出（ER 图、API 契约、测试用例）都经过人工确认 |

### 3.4 经验总结

1. **不要信任 AI 的一次性输出** — 每次生成后必须验证构建和测试
2. **AI 擅长局部优化，不擅长全局架构** — 架构决策（数据库选型、通信协议）由人主导
3. **Prompt 中明确"不要做什么"** — 例如「请只生成测试代码，不要生成实现代码」有效防止 AI 越界
4. **环境信息要随 Prompt 附上** — 告知 AI 当前项目结构、文件内容、已有代码，避免重复生成
