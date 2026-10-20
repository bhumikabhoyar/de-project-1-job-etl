from src.extract import extract_csv
from src.logger import setup_logging

RAW_PATH = "data/raw/job_postings_raw.csv"


def main():
    setup_logging()
    df = extract_csv(RAW_PATH)
    print(df.head())


if __name__ == "__main__":
    main()