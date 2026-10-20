import sqlite3

conn = sqlite3.connect("data/jobs.db")

queries = {
    "Total rows": "SELECT COUNT(*) FROM job_postings",
    "Jobs per location": """
        SELECT location, COUNT(*) AS jobs FROM job_postings
        GROUP BY location ORDER BY jobs DESC""",
    "Avg salary (LPA) by title": """
        SELECT job_title, ROUND(AVG(salary_min_lpa), 1) AS avg_min_lpa, COUNT(*) AS jobs
        FROM job_postings WHERE salary_min_lpa IS NOT NULL
        GROUP BY job_title ORDER BY avg_min_lpa DESC""",
    "Entry-level data jobs in Pune": """
        SELECT job_id, job_title, company, skills FROM job_postings
        WHERE location = 'Pune' AND exp_min_years <= 1
          AND job_title LIKE '%Data%' LIMIT 5""",
}

for name, sql in queries.items():
    print(f"\n--- {name} ---")
    for row in conn.execute(sql):
        print(row)
conn.close()