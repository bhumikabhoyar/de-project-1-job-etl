import logging
import sys
from src.ai_report import generate_report
from pathlib import Path


from src.extract import extract_csv
from src.transform import transform
from src.validate import validate
from src.load import load_to_sqlite
from src.run_tracker import RunTracker
from src.logger import setup_logging

RAW_PATH = "data/raw/job_postings_raw.csv"
CLEAN_PATH = "data/processed/job_postings_clean.csv"
REJECT_PATH = "data/rejected/job_postings_rejected.csv"
DB_PATH = "data/jobs.db"

logger = logging.getLogger("pipeline")


def main():
    setup_logging()
    logger.info("Pipeline started")
    tracker = RunTracker(DB_PATH)
    try:
        raw = extract_csv(RAW_PATH)
        tracker.stats["rows_extracted"] = len(raw)
        tracker.stats["duplicates_removed"] = int(raw["job_id"].duplicated().sum())

        clean = transform(raw)
        valid, rejected = validate(clean)
        tracker.stats["rows_rejected"] = len(rejected)

        if not rejected.empty:
            Path(REJECT_PATH).parent.mkdir(parents=True, exist_ok=True)
            rejected.to_csv(REJECT_PATH, index=False)
            logger.warning("Saved %d rejected rows to %s", len(rejected), REJECT_PATH)

        valid.to_csv(CLEAN_PATH, index=False)
        load_to_sqlite(valid, DB_PATH)
        tracker.stats["rows_loaded"] = len(valid)

        try:
            generate_report(valid, rejected, tracker.stats)
        except Exception:
            logger.exception("Report generation failed (pipeline continues)")

        tracker.finish("SUCCESS")
        logger.info("Pipeline finished successfully")
    except Exception as exc:
        logger.exception("Pipeline failed")
        tracker.finish("FAILED", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()