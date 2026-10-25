import os
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv
import snowflake.connector

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

print("[*] Connecting to Snowflake...", flush=True)
ctx = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "F1_WH"),
    database=os.getenv("SNOWFLAKE_DATABASE", "F1_PREDICTION_DB"),
    schema="ANALYTICS"
)
cs = ctx.cursor()

root_dir = os.path.dirname(os.path.abspath(__file__))
staging_dir = os.path.join(root_dir, "staging_upload")

print("=" * 70, flush=True)
print("  🚀 DEPLOYING STREAMLIT IN SNOWFLAKE (SiS) FILES TO STAGE", flush=True)
print("=" * 70, flush=True)

total_uploaded = 0
for root, dirs, files in os.walk(staging_dir):
    rel_dir = os.path.relpath(root, staging_dir)
    if rel_dir == ".":
        stage_target = "@F1_PREDICTION_DB.ANALYTICS.F1_STREAMLIT_STAGE"
        display_prefix = ""
    else:
        norm_sub = rel_dir.replace("\\", "/")
        stage_target = f"@F1_PREDICTION_DB.ANALYTICS.F1_STREAMLIT_STAGE/{norm_sub}"
        display_prefix = f"{norm_sub}/"
    
    for f in files:
        full_path = os.path.join(root, f).replace("\\", "/")
        size_kb = os.path.getsize(full_path) / 1024
        
        print(f"[*] Uploading {display_prefix}{f} ({size_kb:.1f} KB) -> {stage_target}...", flush=True)
        put_sql = f"PUT file://{full_path} {stage_target} AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
        try:
            cs.execute(put_sql)
            res = cs.fetchone()
            status = res[4] if res and len(res) > 4 else "UPLOADED"
            print(f"    [+] Status: {status}", flush=True)
            total_uploaded += 1
        except Exception as e:
            print(f"    [-] Error uploading {f}: {e}", flush=True)

print(f"\n[✓] Successfully uploaded {total_uploaded} files to @F1_STREAMLIT_STAGE!", flush=True)

print("\n--- Summary of Objects in @F1_STREAMLIT_STAGE ---", flush=True)
cs.execute("LIST @F1_PREDICTION_DB.ANALYTICS.F1_STREAMLIT_STAGE;")
rows = cs.fetchall()
print(f"Total objects in stage: {len(rows)}", flush=True)
for r in rows:
    print(f"  - {r[0]:<65} ({r[1]:>8} bytes)", flush=True)

cs.close()
ctx.close()
print("\n[✓] All Snowflake SiS stage deployments completed successfully!", flush=True)
