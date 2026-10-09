# Logistics Data Pipeline

A small data engineering project: load logistics CSV files into Snowflake with Python, then clean the orders with SQL.

## What it does
1. **Ingest (Python):** `ingest_snowflake.py` loads every CSV in `sample_data/` into raw Snowflake tables.
   Each row is tagged with `source_file`, `batch_id` and `loaded_at`.
2. **Clean (SQL):** `02_clean_orders.sql` keeps the latest version of each order, then splits the orders into good rows and rejected rows.

## Data
Sample customers, orders and shipments for day 1 and day 2, with deliberate quality problems:
invalid statuses, unknown customers, duplicate orders, zero or negative amounts, and bad shipment dates.

## Flow
```
sample_data/*.csv -> Python -> LOGISTICS_DB.RAW -> SQL -> LOGISTICS_DB.CLEAN
                                (raw_customers,           (latest_orders,
                                 raw_orders,               clean_orders,
                                 raw_shipments)            rejected_orders)
```

## How to run
```powershell
pip install -r requirements.txt
$env:SF_ACCOUNT="your_account"
$env:SF_USER="your_user"
$env:SF_PASSWORD="your_password"
python ingest_snowflake.py
```
Then run `02_clean_orders.sql` in a Snowflake worksheet. Expected result: 40 good orders, 7 rejected.

## Known limits
- Running the script twice loads every file twice (use `batch_id` to tell the loads apart).
- Only orders are cleaned so far; shipments and customer history are not.

## Tools
Python, Snowflake, SQL
