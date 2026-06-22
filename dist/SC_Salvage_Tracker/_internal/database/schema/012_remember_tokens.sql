-- =====================================================
-- REMEMBER ME TOKENS
-- =====================================================

CREATE TABLE IF NOT EXISTS remember_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY(user_id)
        REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_remember_tokens_user_id
ON remember_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_remember_tokens_hash
ON remember_tokens(token_hash);
