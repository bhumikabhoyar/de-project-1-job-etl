import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)
N_ROWS = 500

titles = ["Data Analyst", "data analyst", "DATA ANALYST", "Data Engineer",
          "Jr. Data Engineer", "Senior Data Analyst", "BI Developer",
          "Python Developer", "ETL Developer", "Business Analyst",
          "Machine Learning Engineer"]
companies = ["Infosys", "TCS", "Wipro", "Persistent Systems", "Zensar",
             "Cognizant", "Capgemini", "Tech Mahindra", "Accenture",
             "DataNova Pvt Ltd", "Startup Labs"]
locations = ["Pune", "pune", "PUNE", "Pune, MH", "Pune ", "Mumbai", "mumbai",
             "Nagpur", "Bengaluru", "Bangalore", "Hyderabad", "Remote"]
salaries = ["6-8 LPA", "8 LPA", "INR 600000", "6,00,000", "12-15 LPA",
            "50000/month", "N/A", "", "negotiable", "4.5 LPA", "20 LPA"]
experiences = ["0-1 years", "2-4 yrs", "Fresher", "5+ years", "3 years",
               "1-3 Years", "", "6-10 yrs"]
skills_pool = ["Python", "SQL", "Excel", "Power BI", "Tableau", "Pandas",
               "Spark", "Airflow", "AWS", "Docker", "Git", "PostgreSQL"]
job_types = ["Full-time", "full time", "Internship", "Contract", "FULL-TIME", ""]
date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"]


def random_date():
    d = datetime(2026, 10, 1) - timedelta(days=random.randint(0, 90))
    return d.strftime(random.choice(date_formats)) if random.random() > 0.05 else ""


def random_skills():
    chosen = random.sample(skills_pool, random.randint(2, 5))
    sep = random.choice([", ", "|", ";", ","])
    text = sep.join(chosen)
    return text.lower() if random.random() < 0.2 else text


rows = []
for i in range(1, N_ROWS + 1):
    rows.append({
        "job_id": f"JOB-{i:04d}",
        "job_title": random.choice(titles),
        "company": random.choice(companies) if random.random() > 0.04 else None,
        "location": random.choice(locations),
        "salary": random.choice(salaries),
        "experience": random.choice(experiences),
        "skills": random_skills(),
        "posted_date": random_date(),
        "job_type": random.choice(job_types),
    })

df = pd.DataFrame(rows)

# Add ~25 duplicate rows
duplicates = df.sample(25, random_state=1)
df = pd.concat([df, duplicates], ignore_index=True).sample(frac=1, random_state=7)

out = Path("data/raw/job_postings_raw.csv")
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False, encoding="utf-8")
print(f"Saved {len(df)} rows to {out}")