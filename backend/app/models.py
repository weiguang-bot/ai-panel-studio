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

    @staticmethod
    def list_by_session(session_id, cursor=None, limit=100):
        conn = _get_db()
        try:
            query = 'SELECT * FROM transcripts WHERE session_id = ?'
            params = [session_id]
            if cursor is not None:
                query += ' AND sequence > ?'
                params.append(cursor)
            query += ' ORDER BY sequence ASC LIMIT ?'
            params.append(limit + 1)  # 多取一条判断 has_more

            rows = conn.execute(query, params).fetchall()
            has_more = len(rows) > limit
            items = [Transcript(r).to_dict() for r in rows[:limit]]
            next_cursor = items[-1]['sequence'] if items else None

            return {
                'transcripts': items,
                'next_cursor': next_cursor if has_more else None,
                'has_more': has_more,
            }
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════
# Consensus — 共识
# ══════════════════════════════════════════════════════════════════════════
class Consensus:
    """共识模型，对应 consensus 表。"""

    TABLE = 'consensus'
