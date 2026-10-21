import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = "claude-haiku-5-5"
REPORT_PATH = "reports/dq_report.md"


def build_stats(valid: pd.DataFrame, rejected: pd.DataFrame, run_stats: dict) -> dict:
    """Aggregated numbers only: no raw rows are sent to the LLM."""
    null_pct = (valid.isna().mean() * 100).round(1)
    return {
        "run": run_stats,
        "null_percent_by_column": {c: v for c, v in null_pct.items() if v > 0},
        "reject_reasons": rejected["reject_reason"].value_counts().to_dict()
        if not rejected.empty else {},
        "top_locations": valid["location"].value_counts().head(5).to_dict(),
        "job_type_counts": valid["job_type"].value_counts().to_dict(),
        "company_unknown_count": int((valid["company"] == "Unknown").sum()),
    }


def _fallback_report(stats: dict) -> str:
    run = stats["run"]
    lines = [
        "## Data quality summary (template)",
        f"- Extracted {run.get('rows_extracted')} rows; removed "
        f"{run.get('duplicates_removed')} duplicates; rejected {run.get('rows_rejected')}; "
        f"loaded {run.get('rows_loaded')}.",
        f"- Reject reasons: {stats['reject_reasons'] or 'none'}",
        f"- Columns with missing values (%): {stats['null_percent_by_column'] or 'none'}",
    ]
    return "\n".join(lines)


def _llm_report(stats: dict) -> str:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    prompt = (
        "You are a data engineer reviewing the latest run of a job-postings ETL "
        "pipeline. Using ONLY the statistics below, write a short markdown report "
        "with: (1) a 2-sentence overall summary, (2) the main data-quality issues, "
        "(3) 2-3 concrete recommendations. Do not invent numbers or facts that are "
        "not in the stats.\n\n"
        f"STATS:\n{json.dumps(stats, indent=2, default=str)}"
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def generate_report(valid, rejected, run_stats) -> str:
    stats = build_stats(valid, rejected, run_stats)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            body = _llm_report(stats)
            source = f"AI-generated ({MODEL})"
        except Exception:
            logger.exception("LLM report failed, using template instead")
            body, source = _fallback_report(stats), "template (LLM failed)"
    else:
        logger.warning("ANTHROPIC_API_KEY not set, using template report")
        body, source = _fallback_report(stats), "template"

    report = f"# Data Quality Report\n_Generated {datetime.now():%Y-%m-%d %H:%M} | {source}_\n\n{body}\n"
    Path(REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(REPORT_PATH).write_text(report, encoding="utf-8")
    logger.info("Report saved to %s", REPORT_PATH)
    return report