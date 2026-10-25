import os
import sys
from dotenv import load_dotenv
import snowflake.connector

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

print("[1] Connecting to Snowflake...", flush=True)
ctx = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse="F1_WH",
    database="F1_PREDICTION_DB",
    schema="ANALYTICS"
)
cs = ctx.cursor()
print("[2] Connected! Testing PUT db_utils.py...", flush=True)

test_file = os.path.abspath("staging_upload/db_utils.py").replace("\\", "/")
print(f"File to upload: {test_file}", flush=True)

sql = f"PUT file://{test_file} @F1_STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
print(f"Executing: {sql}", flush=True)
cs.execute(sql)
print("Result:", cs.fetchall(), flush=True)

cs.close()
ctx.close()
print("[3] Done!", flush=True)
