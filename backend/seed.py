"""
AI 圆桌讨论 — 样例数据填充脚本

独立运行：python seed.py
将预设话题、专家和发言记录写入 SQLite 数据库。
"""
import os
import sqlite3
import uuid
from datetime import datetime, timezone


# ─── 数据库路径 ──────────────────────────────────────────

DB_PATH = os.environ.get(
    'DATABASE_URL',
    os.path.join(os.path.dirname(__file__), 'instance', 'roundtable.db'),
)


# ─── 预设数据 ────────────────────────────────────────────

TOPICS = [
    {
        'topic': '人工智能是否会取代人类设计师',
        'expert_count': 4,
        'experts': [
            {'name': '陈薇', 'title': 'UI/UX 设计总监 · 阿里巴巴',
             'stance': 'AI 是工具，创意仍需人类主导', 'color': '#6366f1', 'avatar_emoji': '🎨'},
            {'name': '刘明远', 'title': 'AI 生成艺术研究者 · 中央美院',
             'stance': 'AI 已能独立完成高质量设计作品', 'color': '#10b981', 'avatar_emoji': '🧑‍🎨'},
            {'name': '周婷', 'title': '品牌策略顾问 · 奥美',
             'stance': '设计行业将重构，而非被取代', 'color': '#f59e0b', 'avatar_emoji': '👩‍💼'},
            {'name': '王浩宇', 'title': '前端工程师 · 字节跳动',
             'stance': 'AI 辅助设计让开发效率提升 10 倍', 'color': '#ef4444', 'avatar_emoji': '👨‍💻'},
        ],
        'transcripts': [
            ('host', '各位专家好，今天我们讨论的话题是：AI 是否会取代人类设计师。请大家畅所欲言。'),
            ('expert_0', 'AI 确实强大，但目前仍无法替代人类设计师的审美判断和情感理解。'),
            ('expert_1', '我持不同观点。最新的 AI 设计工具已经能生成媲美专业水准的视觉作品。'),
            ('expert_2', '我认为行业会重构而非取代。设计师的角色将从执行者转变为策略者。'),
            ('expert_3', '从工程角度看，AI 辅助工具让我们的设计稿到代码的转化效率提升了至少 10 倍。'),
            ('host', '非常精彩的观点！那么 AI 在设计教育领域会产生什么影响？'),
            ('expert_0', '设计教育需要改革，学生必须学会与 AI 协作，而不是单纯学习软件操作。'),
            ('expert_1', 'AI 降低了设计门槛，让更多人能参与创作，这是好事。'),
        ],
    },
    {
        'topic': '自动驾驶的安全责任归属',
        'expert_count': 4,
        'experts': [
            {'name': '张明远', 'title': '自动驾驶算法专家 · 百度 Apollo',
             'stance': '技术成熟度已足够，法规需要先行', 'color': '#8b5cf6', 'avatar_emoji': '🚗'},
            {'name': '李雪琴', 'title': '交通法规教授 · 中国政法大学',
             'stance': '责任归属是当前最大障碍', 'color': '#ec4899', 'avatar_emoji': '👩‍⚖️'},
            {'name': '赵铁柱', 'title': '保险精算师 · 平安产险',
             'stance': '需要新的保险模型来覆盖自动驾驶风险', 'color': '#14b8a6', 'avatar_emoji': '📊'},
            {'name': '王思涵', 'title': '车辆工程专家 · 清华大学',
             'stance': '人机共驾过渡期的安全问题最复杂', 'color': '#f97316', 'avatar_emoji': '🔧'},
        ],
        'transcripts': [
            ('host', '各位好，今天讨论自动驾驶的安全责任归属问题。'),
            ('expert_0', '从技术角度看，L4 级自动驾驶的安全性已超过人类驾驶员。'),
            ('expert_1', '但法律上责任归属仍不明确——事故由车主、制造商还是算法承担？'),
            ('expert_2', '保险行业需要全新的精算模型来覆盖自动驾驶模式下的风险。'),
            ('expert_3', '人机共驾的过渡期是最大的挑战，责任划分尤其困难。'),
            ('host', '感谢各位的深入分析。在法规完善之前，我们应该如何推进这项技术？'),
            ('expert_0', '可以先从封闭场景开始，如自动驾驶出租车在限定区域内运营。'),
            ('expert_1', '同意。试点运营的同时积累数据，为立法提供依据。'),
        ],
    },
    {
        'topic': '远程办公对城市发展的长期影响',
        'expert_count': 4,
        'experts': [
            {'name': '林小婉', 'title': '城市经济学教授 · 复旦大学',
             'stance': '远程办公将重塑城市空间结构', 'color': '#6366f1', 'avatar_emoji': '🏙️'},
            {'name': '孙浩', 'title': 'HR 科技副总裁 · 携程',
             'stance': '混合办公是未来主流模式', 'color': '#10b981', 'avatar_emoji': '💼'},
            {'name': '赵雅文', 'title': '商业地产分析师 · 仲量联行',
             'stance': '商业地产面临结构性转型', 'color': '#f59e0b', 'avatar_emoji': '🏢'},
            {'name': '吴明', 'title': '社会学家 · 北京大学',
             'stance': '远程办公加剧了社会不平等', 'color': '#ef4444', 'avatar_emoji': '📚'},
        ],
        'transcripts': [
            ('host', '各位专家好，今天的话题是远程办公对城市发展的长期影响。'),
            ('expert_0', '远程办公正在推动城市从单中心向多中心结构演变。'),
            ('expert_1', '混合办公模式将成为常态，完全远程和完全线下都会减少。'),
            ('expert_2', '商业地产需求确实在下降，但品质更高的办公空间反而更受欢迎。'),
            ('expert_3', '但我们要看到，远程办公并不适合所有人群，低收入群体反而更依赖线下工作。'),
            ('host', '非常有启发性的视角。那么对于城市规划者来说，应该如何应对？'),
            ('expert_0', '城市规划应该增加社区级别的混合功能空间，减少通勤距离。'),
            ('expert_1', '企业也需要重新设计组织管理方式，适应分布式团队。'),
        ],
    },
    {
        'topic': '量子计算的商业化前景',
        'expert_count': 4,
        'experts': [
            {'name': '钱学思', 'title': '量子物理研究员 · 中科院量子卓越中心',
             'stance': '通用量子计算还需 10-15 年', 'color': '#8b5cf6', 'avatar_emoji': '🔬'},
            {'name': '马晓芸', 'title': '量子计算产品经理 · 本源量子',
             'stance': '特定领域量子优势已可实现', 'color': '#ec4899', 'avatar_emoji': '💻'},
            {'name': '黄磊', 'title': '科技投资合伙人 · 红杉中国',
             'stance': '资本需要理性看待量子计算的 ROI', 'color': '#14b8a6', 'avatar_emoji': '💰'},
            {'name': '陈思远', 'title': '密码学专家 · 阿里巴巴安全部',
             'stance': '量子计算对现有加密体系的威胁被夸大了', 'color': '#f97316', 'avatar_emoji': '🔐'},
        ],
        'transcripts': [
            ('host', '欢迎各位！今天我们探讨量子计算的商业化前景。'),
            ('expert_0', '量子纠错技术仍在早期阶段，通用量子计算机至少还需十年。'),
            ('expert_1', '但在量子化学模拟和优化问题领域，近期已有突破性进展。'),
            ('expert_2', '投资界对量子计算的关注度很高，但需要管理好预期。'),
            ('expert_3', '后量子密码学的标准化工作正在推进，不必过度恐慌。'),
            ('host', '各位的观点非常专业。量子计算在金融领域可能最先落地吗？'),
            ('expert_0', '金融领域的组合优化和风险评估确实是量子计算的理想应用场景。'),
            ('expert_1', '药物研发也是近期最有潜力的商业化方向。'),
        ],
    },
    {
        'topic': 'AI 时代的教育体系如何变革',
        'expert_count': 4,
        'experts': [
            {'name': '张明', 'title': '教育技术专家 · 北京师范大学',
             'stance': '教育体系必须从知识传授转向能力培养', 'color': '#6366f1', 'avatar_emoji': '📖'},
            {'name': '陈小艺', 'title': 'AI 教育创业者 · 松鼠 AI',
             'stance': '个性化学习是 AI 教育最大的价值', 'color': '#10b981', 'avatar_emoji': '🤖'},
            {'name': '李国平', 'title': '高中校长 · 人大附中',
             'stance': '一线教育者需要 AI 工具而非取代', 'color': '#f59e0b', 'avatar_emoji': '👨‍🏫'},
            {'name': '刘嘉', 'title': '认知科学家 · 清华大学脑与智能实验室',
             'stance': 'AI 时代更需要培养批判性思维和创造力', 'color': '#ef4444', 'avatar_emoji': '🧠'},
        ],
        'transcripts': [
            ('host', '各位专家，今天我们讨论 AI 时代教育体系如何变革。'),
            ('expert_0', '现在的教育体系是工业时代的产物，AI 时代需要彻底重构。'),
            ('expert_1', 'AI 已经能实现真正的个性化学习路径，每个学生都能有专属 AI 老师。'),
            ('expert_2', '从一线经验看，老师最需要的不是被取代，而是能减轻负担的 AI 工具。'),
            ('expert_3', '教育的目标应该转向培养批判性思维和创造力，这些是 AI 无法替代的。'),
            ('host', '非常有深度的分享。那么考试评价体系应该如何改革？'),
            ('expert_0', '应该从知识记忆的考核转向项目制、探究式能力的评估。'),
            ('expert_1', 'AI 辅助评估可以做到更客观、更全面，减少人为偏差。'),
        ],
    },
]


