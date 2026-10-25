import os
import shutil

root_dir = r"c:\Users\dhruv\.gemini\antigravity-ide\scratch\f1_dw\f1-race-intelligence"
stage_dir = os.path.join(root_dir, "staging_upload")

# 1. Clean/Create directories
for sub in ["", "pages", "data", "models", "reports"]:
    os.makedirs(os.path.join(stage_dir, sub), exist_ok=True)

print("[*] Assembling files for Snowflake SiS stage...")

# Copy db_utils.py and environment.yml
shutil.copy2(os.path.join(root_dir, "logic", "db_utils.py"), os.path.join(stage_dir, "db_utils.py"))
shutil.copy2(os.path.join(root_dir, "logic", "environment.yml"), os.path.join(stage_dir, "environment.yml"))

# Copy all pages from logic/other_pages/
pages_src = os.path.join(root_dir, "logic", "other_pages")
for p in os.listdir(pages_src):
    if p.endswith(".py"):
        shutil.copy2(os.path.join(pages_src, p), os.path.join(stage_dir, "pages", p))

# Copy jury pages with clear prefix
shutil.copy2(os.path.join(root_dir, "jury", "pages", "1_Pattern_Matching.py"), 
             os.path.join(stage_dir, "pages", "01_Jury_Deliverable_1_Pattern_Matching.py"))
shutil.copy2(os.path.join(root_dir, "jury", "pages", "2_Classification_Comparison.py"), 
             os.path.join(stage_dir, "pages", "02_Jury_Deliverable_2_Classification_Comparison.py"))
shutil.copy2(os.path.join(root_dir, "jury", "pages", "3_Model_Classification_and_Performance_Metrics.py"), 
             os.path.join(stage_dir, "pages", "03_Jury_Deliverable_3_Champion_Model.py"))

# Copy data files
data_candidates = [
    os.path.join(root_dir, "logic", "data", "clean_f1_modeling_master.csv"),
    os.path.join(root_dir, "logic", "data", "raw_circuits.csv"),
    os.path.join(root_dir, "logic", "data", "raw_constructors.csv"),
    os.path.join(root_dir, "logic", "data", "raw_drivers.csv"),
    os.path.join(root_dir, "logic", "data", "raw_race_results.csv"),
    os.path.join(root_dir, "logic", "data", "raw_races.csv"),
    os.path.join(root_dir, "logic", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
]
for src in data_candidates:
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(stage_dir, "data", os.path.basename(src)))
        print(f"  + Staged data: {os.path.basename(src)}")

# Copy models
model_candidates = [
    os.path.join(root_dir, "logic", "models", "f1_race_lab_models.joblib"),
    os.path.join(root_dir, "jury", "3_Model_Classification_with_Performance_Metrics", "champion_xgboost_classifier.joblib"),
    os.path.join(root_dir, "logic", "reports", "champion_f1_xgb.joblib"),
    os.path.join(root_dir, "logic", "reports", "champion_regression_model.joblib"),
]
for src in model_candidates:
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(stage_dir, "models", os.path.basename(src)))
        # Also copy to reports for legacy candidate paths
        shutil.copy2(src, os.path.join(stage_dir, "reports", os.path.basename(src)))
        print(f"  + Staged model: {os.path.basename(src)}")

# Copy reports
reports_src = os.path.join(root_dir, "logic", "reports")
for r in os.listdir(reports_src):
    src = os.path.join(reports_src, r)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(stage_dir, "reports", r))
        print(f"  + Staged report: {r}")

# Also copy association_rules.csv if exists (without overwriting f1_association_rules.csv)
ar_src = os.path.join(root_dir, "logic", "04_pattern_mining", "association_rules.csv")
if os.path.exists(ar_src):
    shutil.copy2(ar_src, os.path.join(stage_dir, "reports", "association_rules.csv"))
    print("  + Staged association_rules.csv")

# Copy architecture diagram vector asset
svg_src = os.path.join(root_dir, "logic", "docs", "architecture.svg")
if os.path.exists(svg_src):
    os.makedirs(os.path.join(stage_dir, "docs"), exist_ok=True)
    shutil.copy2(svg_src, os.path.join(stage_dir, "docs", "architecture.svg"))
    shutil.copy2(svg_src, os.path.join(stage_dir, "architecture.svg"))
    print("  + Staged architecture.svg")

print("\n[✓] Staging directory assembled successfully!")
