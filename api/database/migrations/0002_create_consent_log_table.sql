CREATE TABLE IF NOT EXISTS consent_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voice_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (voice_id) REFERENCES voices (voice_id)
);

CREATE INDEX IF NOT EXISTS idx_consent_log_voice_id ON consent_log (voice_id);
