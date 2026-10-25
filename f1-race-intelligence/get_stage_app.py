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

os.makedirs("downloaded_stage", exist_ok=True)
print("Downloading streamlit_app.py from @F1_STREAMLIT_STAGE...")
cs.execute("GET @F1_STREAMLIT_STAGE/streamlit_app.py file://./downloaded_stage;")
for row in cs.fetchall():
    print(row)

cs.close()
ctx.close()
