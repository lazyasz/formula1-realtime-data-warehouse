import os
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv
import snowflake.connector

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

ctx = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "F1_WH"),
    database=os.getenv("SNOWFLAKE_DATABASE", "F1_PREDICTION_DB")
)
cs = ctx.cursor()

print("[*] Fetching Streamlits in Snowflake...")
cs.execute("SHOW STREAMLITS IN ACCOUNT;")
cols = [c[0] for c in cs.description]
streamlits = cs.fetchall()
for row in streamlits:
    d = dict(zip(cols, row))
    print(f"Streamlit App: {d.get('name')}")
    print(f"  - Database: {d.get('database_name')}")
    print(f"  - Schema:   {d.get('schema_name')}")
    print(f"  - Title:    {d.get('title')}")
    print(f"  - Location: {d.get('root_location')}")
    print(f"  - Main file:{d.get('main_file')}")
    print(f"  - URL ID:   {d.get('url_id')}\n")

# Also check stages in F1_PREDICTION_DB
print("[*] Checking stages in F1_PREDICTION_DB...")
cs.execute("SHOW STAGES IN DATABASE F1_PREDICTION_DB;")
cols_st = [c[0] for c in cs.description]
for row in cs.fetchall():
    d = dict(zip(cols_st, row))
    print(f"Stage: {d.get('database_name')}.{d.get('schema_name')}.{d.get('name')}")

cs.close()
ctx.close()
