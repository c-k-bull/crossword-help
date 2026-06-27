CREATE TABLE IF NOT EXISTS searches (
    id SERIAL PRIMARY KEY,
    mode TEXT NOT NULL,
    pattern TEXT,
    clue TEXT,
    letters TEXT,
    meaning TEXT,
    result_count INTEGER NOT NULL DEFAULT 0,
    top_result TEXT,
    was_correct BOOLEAN NOT NULL DEFAULT TRUE,
    corrected_answer TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS searches_created_at_idx ON searches (created_at DESC);
CREATE INDEX IF NOT EXISTS searches_mode_idx ON searches (mode);
CREATE INDEX IF NOT EXISTS searches_was_correct_idx ON searches (was_correct);
