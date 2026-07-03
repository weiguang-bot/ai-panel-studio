"""
AI 圆桌讨论 — 数据模型

使用原生 sqlite3 模块，基于 docs/schema.sql 定义的 DDL。
每个模型对应一个表，提供基础的 CRUD 静态方法。
"""
import uuid
from datetime import datetime, timezone
from flask import current_app


def _get_db():
    """获取当前应用的数据库连接。"""
    import sqlite3
    db_path = current_app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _gen_id():
    """生成 UUID 字符串。"""
    return str(uuid.uuid4())


def _now():
    """返回当前 UTC ISO-8601 时间字符串。"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


# ══════════════════════════════════════════════════════════════════════════
# Session — 讨论会话
# ══════════════════════════════════════════════════════════════════════════
class Session:
    """讨论会话模型，对应 sessions 表。"""

    TABLE = 'sessions'
    ALLOWED_STATUSES = ('pending', 'generating', 'discussing', 'concluded', 'error')

    def __init__(self, row):
        self.id = row['id']
        self.topic = row['topic']
        self.expert_count = row['expert_count']
        self.status = row['status']
        self.created_at = row['created_at']
        self.updated_at = row['updated_at']

    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'expert_count': self.expert_count,
            'status': self.status,
            'created_at': self.created_at,
        }

    # ── CRUD ──────────────────────────────────────────

    @staticmethod
    def create(topic, expert_count=4):
        conn = _get_db()
        try:
            sid = _gen_id()
            now = _now()
            conn.execute(
                'INSERT INTO sessions (id, topic, expert_count, status, created_at, updated_at) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (sid, topic, expert_count, 'pending', now, now),
            )
            conn.commit()
            return Session.get(sid)
        finally:
            conn.close()

    @staticmethod
    def get(session_id):
        conn = _get_db()
        try:
            row = conn.execute(
                'SELECT * FROM sessions WHERE id = ?', (session_id,)
            ).fetchone()
            return Session(row) if row else None
        finally:
            conn.close()

    @classmethod
    def list(cls, page=1, size=20, status=None):
        """获取会话列表，支持分页和状态筛选。

        返回:
            (sessions_list, total_count)
            - sessions_list: 当前页的 Session 对象列表
            - total_count: 符合条件的总记录数
        """
        conn = _get_db()
        try:
            query = 'SELECT * FROM sessions'
            count_query = 'SELECT COUNT(*) FROM sessions'
            params = []
            count_params = []

            if status:
                query += ' WHERE status = ?'
                count_query += ' WHERE status = ?'
                params.append(status)
                count_params.append(status)

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            offset = (page - 1) * size
            params.extend([size, offset])

            rows = conn.execute(query, params).fetchall()
            total = conn.execute(count_query, count_params).fetchone()[0]

            sessions_list = [cls(r) for r in rows]
            return sessions_list, total
        finally:
            conn.close()

    @staticmethod
    def update_status(session_id, new_status):
        if new_status not in Session.ALLOWED_STATUSES:
            raise ValueError(f'Invalid status: {new_status}')
        conn = _get_db()
        try:
            now = _now()
            conn.execute(
                'UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?',
                (new_status, now, session_id),
            )
            conn.commit()
            return Session.get(session_id)
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════
# Expert — 专家
# ══════════════════════════════════════════════════════════════════════════
class Expert:
    """专家模型，对应 experts 表。"""

    TABLE = 'experts'

    def __init__(self, row):
        self.id = row['id']
        self.session_id = row['session_id']
        self.name = row['name']
        self.title = row['title']
        self.stance = row['stance']
        self.color = row['color']
        self.avatar_emoji = row['avatar_emoji']
        self.sort_order = row['sort_order']

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'name': self.name,
            'title': self.title,
            'stance': self.stance,
            'color': self.color,
            'avatar_emoji': self.avatar_emoji,
            'sort_order': self.sort_order,
        }

    # ── CRUD ──────────────────────────────────────────

    @staticmethod
    def bulk_create(session_id, experts_data):
        """批量插入专家数据。
        experts_data: list of dicts with keys: name, title, stance, color, avatar_emoji, sort_order
        """
        conn = _get_db()
        try:
            rows = []
            for ed in experts_data:
                eid = _gen_id()
                conn.execute(
                    'INSERT INTO experts (id, session_id, name, title, stance, color, avatar_emoji, sort_order) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (eid, session_id, ed['name'], ed['title'], ed['stance'],
                     ed['color'], ed['avatar_emoji'], ed.get('sort_order', 0)),
                )
                rows.append(eid)
            conn.commit()
            return Expert.list_by_session(session_id)
        finally:
            conn.close()

    @staticmethod
    def list_by_session(session_id):
        conn = _get_db()
        try:
            rows = conn.execute(
                'SELECT * FROM experts WHERE session_id = ? ORDER BY sort_order',
                (session_id,),
            ).fetchall()
            return [Expert(r).to_dict() for r in rows]
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════
# Transcript — 发言记录
# ══════════════════════════════════════════════════════════════════════════
class Transcript:
    """发言记录模型，对应 transcripts 表。"""

    TABLE = 'transcripts'

    def __init__(self, row):
        self.id = row['id']
        self.session_id = row['session_id']
        self.speaker_type = row['speaker_type']
        self.speaker_id = row['speaker_id']
        self.speaker_name = row['speaker_name']
        self.avatar_emoji = row['avatar_emoji']
        self.content = row['content']
        self.sequence = row['sequence']
        self.created_at = row['created_at']

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'speaker_type': self.speaker_type,
            'speaker_id': self.speaker_id,
            'speaker_name': self.speaker_name,
            'avatar_emoji': self.avatar_emoji,
            'content': self.content,
            'sequence': self.sequence,
            'created_at': self.created_at,
        }

    # ── CRUD ──────────────────────────────────────────

    @staticmethod
    def create(session_id, speaker_type, speaker_name, content, avatar_emoji='💬',
               speaker_id=None):
        conn = _get_db()
        try:
            tid = _gen_id()
            now = _now()
            # 获取当前最大 sequence
            last = conn.execute(
                'SELECT MAX(sequence) as mx FROM transcripts WHERE session_id = ?',
                (session_id,),
            ).fetchone()
            seq = (last['mx'] or 0) + 1

            conn.execute(
                'INSERT INTO transcripts (id, session_id, speaker_type, speaker_id, '
                'speaker_name, avatar_emoji, content, sequence, created_at) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (tid, session_id, speaker_type, speaker_id, speaker_name,
                 avatar_emoji, content, seq, now),
            )
            conn.commit()
            return Transcript.get(tid)
        finally:
            conn.close()

    @staticmethod
    def get(transcript_id):
        conn = _get_db()
        try:
            row = conn.execute(
                'SELECT * FROM transcripts WHERE id = ?', (transcript_id,)
            ).fetchone()
            return Transcript(row) if row else None
        finally:
            conn.close()

    @classmethod
    def list_by_session(cls, session_id, cursor=None, limit=50, after=None):
        """按 session 查询发言记录，支持游标分页和增量拉取。

        参数：
            session_id: 会话 UUID
            cursor: 游标值（sequence），返回该值之后的记录
            limit: 每页条数（默认 50）
            after: 增量拉取起点（与 cursor 语义相同）

        返回：
            (transcripts_list, next_cursor)
            - transcripts_list: Transcript 对象列表（按 sequence ASC）
            - next_cursor: 最后一条的 sequence；无更多数据时返回 None
        """
        conn = _get_db()
        try:
            query = 'SELECT * FROM transcripts WHERE session_id = ?'
            params = [session_id]

            # cursor 和 after 语义相同：返回该值之后的记录
            cursor_val = cursor if cursor is not None else after
            if cursor_val is not None:
                query += ' AND sequence > ?'
                params.append(cursor_val)

            query += ' ORDER BY sequence ASC LIMIT ?'
            params.append(limit + 1)  # 多取一条判断 has_more

            rows = conn.execute(query, params).fetchall()
            has_more = len(rows) > limit
            items = [cls(r) for r in rows[:limit]]
            next_cursor = items[-1].sequence if items and has_more else None

            return items, next_cursor
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════
# Consensus — 共识
# ══════════════════════════════════════════════════════════════════════════
class Consensus:
    """共识模型，对应 consensus 表。"""

    TABLE = 'consensus'

    def __init__(self, row):
        self.id = row['id']
        self.session_id = row['session_id']
        self.summary = row['summary']
        self.sort_order = row['sort_order']
        self.created_at = row['created_at']

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'summary': self.summary,
            'sort_order': self.sort_order,
            'created_at': self.created_at,
        }

    # ── CRUD ──────────────────────────────────────────

    @staticmethod
    def bulk_create(session_id, consensus_list):
        """批量创建共识记录。
        consensus_list: [{'summary': str, 'degree': str, 'order_index': int}]
        """
        conn = _get_db()
        try:
            cids = []
            for item in consensus_list:
                cid = _gen_id()
                now = _now()
                conn.execute(
                    'INSERT INTO consensus (id, session_id, summary, sort_order, created_at) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (cid, session_id, item['summary'], item['order_index'], now),
                )
                cids.append(cid)
            conn.commit()
            return Consensus.list_by_session(session_id)
        finally:
            conn.close()

    @staticmethod
    def list_by_session(session_id):
        conn = _get_db()
        try:
            rows = conn.execute(
                'SELECT * FROM consensus WHERE session_id = ? ORDER BY sort_order',
                (session_id,),
            ).fetchall()
            return [Consensus(r).to_dict() for r in rows]
        finally:
            conn.close()

    @staticmethod
    def delete_by_session(session_id):
        conn = _get_db()
        try:
            conn.execute('DELETE FROM consensus WHERE session_id = ?', (session_id,))
            conn.commit()
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════
# Divergence — 分歧
# ══════════════════════════════════════════════════════════════════════════
class Divergence:
    """分歧模型，对应 divergences 表。"""

    TABLE = 'divergences'

    def __init__(self, row):
        self.id = row['id']
        self.session_id = row['session_id']
        self.description = row['description']
        self.involved_experts = row['involved_experts']  # JSON 字符串
        self.side_a_expert = row['side_a_expert']
        self.side_b_expert = row['side_b_expert']
        self.sort_order = row['sort_order']
        self.created_at = row['created_at']

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'session_id': self.session_id,
            'description': self.description,
            'involved_experts': json.loads(self.involved_experts) if self.involved_experts else [],
            'sort_order': self.sort_order,
            'created_at': self.created_at,
        }

    # ── CRUD ──────────────────────────────────────────

    @staticmethod
    def bulk_create(session_id, divergences_list):
        """批量创建分歧记录。
        divergences_list: [{'description': str, 'severity': str,
                           'involved_expert_ids': list, 'order_index': int}]
        """
        conn = _get_db()
        try:
            dids = []
            for item in divergences_list:
                did = _gen_id()
                now = _now()
                involved = json.dumps(
                    item.get('involved_expert_ids', []),
                    ensure_ascii=False,
                )
                conn.execute(
                    'INSERT INTO divergences (id, session_id, description, involved_experts, '
                    'sort_order, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (did, session_id, item['description'], involved,
                     item['order_index'], now),
                )
                dids.append(did)
            conn.commit()
            return Divergence.list_by_session(session_id)
        finally:
            conn.close()

    @staticmethod
    def list_by_session(session_id):
        conn = _get_db()
        try:
            rows = conn.execute(
                'SELECT * FROM divergences WHERE session_id = ? ORDER BY sort_order',
                (session_id,),
            ).fetchall()
            return [Divergence(r).to_dict() for r in rows]
        finally:
            conn.close()

    @staticmethod
    def delete_by_session(session_id):
        conn = _get_db()
        try:
            conn.execute('DELETE FROM divergences WHERE session_id = ?', (session_id,))
            conn.commit()
        finally:
            conn.close()
