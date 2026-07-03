"""
AI 圆桌讨论 — 数据库工具

提供数据库初始化、连接获取等基础设施。
"""
import os
import sqlite3
from flask import current_app


def get_db():
    """获取当前请求的数据库连接。"""
    if 'db' not in current_app.extensions:
        db_path = current_app.config['DATABASE']
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        current_app.extensions['db'] = conn
    return current_app.extensions['db']


def close_db(exception=None):
    """关闭数据库连接。"""
    conn = current_app.extensions.pop('db', None)
    if conn:
        conn.close()


def init_db():
    """初始化数据库表结构（幂等）。"""
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'doc', 'docs', 'schema.sql',
    )
    # 如果 schema.sql 不可用，使用内联 DDL
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
    else:
        schema_sql = _INLINE_SCHEMA

    db_path = current_app.config['DATABASE']
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


# ─── 内联 DDL（兜底，与 doc/docs/schema.sql 保持同步）────────────────────

_INLINE_SCHEMA = """
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
CREATE INDEX IF NOT EXISTS idx_experts_session ON experts(session_id);

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
CREATE INDEX IF NOT EXISTS idx_transcripts_session ON transcripts(session_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_sequence ON transcripts(session_id, sequence);

CREATE TABLE IF NOT EXISTS consensus (
    id            TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    summary       TEXT NOT NULL,
    sort_order    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_consensus_session ON consensus(session_id);

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
CREATE INDEX IF NOT EXISTS idx_divergences_session ON divergences(session_id);
"""
