 -- ============================================================
  -- 1. 讨论会话表
  -- ============================================================
  CREATE TABLE IF NOT EXISTS sessions (
      id            TEXT PRIMARY KEY,                              -- UUID
      topic         TEXT NOT NULL,                                 -- 讨论话题
      expert_count  INTEGER NOT NULL DEFAULT 4 CHECK(expert_count BETWEEN 1 AND 10),  -- 专家人数
      status        TEXT NOT NULL DEFAULT 'pending'                -- pending | generating | discussing | concluded | error
                    CHECK(status IN ('pending','generating','discussing','concluded','error')),
      created_at    TEXT NOT NULL DEFAULT (datetime('now')),       -- ISO-8601
      updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
  );

  -- ============================================================
  -- 2. 专家表
  -- ============================================================
  CREATE TABLE IF NOT EXISTS experts (
      id            TEXT PRIMARY KEY,                              -- UUID
      session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      name          TEXT NOT NULL,                                 -- 专家姓名
      title         TEXT NOT NULL DEFAULT '',                      -- 头衔/身份
      stance        TEXT NOT NULL DEFAULT '',                      -- 立场描述
      color         TEXT NOT NULL DEFAULT '#6366f1',               -- 代表色 hex
      avatar_emoji  TEXT NOT NULL DEFAULT '🧑‍💼',                -- Emoji 头像
      sort_order    INTEGER NOT NULL DEFAULT 0,                    -- 排序
      created_at    TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_experts_session ON experts(session_id);

  -- ============================================================
  -- 3. 发言记录表
  -- ============================================================
  CREATE TABLE IF NOT EXISTS transcripts (
      id            TEXT PRIMARY KEY,                              -- UUID
      session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      speaker_type  TEXT NOT NULL CHECK(speaker_type IN ('host','expert')),  -- 发言人类别
      speaker_id    TEXT,                                          -- 专家 ID（host 时为 NULL）
      speaker_name  TEXT NOT NULL,                                 -- 显示名（冗余，避免 JOIN）
      avatar_emoji  TEXT NOT NULL DEFAULT '💬',                     -- 发言人头像
      content       TEXT NOT NULL,                                 -- 发言内容
      sequence      INTEGER NOT NULL,                              -- 全局序号（按 session 递增）
      created_at    TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_transcripts_session ON transcripts(session_id);
  CREATE INDEX IF NOT EXISTS idx_transcripts_sequence ON transcripts(session_id, sequence);

  -- ============================================================
  -- 4. 共识表
  -- ============================================================
  CREATE TABLE IF NOT EXISTS consensus (
      id            TEXT PRIMARY KEY,                              -- UUID
      session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      summary       TEXT NOT NULL,                                 -- 共识描述
      sort_order    INTEGER NOT NULL DEFAULT 0,                    -- 排序
      created_at    TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_consensus_session ON consensus(session_id);

  -- ============================================================
  -- 5. 分歧表
  -- ============================================================
  CREATE TABLE IF NOT EXISTS divergences (
      id              TEXT PRIMARY KEY,                            -- UUID
      session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      description     TEXT NOT NULL,                               -- 分歧描述
      involved_experts TEXT NOT NULL DEFAULT '[]',                 -- JSON 数组，如 ["e1","e3"]
      side_a_expert   TEXT REFERENCES experts(id),                 -- 正方专家 ID（可选）
      side_b_expert   TEXT REFERENCES experts(id),                 -- 反方专家 ID（可选）
      sort_order      INTEGER NOT NULL DEFAULT 0,                  -- 排序
      created_at      TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_divergences_session ON divergences(session_id);