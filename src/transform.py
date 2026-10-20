import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

SKILL_MAP = {s.lower(): s for s in [
    "Python", "SQL", "Excel", "Power BI", "Tableau", "Pandas", "Spark",
    "Airflow", "AWS", "Docker", "Git", "PostgreSQL",
]}
WORD_FIXES = {"Bi": "BI", "Etl": "ETL"}
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"]
NAN = float("nan")


# ---------- small cleaning functions ----------

def clean_title(value):
    if pd.isna(value):
        return None
    text = value.strip().lower().replace("jr.", "junior").replace("sr.", "senior")
    words = [w.capitalize() for w in text.split()]
    return " ".join(WORD_FIXES.get(w, w) for w in words)


def clean_location(value):
    if pd.isna(value):
        return None
    text = re.sub(r",\s*mh$", "", value.strip().lower())
    if text == "bangalore":
        text = "bengaluru"
    return text.title()


def parse_salary(value):
    """Return (min_lpa, max_lpa). Annual salary in lakhs per annum."""
    if pd.isna(value):
        return NAN, NAN
    text = value.lower().replace(",", "")
    nums = [float(n) for n in re.findall(r"\d+\.?\d*", text)]
    if not nums:                       # "N/A", "negotiable"
        return NAN, NAN
    if "lpa" in text:
        low, high = nums[0], nums[-1]
    elif "month" in text:
        low = high = nums[0] * 12 / 100_000
    else:                              # plain annual rupees
        low = high = nums[0] / 100_000
    return round(low, 2), round(high, 2)


def parse_experience(value):
    """Return (min_years, max_years). '5+' has no upper bound."""
    if pd.isna(value):
        return NAN, NAN
    text = value.lower()
    if "fresher" in text:
        return 0.0, 0.0
    nums = [float(n) for n in re.findall(r"\d+", text)]
    if not nums:
        return NAN, NAN
    if "+" in text:
        return nums[0], NAN
    return nums[0], nums[-1]


def clean_skills(value):
    if pd.isna(value):
        return None
    parts = [p.strip().lower() for p in re.split(r"[,;|]", value) if p.strip()]
    skills = {SKILL_MAP.get(p, p.title()) for p in parts}
    return ", ".join(sorted(skills))


def clean_job_type(value):
    if pd.isna(value):
        return "Unknown"
    text = value.strip().lower().replace("-", " ")
    return {"full time": "Full-time", "internship": "Internship",
            "contract": "Contract"}.get(text, "Unknown")


def parse_dates(series: pd.Series) -> pd.Series:
    """Try each known format; anything unparseable becomes NaT."""
    result = pd.to_datetime(series, format=DATE_FORMATS[0], errors="coerce")
    for fmt in DATE_FORMATS[1:]:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        result = result.fillna(parsed)
    return result


# ---------- main transform ----------

def transform(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transform started: %d rows", len(df))
    df = df.copy()

    before = len(df)
    df = df.drop_duplicates(subset="job_id", keep="first")
    logger.info("Removed %d duplicate rows", before - len(df))

    df["job_title"] = df["job_title"].map(clean_title)
    df["company"] = df["company"].str.strip().fillna("Unknown")
    df["location"] = df["location"].map(clean_location)
    df["job_type"] = df["job_type"].map(clean_job_type)
    df["skills"] = df["skills"].map(clean_skills)

    salary = pd.DataFrame(df["salary"].map(parse_salary).tolist(),
                          index=df.index, columns=["salary_min_lpa", "salary_max_lpa"])
    exp = pd.DataFrame(df["experience"].map(parse_experience).tolist(),
                       index=df.index, columns=["exp_min_years", "exp_max_years"])
    df = pd.concat([df.drop(columns=["salary", "experience"]), salary, exp], axis=1)

    dates = parse_dates(df["posted_date"])
    bad = df["posted_date"].notna() & dates.isna()
    if bad.any():
        logger.warning("%d dates could not be parsed", bad.sum())
    df["posted_date"] = dates.dt.strftime("%Y-%m-%d")

    # Data-quality checks: fail loudly if something is wrong
    assert df["job_id"].is_unique, "job_id must be unique"
    assert df["job_title"].notna().all(), "job_title must not be empty"

    logger.info("Transform finished: %d rows", len(df))
    return df.reset_index(drop=True)