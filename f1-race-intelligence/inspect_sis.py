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
    database=os.getenv("SNOWFLAKE_DATABASE", "F1_PREDICTION_DB"),
    schema="ANALYTICS"
)
cs = ctx.cursor()

print("--- DESCRIBE STREAMLIT ---")
try:
    cs.execute("DESCRIBE STREAMLIT F1_RACE_INTELLIGENCE;")
    for row in cs.fetchall():
        print(row)
except Exception as e:
    print("Error describing streamlit:", e)

print("\n--- LIST @F1_STREAMLIT_STAGE ---")
try:
    cs.execute("LIST @F1_STREAMLIT_STAGE;")
    for row in cs.fetchall():
        print(row)
except Exception as e:
    print("Error listing @F1_STREAMLIT_STAGE:", e)

print("\n--- SHOW STAGES IN SCHEMA ANALYTICS ---")
try:
    cs.execute("SHOW STAGES;")
    for row in cs.fetchall():
        print(row[1]) # stage name
except Exception as e:
    print("Error showing stages:", e)

cs.close()
ctx.close()
