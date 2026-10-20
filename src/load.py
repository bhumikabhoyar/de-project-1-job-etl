import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS job_postings (
    job_id          TEXT PRIMARY KEY,
    job_title       TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    skills          TEXT,
    posted_date     TEXT,
    job_type        TEXT,
    salary_min_lpa  REAL,
    salary_max_lpa  REAL,
    exp_min_years   REAL,
    exp_max_years   REAL,
    loaded_at       TEXT NOT NULL
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_jobs_location ON job_postings(location);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_title ON job_postings(job_title);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_posted ON job_postings(posted_date);",
]

COLUMNS = [
    "job_id", "job_title", "company", "location", "skills", "posted_date",
    "job_type", "salary_min_lpa", "salary_max_lpa", "exp_min_years",
    "exp_max_years", "loaded_at",
]

UPSERT = f"""
INSERT INTO job_postings ({", ".join(COLUMNS)})
VALUES ({", ".join("?" for _ in COLUMNS)})
ON CONFLICT(job_id) DO UPDATE SET
    {", ".join(f"{c} = excluded.{c}" for c in COLUMNS if c != "job_id")};
"""


def load_to_sqlite(df: pd.DataFrame, db_path: str) -> int:
    """Upsert rows into SQLite. Returns the total row count in the table."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Load started: %d rows -> %s", len(df), db_path)

    df = df.copy()
    df["loaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # SQLite needs None (not NaN) for NULL
    records = df[COLUMNS].astype(object).where(df[COLUMNS].notna(), None)
    rows = list(records.itertuples(index=False, name=None))

    conn = sqlite3.connect(db_path)
    try:
        with conn:  # one transaction: all rows load, or none do
            conn.execute(CREATE_TABLE)
            for stmt in CREATE_INDEXES:
                conn.execute(stmt)
            conn.executemany(UPSERT, rows)
        total = conn.execute("SELECT COUNT(*) FROM job_postings").fetchone()[0]
    except sqlite3.Error:
        logger.exception("Load failed, transaction rolled back")
        raise
    finally:
        conn.close()

    logger.info("Load finished: table now has %d rows", total)
    return total