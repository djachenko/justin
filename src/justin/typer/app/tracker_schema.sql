-- .justin/cms/tracking.db schema
-- Создать один раз вручную: sqlite3 ~/.justin/cms/tracking.db < tracking_schema.sql

CREATE TABLE IF NOT EXISTS TrackEntry (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    command         TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL,
    clock_duration  INTEGER NOT NULL,
    cpu_duration    INTEGER NOT NULL,
    error           TEXT
);