import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import sys
import time
from coverage import Coverage
from justin_utils.singleton import Singleton


@dataclass
class TrackEntry:
    command: str
    timestamp: str
    clock_duration: float
    cpu_duration: float
    error: Optional[str] = None

    @classmethod
    def type(cls) -> str:
        return "TrackEntry"


_DB_PATH: Optional[Path] = None


class Tracker(Singleton):
    def __init__(self):
        super().__init__()

        self.__root = None

    @property
    def coverage(self):
        coverage_folder = self.__root / "coverage"
        coverage_folder.mkdir(parents=True, exist_ok=True)
        coverage_file = coverage_folder / f"{int(time.time() * 1000)}.coverage"

        coverage = Coverage(data_file=str(coverage_file))
        coverage.config.disable_warnings = [
            "module-not-measured",
            "no-data-collected",
        ]

        return coverage

    def setup(self, root: Path) -> None:
        self.__root = root

    def write(
            self,
            command: str,
            timestamp: str,
            clock_duration: float,
            cpu_duration: float,
            error: Optional[str] = None,
    ) -> None:
        with sqlite3.connect(self.__root / "tracking.db") as conn:
            conn.execute(
                "INSERT INTO TrackEntry (command, timestamp, clock_duration, cpu_duration, error) VALUES (?, ?, ?, ?, ?)",
                (command, timestamp, clock_duration, cpu_duration, error)
            )


@contextmanager
def track():
    start_timestamp = datetime.now().isoformat()

    start_global_time = time.perf_counter()
    start_system_time = time.process_time()

    argv = sys.argv
    command = " ".join(argv)
    error = None

    tracker = Tracker.instance()
    coverage = tracker.coverage

    coverage.start()

    try:
        yield
    except Exception as e:
        error = type(e).__name__ + ": " + str(e)
        raise

    finally:
        coverage.stop()
        coverage.save()

        end_global_time = time.perf_counter()
        end_system_time = time.process_time()

        tracker.write(
            command=command,
            timestamp=start_timestamp,
            clock_duration=end_global_time - start_global_time,
            cpu_duration=end_system_time - start_system_time,
            error=error,
        )
