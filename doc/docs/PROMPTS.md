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