# Prompt 记录文档

## [SDD阶段] Prompt 1：数据建模与API契约设计

**完整Prompt内容：**
[SDD阶段] 我现在要做一个"AI圆桌讨论"Web应用。请先帮我完成数据建模和API契约设计，不要生成任何业务逻辑代码。

需求：用户输入讨论话题和专家人数（默认4人），系统生成主持人和专家列表，进入讨论模式后实时推送发言。

核心实体：
- 讨论会话（Session）：id, topic, expert_count, status, created_at
- 专家（Expert）：id, session_id, name, title, stance, color, avatar_emoji
- 发言（Transcript）：id, session_id, speaker_id, speaker_type (host/expert), content, sequence, timestamp
- 共识（Consensus）：id, session_id, summary, created_at
- 分歧（Divergence）：id, session_id, description, involved_experts, created_at

请输出：
1. SQLite 的 ER 图（用 Markdown 表格和关系描述）
2. 完整的 CREATE TABLE 建表语句
3. 一份 OpenAPI 3.0 的 YAML 契约，定义5个接口...

**意图：**
让 Claude 先完成数据建模和API契约，为后续开发提供清晰蓝图。

**遇到的挑战：**
Claude 输出被 token 限制截断，需要分两次输出；成功产出完整 ER图、SQL 和 OpenAPI。

**如何引导AI修正：**
在第一次输出被截断后，要求继续输出剩余部分，最终获得完整契约。

**产出文件：**
- docs/ER.md
- docs/schema.sql
- docs/api.yaml

---

## [DDD阶段] Prompt 2：前端UI组件生成

**完整Prompt内容：**
[DDD阶段] 我现在要为"AI圆桌讨论"Web应用生成前端UI组件。请基于以下技术栈和设计规范，生成完整的页面代码。

技术栈：Vue 3 + Vite（单页面组件，使用 Composition API）

页面结构与交互要求：
1. 首页/创建区：话题输入框（textarea）、专家人数选择器（滑块，默认4，范围2-10）、"开始讨论"按钮
2. 演播厅模式：顶部标题栏、中间发言滚动区（独立滚动）、左侧/右侧嘉宾席
3. 视觉风格：深色背景（深灰/墨蓝渐变）、发光边框、Glassmorphism、响应式布局
4. 状态模拟：页面加载后自动生成模拟数据（4位专家+1位主持人），点击"开始讨论"后每隔2-3秒生成一条模拟发言

所有样式内联在组件中（scoped），可独立运行。

**意图：**
生成一个包含完整视觉风格和交互逻辑的前端页面，先使用 Mock 数据模拟全部交互，后续替换为真实 API。

**遇到的挑战：**
组件文件较大（约2260行），需要分步生成和调整样式细节。CSS 变量作用域需要放在组件选择器内而非 :root 上，否则 scoped 样式无法穿透。

**如何引导AI修正：**
明确要求"所有样式内联在组件中（scoped）"，并指定响应式布局的断点。通过构建验证（npm run build）发现 IndentationError 后，修正了重复的 `</style>` 标签。

**产出文件：**
- frontend/src/App.vue

---

## [TDD阶段] Prompt 3：POST /api/sessions 测试与实现

**完整Prompt内容：**
[TDD阶段-测试] 请为 POST /api/sessions 接口编写完整的 pytest 测试用例。

测试用例：
1. test_create_session_success：输入有效的 topic 和 expert_count=4，验证返回 201
2. test_create_session_missing_topic：缺少 topic，验证返回 400 VALIDATION_ERROR
3. test_create_session_expert_count_out_of_range：expert_count=0，验证返回 400
4. test_create_session_default_expert_count：不传 expert_count，验证默认值为 4
5. test_create_session_generates_experts：创建成功后验证生成了正确数量的专家

注意：请只生成测试代码，不要生成实现代码。

**意图：**
先编写测试定义接口契约，再实现业务逻辑使测试通过。测试覆盖了参数校验、边界条件和默认值。

**遇到的挑战：**
Session.create() 的模型方法已存在但蓝图未调用。专家批量创建需要同时调用 Expert.bulk_create()。测试中 expert_count=None 时需要作为"未提供"处理。

**如何引导AI修正：**
先红阶段（测试通过占位实现），再绿阶段（实现逻辑）。发现 expert_count=None 返回 400 后，在蓝图中添加了 `if expert_count is None: expert_count = 4` 分支。

**产出文件：**
- tests/test_sessions.py
- app/blueprints/sessions.py (修改)

---

## [TDD阶段] Prompt 4：GET /api/sessions 测试与实现

**完整Prompt内容：**
[TDD阶段-测试] 请为 GET /api/sessions 接口编写 pytest 测试用例。

需求：返回会话列表，按 created_at 倒序排列，支持分页（page/size）和状态筛选（status）。

测试用例：
1. test_list_sessions_empty：无会话时返回空列表
2. test_list_sessions_pagination：创建 25 个会话，验证 page=2, size=10
3. test_list_sessions_status_filter：筛选 status=discussing
4. test_list_sessions_default_pagination：默认 page=1, size=20
5. test_list_sessions_invalid_page：page=0 时返回 400

