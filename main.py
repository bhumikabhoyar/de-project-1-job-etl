from src.extract import extract_csv
from src.transform import transform
from src.logger import setup_logging

RAW_PATH = "data/raw/job_postings_raw.csv"
CLEAN_PATH = "data/processed/job_postings_clean.csv"


def main():
    setup_logging()
    raw = extract_csv(RAW_PATH)
    clean = transform(raw)
    clean.to_csv(CLEAN_PATH, index=False)
    print(clean.head(10).to_string())
    print()
    print(clean.isna().sum())


if __name__ == "__main__":
    main()