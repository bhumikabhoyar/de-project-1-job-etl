import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "job_id", "job_title", "company", "location", "salary",
    "experience", "skills", "posted_date", "job_type",
]


def extract_csv(path: str) -> pd.DataFrame:
    """Read the raw CSV and validate its structure."""
    path = Path(path)
    logger.info("Extract started: %s", path)

    if not path.exists():
        logger.error("File not found: %s", path)
        raise FileNotFoundError(path)

    # Read everything as text. Only truly empty cells become NaN, so values
    # like "N/A" stay visible and we handle them deliberately in Transform.
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])

    if df.empty:
        raise ValueError(f"{path} contains no rows")

    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        logger.error("Missing columns: %s", sorted(missing))
        raise ValueError(f"Missing columns: {sorted(missing)}")

    logger.info("Extracted %d rows, %d columns", *df.shape)
    nulls = df.isna().sum()
    for col, n in nulls[nulls > 0].items():
        logger.warning("Column '%s' has %d empty values", col, n)

    return df