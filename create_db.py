import pandas as pd
from datasets import load_dataset
import sqlite3
import os

print("Downloading dataset from Hugging Face...")
# Load the dataset
ds = load_dataset('lukebarousse/data_jobs', split='train')

print(f"Dataset loaded with {len(ds)} rows.")
print("Converting to pandas DataFrame (taking a sample of 50,000 rows for speed)...")

# Take a sample to keep the SQLite database small and queries fast
# Explicitly typing df as pd.DataFrame to satisfy Pylance
df: pd.DataFrame = ds.select(range(50000)).to_pandas() # type: ignore

# Clean up column names just in case
df.columns = [c.replace(' ', '_').lower() for c in df.columns]

# Ensure date columns are strings (SQLite doesn't have a native datetime type)
if 'job_posted_date' in df.columns:
    df['job_posted_date'] = df['job_posted_date'].astype(str)

db_path = "data_jobs.sqlite"
if os.path.exists(db_path):
    os.remove(db_path)

print(f"Saving to SQLite database: {db_path}...")
conn = sqlite3.connect(db_path)
df.to_sql('job_postings', conn, index=False, if_exists='replace')

# Create some basic indexes to make SQL queries faster
print("Creating indexes...")
cursor = conn.cursor()
cursor.execute('CREATE INDEX idx_job_title ON job_postings(job_title_short)')
cursor.execute('CREATE INDEX idx_country ON job_postings(job_country)')
cursor.execute('CREATE INDEX idx_salary ON job_postings(salary_year_avg)')
conn.commit()
conn.close()

print(f"Database created successfully at {db_path}!")
print("Columns in 'job_postings' table:")
print(df.columns.tolist())
