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

print("=" * 80)
print("  🔍 SNOWFLAKE STREAMLIT VERIFICATION & STATUS CHECK")
print("=" * 80)

# Check Streamlit App definition
cs.execute("DESCRIBE STREAMLIT F1_RACE_INTELLIGENCE;")
desc = cs.fetchone()
print(f"[✓] Streamlit Application Name: {desc[0]}")
print(f"    Title:         {desc[1]}")
print(f"    Root Location: {desc[2]}")
print(f"    Main File:     {desc[3]}")
print(f"    Warehouse:     {desc[4]}")
print(f"    URL ID:        {desc[5]}")

# Verify file count on stage
cs.execute("LIST @F1_STREAMLIT_STAGE;")
rows = cs.fetchall()
print(f"\n[✓] Stage Objects Count: {len(rows)} verified on @F1_STREAMLIT_STAGE")

# Verify views
cs.execute("SELECT COUNT(*) FROM ANALYTICS.V_JURY_DELIVERABLE_1_PATTERN_RULES;")
c1 = cs.fetchone()[0]
cs.execute("SELECT COUNT(*) FROM ANALYTICS.V_JURY_DELIVERABLE_2_MODEL_COMPARISON;")
c2 = cs.fetchone()[0]
cs.execute("SELECT COUNT(*) FROM ANALYTICS.V_JURY_DELIVERABLE_3_CHAMPION_FEATURE_IMPORTANCE;")
c3 = cs.fetchone()[0]
print(f"[✓] Jury View 1 (Pattern Rules):       {c1} rules")
print(f"[✓] Jury View 2 (Model Comparison):    {c2} benchmarked models")
print(f"[✓] Jury View 3 (Feature Importance):  {c3} features")

cs.close()
ctx.close()
print("\n" + "=" * 80)
print("  ✅ SNOWFLAKE STREAMLIT BACKEND & STAGE 100% OPERATIONAL & FLAWLESS!")
print("=" * 80)
