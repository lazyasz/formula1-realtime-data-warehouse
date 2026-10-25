import os
import sys
from dotenv import load_dotenv
import snowflake.connector

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

ctx = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse="F1_WH",
    database="F1_PREDICTION_DB",
    schema="ANALYTICS"
)
cs = ctx.cursor()

test_file = os.path.abspath("staging_upload/pages/15_Power_BI_Race_Predictor_Dashboard.py").replace("\\", "/")
sql = f"PUT file://{test_file} @F1_STREAMLIT_STAGE/pages AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
print(f"Executing: {sql}", flush=True)
cs.execute(sql)
print("Result:", cs.fetchall(), flush=True)

cs.close()
ctx.close()