# ─── 数据库操作 ──────────────────────────────────────────

def get_conn():
    """获取数据库连接。"""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_tables(conn):
    """初始化表结构（幂等）。"""
    schema = """
    CREATE TABLE IF NOT EXISTS sessions (
        id            TEXT PRIMARY KEY,
        topic         TEXT NOT NULL,
        expert_count  INTEGER NOT NULL DEFAULT 4 CHECK(expert_count BETWEEN 1 AND 10),
        status        TEXT NOT NULL DEFAULT 'pending'
                      CHECK(status IN ('pending','generating','discussing','concluded','error')),
        created_at    TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS experts (
        id            TEXT PRIMARY KEY,
        session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        name          TEXT NOT NULL,
        title         TEXT NOT NULL DEFAULT '',
        stance        TEXT NOT NULL DEFAULT '',
        color         TEXT NOT NULL DEFAULT '#6366f1',
        avatar_emoji  TEXT NOT NULL DEFAULT '🧑‍💼',
        sort_order    INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS transcripts (
        id            TEXT PRIMARY KEY,
        session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        speaker_type  TEXT NOT NULL CHECK(speaker_type IN ('host','expert')),
        speaker_id    TEXT,
        speaker_name  TEXT NOT NULL,
        avatar_emoji  TEXT NOT NULL DEFAULT '💬',
        content       TEXT NOT NULL,
        sequence      INTEGER NOT NULL,
        created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS consensus (
        id            TEXT PRIMARY KEY,
        session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        summary       TEXT NOT NULL,
        sort_order    INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS divergences (
        id              TEXT PRIMARY KEY,
        session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        description     TEXT NOT NULL,
        involved_experts TEXT NOT NULL DEFAULT '[]',
        side_a_expert   TEXT REFERENCES experts(id),
        side_b_expert   TEXT REFERENCES experts(id),
        sort_order      INTEGER NOT NULL DEFAULT 0,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """
    conn.executescript(schema)
    conn.commit()


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def seed():
    """填充样例数据。"""
    conn = get_conn()
    init_tables(conn)
    cursor = conn.cursor()

    print(f'📦 数据库：{DB_PATH}')
    print(f'📝 共 {len(TOPICS)} 个预设话题\n')

    for topic_data in TOPICS:
        now = _now()
        session_id = _uuid()
        topic = topic_data['topic']
        expert_count = topic_data['expert_count']

        # 插入会话
        cursor.execute(
            'INSERT INTO sessions (id, topic, expert_count, status, created_at, updated_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (session_id, topic, expert_count, 'concluded', now, now),
        )
        print(f'  ✅ 会话：{topic}')

        # 插入专家
        expert_ids = {}
        for i, expert in enumerate(topic_data['experts']):
            eid = _uuid()
            expert_ids[f'expert_{i}'] = eid
            cursor.execute(
                'INSERT INTO experts (id, session_id, name, title, stance, color, avatar_emoji, sort_order, created_at) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (eid, session_id, expert['name'], expert['title'], expert['stance'],
                 expert['color'], expert['avatar_emoji'], i + 1, now),
            )

        # 插入发言记录
        for seq, (speaker_type, content) in enumerate(topic_data['transcripts'], 1):
            tid = _uuid()
            if speaker_type == 'host':
                cursor.execute(
                    'INSERT INTO transcripts (id, session_id, speaker_type, speaker_id, '
                    'speaker_name, avatar_emoji, content, sequence, created_at) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (tid, session_id, 'host', None, '主持人', '🎙️', content, seq, now),
                )
            else:
                eid = expert_ids.get(speaker_type)
                expert = topic_data['experts'][int(speaker_type.split('_')[1])]
                cursor.execute(
                    'INSERT INTO transcripts (id, session_id, speaker_type, speaker_id, '
                    'speaker_name, avatar_emoji, content, sequence, created_at) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (tid, session_id, 'expert', eid, expert['name'],
                     expert['avatar_emoji'], content, seq, now),
                )

        # 插入共识
        consensus_list = topic_data.get('consensus', [
            f'与会专家一致认为{topic}具有深远影响',
            '各方均认同需要多方协作来应对挑战',
        ])
        for i, summary in enumerate(consensus_list, 1):
            cursor.execute(
                'INSERT INTO consensus (id, session_id, summary, sort_order, created_at) '
                'VALUES (?, ?, ?, ?, ?)',
                (_uuid(), session_id, summary, i, now),
            )

        # 插入分歧（可选）
        divergences = topic_data.get('divergences', [
            '在具体实施路径和时间线上存在不同看法',
        ])
        for i, desc in enumerate(divergences, 1):
            cursor.execute(
                'INSERT INTO divergences (id, session_id, description, involved_experts, sort_order, created_at) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (_uuid(), session_id, desc, '[]', i, now),
            )

        print(f'    ├ 专家：{len(topic_data["experts"])} 位')
        print(f'    ├ 发言：{len(topic_data["transcripts"])} 条')
        print(f'    └ 状态：concluded\n')

    conn.commit()
    conn.close()

    print(f'🎉 填充完成！共 {len(TOPICS)} 个话题、{sum(len(t["experts"]) for t in TOPICS)} 位专家、'
          f'{sum(len(t["transcripts"]) for t in TOPICS)} 条发言记录。')


if __name__ == '__main__':
    seed()
