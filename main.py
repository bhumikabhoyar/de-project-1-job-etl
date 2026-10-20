import logging

from src.extract import extract_csv
from src.transform import transform
from src.load import load_to_sqlite
from src.logger import setup_logging

RAW_PATH = "data/raw/job_postings_raw.csv"
CLEAN_PATH = "data/processed/job_postings_clean.csv"
DB_PATH = "data/jobs.db"

logger = logging.getLogger("pipeline")


def main():
    setup_logging()
    logger.info("Pipeline started")
    raw = extract_csv(RAW_PATH)
    clean = transform(raw)
    clean.to_csv(CLEAN_PATH, index=False)
    total = load_to_sqlite(clean, DB_PATH)
    logger.info("Pipeline finished: %d rows in database", total)


if __name__ == "__main__":
    main()