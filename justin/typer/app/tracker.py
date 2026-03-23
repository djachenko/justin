from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase, SQLiteEntry


@dataclass
class TrackEntry(SQLiteEntry):
    command: str
    timestamp: str
    duration: float
    error: Optional[str] = None

    @classmethod
    def type(cls) -> str:
        return "TrackEntry"


_DB_PATH: Optional[Path] = None


def setup_tracking(cms_root: Path) -> None:
    """Call once at app startup, before any commands run."""
    global _DB_PATH
    _DB_PATH = cms_root


def write_entry(entry: TrackEntry) -> None:
    if _DB_PATH is None:
        return

    try:
        import sqlite3

        with sqlite3.connect(_DB_PATH / "tracking.db") as conn:
            conn.execute(
                "INSERT INTO TrackEntry (command, timestamp, duration, error) VALUES (?, ?, ?, ?)",
                (entry.command, entry.timestamp, entry.duration, entry.error)
            )
    except Exception:
        pass