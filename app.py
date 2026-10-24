import os

import pandas as pd
import snowflake.connector
import streamlit as st

st.title("Logistics Orders Dashboard")


@st.cache_data(ttl=300)
def run_query(sql):
    # credentials come from environment variables, same as ingest_snowflake.py
    conn = snowflake.connector.connect(
        account=os.environ["SF_ACCOUNT"],
        user=os.environ["SF_USER"],
        password=os.environ["SF_PASSWORD"],
        warehouse="LOGI_WH",
    )
    cur = conn.cursor()
    cur.execute(sql)
    df = pd.DataFrame(cur.fetchall(), columns=[c[0].lower() for c in cur.description])
    conn.close()
    return df


# top numbers
counts = run_query("""
    SELECT (SELECT COUNT(*) FROM LOGISTICS_DB.CLEAN.CLEAN_ORDERS)    AS good,
           (SELECT COUNT(*) FROM LOGISTICS_DB.CLEAN.REJECTED_ORDERS) AS bad
""")
col1, col2 = st.columns(2)
col1.metric("Clean orders", int(counts.good[0]))
col2.metric("Rejected orders", int(counts.bad[0]))

# clean orders by status
st.subheader("Clean orders by status")
by_status = run_query("""
    SELECT order_status, COUNT(*) AS orders
    FROM LOGISTICS_DB.CLEAN.CLEAN_ORDERS
    GROUP BY order_status
""")
st.bar_chart(by_status.set_index("order_status"))

# clean orders by warehouse region
st.subheader("Clean orders by region")
by_region = run_query("""
    SELECT warehouse_region, COUNT(*) AS orders, SUM(TRY_TO_NUMBER(order_amount)) AS revenue
    FROM LOGISTICS_DB.CLEAN.CLEAN_ORDERS
    GROUP BY warehouse_region
""")
st.dataframe(by_region)

# why orders were rejected
st.subheader("Rejected orders by reason")
rejected = run_query("""
    SELECT order_id, customer_id, order_status, order_amount,
           CASE
               WHEN order_status NOT IN ('PLACED','PACKED','SHIPPED','DELIVERED','CANCELLED') THEN 'Invalid status'
               WHEN customer_id NOT IN (SELECT customer_id FROM LOGISTICS_DB.RAW.RAW_CUSTOMERS) THEN 'Unknown customer'
               ELSE 'Zero or negative amount'
           END AS reason
    FROM LOGISTICS_DB.CLEAN.REJECTED_ORDERS
""")
st.bar_chart(rejected.groupby("reason").size())
st.dataframe(rejected)
