import csv
import os
from datetime import datetime
from pathlib import Path

import snowflake.connector

DATA_DIR = Path("sample_data")

# one batch per run: id for grouping rows, timestamp for audit
loaded_at = datetime.now()
batch_id = loaded_at.strftime("%Y%m%d%H%M%S")

# credentials come from environment variables, never from the code
conn = snowflake.connector.connect(
    account=os.environ["SF_ACCOUNT"],
    user=os.environ["SF_USER"],
    password=os.environ["SF_PASSWORD"],
    warehouse="LOGI_WH",
)
cur = conn.cursor()

# safe to re-run: only creates them if missing
cur.execute("CREATE DATABASE IF NOT EXISTS LOGISTICS_DB")
cur.execute("CREATE SCHEMA IF NOT EXISTS LOGISTICS_DB.RAW")
cur.execute("USE SCHEMA LOGISTICS_DB.RAW")

for file in sorted(DATA_DIR.glob("*.csv")):
    # customers_day1.csv -> raw_customers
    table = "raw_" + file.stem.split("_")[0]

    with open(file, newline="") as f:
        reader = csv.reader(f)
        columns = next(reader)
        rows = [r + [file.name, batch_id, loaded_at.isoformat()] for r in reader]

    # raw layer: everything TEXT, so bad data still loads
    col_defs = ", ".join(f"{c} TEXT" for c in columns)
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_defs}, source_file TEXT, batch_id TEXT, loaded_at TEXT)")

    marks = ", ".join(["%s"] * (len(columns) + 3))
    cur.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)
    print(f"{file.name}: {len(rows)} rows -> {table}")

conn.close()
