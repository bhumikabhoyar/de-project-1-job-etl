import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Each rule returns True for rows that FAIL it
RULES = {
    "missing_posted_date": lambda d: d["posted_date"].isna(),
    "salary_min_gt_max": lambda d: d["salary_min_lpa"] > d["salary_max_lpa"],
    "exp_min_gt_max": lambda d: d["exp_min_years"] > d["exp_max_years"],
    "future_date": lambda d: pd.to_datetime(d["posted_date"], errors="coerce")
    > pd.Timestamp.today(),
}


def validate(df: pd.DataFrame):
    """Split into (valid, rejected). Rejected rows get a reject_reason."""
    reasons = pd.Series("", index=df.index)
    for name, rule in RULES.items():
        failed = rule(df).fillna(False)
        if failed.any():
            logger.warning("Rule '%s' failed for %d rows", name, failed.sum())
        reasons = reasons.where(~failed, reasons + name + ";")

    bad = reasons != ""
    rejected = df[bad].assign(reject_reason=reasons[bad].str.rstrip(";"))
    valid = df[~bad]
    logger.info("Validation: %d valid, %d rejected", len(valid), len(rejected))
    return valid, rejected