**意图：**
测试列表查询的分页、筛选、参数校验功能。通过严格校验（page<1→400）定义接口契约。

**遇到的挑战：**
Session.list() 原本返回 dict，但在实现阶段改为返回 `(list, total)` 元组。测试需要适配。

**如何引导AI修正：**
将 Session.list() 改为 classmethod，返回 `(sessions_list, total_count)`。蓝图负责序列化和组装响应 JSON。

**产出文件：**
- tests/test_sessions_list.py
- app/models.py (修改)

---

## [TDD阶段] Prompt 5：SSE 事件流测试与实现

**完整Prompt内容：**
[TDD阶段-测试] 请为 GET /api/sessions/{id}/events（SSE 事件流）接口编写测试用例。

测试用例：
1. test_sse_connection_success：验证返回 200，Content-Type 为 text/event-stream
2. test_sse_session_not_found：不存在的会话返回 404
3. test_sse_heartbeat：验证 30 秒内收到 heartbeat 事件
4. test_sse_multiple_connections：同一会话多个连接独立接收事件

**意图：**
测试 SSE 流式响应的连接建立、协议格式、心跳保活和多连接隔离。

**遇到的挑战：**
SSE 是流式响应，Flask 测试客户端默认缓冲响应，会导致测试挂起。需要使用 `buffered=False` 获取底层迭代器。heartbeat 测试需等待 30 秒，通过 threading + queue 异步读取。

**如何引导AI修正：**
使用 `threading.Thread` 异步读取流式响应，`queue.Queue` 线程安全传递数据。`queue.Empty` 异常应放在 while 循环内部，避免单次超时退出。

**产出文件：**
- tests/test_sse_events.py
- app/services/transcript_stream.py (新建)

---

## [TDD阶段] Prompt 6：发言记录与结论生成测试

**完整Prompt内容：**
[TDD阶段-测试] 请为 GET /api/sessions/{id}/transcript 和 POST /api/sessions/{id}/conclusion 编写测试用例。

**意图：**
覆盖发言记录的游标分页、增量拉取和结论生成的状态校验、幂等性、响应格式。

**遇到的挑战：**
Transcript.list_by_session() 返回元组（兼容之前改动的返回格式）。结论接口通过 mock 模拟 DeepSeek API 调用。`test_conclusion_session_concluded` 需要使用 `Session.create()` 直接创建状态为 concluded 的会话。

**如何引导AI修正：**
使用 `@patch('app.blueprints.conclusion.generate_conclusion', create=True)` 允许 mock 目标在不存在时自动创建。

**产出文件：**
- tests/test_transcripts.py
- tests/test_conclusion.py

---

## [E2E阶段] Prompt 7：前后端联调

**完整Prompt内容：**
[E2E阶段-联调] 请修改 Vue 前端代码，将模拟数据替换为真实 API 调用，实现前后端完整联调。

需要修改的逻辑：
1. 创建讨论：调用 POST /api/sessions
2. 订阅 SSE 事件：使用原生 EventSource
3. 获取历史发言：调用 GET /api/sessions/{id}/transcript
4. 生成结论：调用 POST /api/sessions/{id}/conclusion

所有模拟数据全部删除，演播厅视觉风格不变。

**意图：**
将前端从 Mock 数据切换到真实后端 API。删除 300+ 行模拟数据代码，接入 fetch + EventSource。

**遇到的挑战：**
App.vue 文件约 2260 行，Edit 工具无法一次性处理如此大的替换。需要分步替换：先替换 import/Mock 数据部分，再替换核心函数。

**如何引导AI修正：**
使用 Python 脚本直接操作文件内容进行精确替换（`python -c "with open(...)"`），避免 Edit 工具的字符串匹配限制。

**产出文件：**
- frontend/src/App.vue (修改)

---

## [E2DE阶段] Prompt 8：讨论引擎与DeepSeek API集成

**完整Prompt内容：**
[E2E阶段-修复] 请创建讨论引擎服务，为SSE流生成发言内容。

新建文件：app/services/discussion_engine.py

功能：在SSE连接建立后，自动生成并推送发言序列。每2-3秒生成一条发言，按顺序：主持人开场 → 专家1 → 专家2 → ... → 专家N → 主持人串场 → ...（共3轮）。

以及后续升级：
[E2E阶段-升级] 将讨论引擎和结论生成器升级为调用真实的 DeepSeek API。

**意图：**
先实现预设发言池的讨论引擎（MVP），再升级为 DeepSeek V4 Pro 模型动态生成。

**遇到的挑战：**
预设发言池使用 `random.choice(HOST_CLOSING)` 时，HOST_CLOSING 被定义为字符串而非列表，导致返回单字符。API 调用的 speaker_id 使用 UUID 与示例值 "e001" 不匹配，专家发言被静默跳过。

**如何引导AI修正：**
修复 random.choice 字符串问题（改为列表）。修复 API 解析使用 speaker_index 替代 UUID。增加 min_tokens、调试日志和最小条数校验。

**产出文件：**
- app/services/discussion_engine.py (新建+修改)
- app/services/deepseek_client.py (新建)
- app/services/conclusion_generator.py (修改)
