import sqlite3

conn = sqlite3.connect("data/jobs.db")
for row in conn.execute("SELECT * FROM pipeline_runs ORDER BY run_id DESC"):
    print(row)
print("jobs table rows:", conn.execute("SELECT COUNT(*) FROM job_postings").fetchone()[0])
conn.close()