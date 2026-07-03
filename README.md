# AI Panel Studio (AI 圆桌讨论)

> AI 驱动的虚拟圆桌讨论 Web 应用 — 输入话题，即刻生成一场由虚拟专家参与的实时讨论。

**实现效果**：输入「人工智能是否会取代人类工作」，系统在 3 秒内创建 4 位不同立场的虚拟专家，通过 SSE 实时推送 3 轮讨论发言，讨论结束后自动生成共识与分歧摘要。

---

## 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | Vue 3 (Composition API) | ^3.4.0 |
| 构建工具 | Vite | ^5.4.0 |
| 后端框架 | Flask | 2.3.3 |
| 数据库 | SQLite (WAL 模式) | — |
| 实时通信 | Server-Sent Events | — |
| AI 模型 | DeepSeek V4 Pro | — |
| 测试框架 | pytest + pytest-flask | 8.0.0 |

---

## 环境要求

- **Python** ≥ 3.11
- **Node.js** ≥ 18
- **npm** ≥ 9

---

## 快速启动

### 1. 后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制并填写密钥）
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY（可选，不填则使用预设模板）

# 启动服务
python run.py
# → Flask 运行在 http://localhost:8080
```

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# → Vite 运行在 http://localhost:5173
```

### 3. 验证

打开浏览器访问 http://localhost:5173，输入话题并点击"开始讨论"，即可看到实时发言流。

---

## 环境变量

| 变量 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `DEEPSEEK_API_KEY` | 否 | DeepSeek API 密钥（不填则使用预设模板） | — |
| `DATABASE_URL` | 否 | SQLite 数据库路径 | `instance/roundtable.db` |
| `PORT` | 否 | 服务端口 | `8080` |
| `FLASK_ENV` | 否 | 运行环境 | `development` |

---

## 核心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/sessions` | 创建讨论会话，返回专家列表 |
| `GET` | `/api/sessions` | 获取会话列表（分页、按状态筛选） |
| `GET` | `/api/sessions/{id}` | 获取会话详情（含专家列表） |
| `GET` | `/api/sessions/{id}/events` | **SSE 事件流**：订阅实时发言 |
| `GET` | `/api/sessions/{id}/transcript` | 获取完整发言记录（游标分页） |
| `POST` | `/api/sessions/{id}/conclusion` | 生成共识分歧摘要（幂等） |
| `GET` | `/api/health` | 健康检查 |

### SSE 事件类型

| 事件 | 说明 | 推送时机 |
|------|------|----------|
| `session.status` | 会话状态变更 | 状态切换时（generating→discussing→concluded） |
| `transcript.new` | 新发言 | AI 每次发言后 |
| `heartbeat` | 保活信号 | 每 30 秒 |
| `session.error` | 错误 | 出错时 |

---

## 项目结构

```
AI Panel Studio/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask 应用工厂
│   │   ├── models.py            # SQLite 数据模型（5 个实体）
│   │   ├── blueprints/
│   │   │   ├── sessions.py      # 会话管理 + SSE 端点
│   │   │   ├── transcripts.py   # 发言记录查询
│   │   │   └── conclusion.py    # 结论生成
│   │   └── services/
│   │       ├── deepseek_client.py    # DeepSeek API 客户端
│   │       ├── discussion_engine.py  # 讨论发言引擎
│   │       ├── expert_generator.py   # 专家生成器
│   │       └── transcript_stream.py  # SSE 流服务
│   ├── tests/                   # 55 个 pytest 测试用例
│   ├── run.py                   # 入口文件
│   ├── seed.py                  # 样例数据填充脚本
│   └── requirements.txt
├── frontend/
│   ├── src/App.vue              # 主页面单文件组件（~2260 行）
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── docs/
│   ├── PRD.md                   # 产品需求文档
│   ├── docs/
│   │   ├── api.yaml             # OpenAPI 3.0 契约
│   │   ├── schema.sql           # DDL 建表语句
│   │   ├── ER.md                # ER 图
│   │   └── PROMPTS.md           # Prompt 工程记录
└── WORKFLOW.md                  # 开发工作流说明
```

---

## 已完成功能

- [x] 话题输入 + 专家人数配置（2-10 人）
- [x] AI 生成虚拟专家（姓名、头衔、立场、配色）
- [x] SSE 实时推送 3 轮讨论发言
- [x] 嘉宾席展示 + 当前发言人高亮 + 声波动画
- [x] 发言活跃度统计 + 发言总数计数
- [x] 游标分页查询历史发言
- [x] 自动/手动生成共识分歧摘要
- [x] 沉浸式深色演播厅 UI + Glassmorphism
- [x] 响应式布局（超宽屏 / 桌面 / 平板 / 手机）
- [x] DeepSeek V4 Pro 模型集成（真实 AI 调用）
- [x] 55 个 pytest 测试全部通过
- [x] 样例数据填充脚本（5 个话题）

---

## 后续改进方向

### 1. 用户系统与会话持久化
当前所有会话数据存储在本地 SQLite 文件中，重启后保留但无法跨设备访问。后续可引入用户认证体系，将会话关联到用户账号，支持查看历史讨论记录。

### 2. AI 生成的深度提升
MVP 阶段的讨论发言基于 DeepSeek 模型调用。后续可以：
- 让 AI 阅读真实文献或新闻后生成更有论据支持的发言
- 支持用户上传参考资料，讨论内容基于用户提供的材料展开
- 增加反驳机制——专家之间可以相互质疑，提升讨论的真实感

### 3. 讨论导出与分享
支持将完整讨论导出为 Markdown/PDF 格式，或生成分享链接。这对于知识工作者和内容创作者的日常使用场景至关重要。

### 4. WebSocket 替代 SSE（可选）
当前使用 SSE 协议通信，优点是浏览器原生支持、实现简单。缺点是不支持双向通信（客户端→服务器）。如果未来需要实时投票、观众提问等交互功能，可考虑迁移到 WebSocket。

### 5. 性能优化
- 当前 SSE 发言使用 `time.sleep()` 控制间隔，可改为异步任务队列
- 数据库查询可增加连接池，减少重复连接的消耗
- 前端发言列表可虚拟化渲染，优化超长讨论的性能
