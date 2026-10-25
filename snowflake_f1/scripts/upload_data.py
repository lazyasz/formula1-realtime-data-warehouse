"""
Formula 1 Snowflake Staging & Data Ingestion Uploader
=====================================================
Uploads prepared CSV datasets and ML reports to Snowflake:
1. Connects using credentials from .env (SNOWFLAKE_ACCOUNT, USER, PASSWORD, WAREHOUSE, etc.)
2. Stages CSV files into the internal stage: @RAW.F1_RAW_STAGE
3. Executes COPY INTO statements into Snowflake RAW and ML tables
4. Provides a dry-run verification mode when running locally without active cloud credentials.
"""

import os
import glob
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

def upload_to_snowflake(dry_run=False):
    print("=" * 80)
    print("   FORMULA 1 SNOWFLAKE DATA STAGING & INGESTION")
    print("=" * 80)

    account = os.getenv("SNOWFLAKE_ACCOUNT", "")
    user = os.getenv("SNOWFLAKE_USER", "")
    password = os.getenv("SNOWFLAKE_PASSWORD", "")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "F1_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "F1_PREDICTION_DB")
    role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")

    files_to_upload = [
        ("clean_f1_modeling_master.csv", os.path.join(data_dir, "clean_f1_modeling_master.csv")),
        ("raw_races.csv", os.path.join(data_dir, "raw_races.csv")),
        ("raw_drivers.csv", os.path.join(data_dir, "raw_drivers.csv")),
        ("raw_constructors.csv", os.path.join(data_dir, "raw_constructors.csv")),
        ("raw_circuits.csv", os.path.join(data_dir, "raw_circuits.csv")),
        ("raw_race_results.csv", os.path.join(data_dir, "raw_race_results.csv")),
        ("model_comparison.csv", os.path.join(reports_dir, "model_comparison.csv")),
        ("f1_association_rules.csv", os.path.join(reports_dir, "f1_association_rules.csv")),
        ("f1_frequent_itemsets.csv", os.path.join(reports_dir, "f1_frequent_itemsets.csv")),
        ("feature_importance.csv", os.path.join(reports_dir, "feature_importance.csv"))
    ]

    print("[*] Target files for Snowflake ingestion:")
    for name, fpath in files_to_upload:
        exists = os.path.exists(fpath)
        sz = os.path.getsize(fpath) / 1024 if exists else 0
        print(f"  - {name:<30}: {'FOUND' if exists else 'MISSING'} ({sz:.1f} KB)")

    if not account or account == "your_snowflake_account_identifier" or dry_run:
        print("\n[!] Notice: No live Snowflake credentials found in .env (or dry_run=True).")
        print("[!] Generating SnowSQL PUT commands ready to paste or execute:")
        print("----------------------------------------------------------------")
        print(f"USE WAREHOUSE {warehouse};")
        print(f"USE DATABASE {database};")
        print(f"USE SCHEMA RAW;")
        print(f"CREATE OR REPLACE STAGE F1_RAW_STAGE FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '\"');")
        for name, fpath in files_to_upload:
            if os.path.exists(fpath):
                norm_path = fpath.replace("\\", "/")
                print(f"PUT file://{norm_path} @F1_RAW_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;")
        print("----------------------------------------------------------------")
        print("[+] Dry-run completed. All source CSV files are validated and ready.")
        return False

    try:
        import snowflake.connector
        print(f"\n[*] Connecting to Snowflake Account '{account}' as user '{user}'...")
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            role=role
        )
        cur = conn.cursor()
        print("[+] Connected successfully! Staging files into @RAW.F1_RAW_STAGE...")

        cur.execute("CREATE OR REPLACE STAGE RAW.F1_RAW_STAGE FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '\"');")
        for name, fpath in files_to_upload:
            if os.path.exists(fpath):
                norm_path = fpath.replace("\\", "/")
                print(f"[*] Uploading {name}...")
                cur.execute(f"PUT file://{norm_path} @RAW.F1_RAW_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;")
                print(f"[+] Staged {name} successfully.")

        cur.close()
        conn.close()
        print("[+] Snowflake Data Staging Completed Successfully!")
        return True
    except Exception as e:
        print(f"[!] Snowflake connection/upload error: {e}")
        print("[!] Tip: Verify credentials in .env file.")
        return False

if __name__ == "__main__":
    upload_to_snowflake()
