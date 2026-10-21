import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

CREATE = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at         TEXT NOT NULL,
    finished_at        TEXT,
    duration_sec       REAL,
    status             TEXT NOT NULL,
    rows_extracted     INTEGER,
    duplicates_removed INTEGER,
    rows_rejected      INTEGER,
    rows_loaded        INTEGER,
    error_message      TEXT
);
"""


class RunTracker:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.stats = {}
        self.started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._t0 = time.perf_counter()

    def finish(self, status: str, error: str | None = None) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute(CREATE)
            conn.execute(
                """INSERT INTO pipeline_runs
                   (started_at, finished_at, duration_sec, status, rows_extracted,
                    duplicates_removed, rows_rejected, rows_loaded, error_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.started_at,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    round(time.perf_counter() - self._t0, 2),
                    status,
                    self.stats.get("rows_extracted"),
                    self.stats.get("duplicates_removed"),
                    self.stats.get("rows_rejected"),
                    self.stats.get("rows_loaded"),
                    error,
                ),
            )
        conn.close()