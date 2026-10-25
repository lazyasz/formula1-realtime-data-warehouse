"""
===============================================================================
SNOWPARK PYTHON STORED PROCEDURE / NOTEBOOK: F1 WINNER PREDICTION PIPELINE
===============================================================================
Project: Formula 1 Race Winner Prediction (Data Warehousing & Data Mining)
Environment: Snowflake Snowpark Python (Snowflake Notebook or Stored Procedure)
Packages Required: xgboost, scikit-learn, pandas, numpy, snowflake-snowpark-python
===============================================================================
"""

import numpy as np
import pandas as pd
from snowflake.snowpark import Session
from xgboost import XGBClassifier

# 1. CORE PREDICTIVE FEATURE VECTOR (CAR, LAP, PIT & CONTEXT)
FEATS = [
    'GRID',
    'QUALI_GAP_PCT',
    'CIRCUIT_LAP_RECORD_MS',
    'TEAM_POINTS_L5',
    'TEAM_DNF_RATE_L10',
    'TEAM_QUALI_GAP_L5',
    'TEAM_AVG_PIT_MS',
    'DRIVER_WIN_RATE_L10',
    'DRIVER_POINTS_L5',
    'DRIVER_CIRCUIT_WINS',
    'REG_ERA'
]

# 2. INNOVATION 3: GROUP-WISE RACE SOFTMAX CALIBRATION
def race_softmax(df: pd.DataFrame, score_col: str, group_col: str = 'RACEID') -> pd.Series:
    """
    Normalizes raw logit outputs across each starting grid so that exactly
    one winner is mathematically picked (sum of probabilities = 100% per race).
    """
    # Numerically stable softmax using max subtraction per group
    max_scores = df.groupby(group_col)[score_col].transform('max')
    exp_scores = np.exp(df[score_col] - max_scores)
    sum_exp = exp_scores.groupby(df[group_col]).transform('sum')
    return exp_scores / sum_exp

# 3. MAIN SNOWPARK EXECUTION PROCEDURE
def run(session: Session) -> str:
    print("[*] Starting Snowpark F1 Race Winner Prediction Training Procedure...")

    # Load datasets from Snowflake ANALYTICS schema
    tr_df = session.table('F1_DM.ANALYTICS.FEATURES_TRAIN').to_pandas()
    te_df = session.table('F1_DM.ANALYTICS.FEATURES_TEST').to_pandas()
    
    # Check for 2026 manual input overrides
    try:
        in2026_df = session.table('F1_DM.ANALYTICS.INPUT_2026').to_pandas()
    except Exception:
        in2026_df = pd.DataFrame()

    print(f"[+] Loaded Train records: {len(tr_df):,} | Test records: {len(te_df):,}")

    # Initialize XGBoost with Asymmetric Cost Scaling (scale_pos_weight = 19.0)
    model = XGBClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=19.0,
        eval_metric='logloss',
        random_state=42
    )

    # Train with Recency Sample Weighting (Innovation 2)
    sample_weights = tr_df['SAMPLE_WEIGHT'] if 'SAMPLE_WEIGHT' in tr_df.columns else None
    model.fit(tr_df[FEATS], tr_df['IS_WINNER'], sample_weight=sample_weights)
    print("[+] XGBoost training complete.")

    # Score 2024 Test Set
    raw_probs = model.predict_proba(te_df[FEATS])[:, 1]
    # Logit transform for softmax temperature scaling
    te_df['RAW_LOGIT'] = np.log(np.clip(raw_probs, 1e-9, 1 - 1e-9) / (1 - np.clip(raw_probs, 1e-9, 1 - 1e-9)))
    te_df['WIN_PROB'] = race_softmax(te_df, score_col='RAW_LOGIT', group_col='RACEID')
    te_df['PREDICTED_RANK'] = te_df.groupby('RACEID')['WIN_PROB'].rank(ascending=False, method='first').astype(int)

    # Format 2024 Predictions for PREDICTIONS table
    preds_2024 = pd.DataFrame({
        'RACE_NAME': te_df.get('RACE_NAME', te_df['RACEID'].astype(str)),
        'YEAR': te_df['YEAR'].astype(int),
        'SPLIT': 'TEST_2024',
        'DRIVERID': te_df['DRIVERID'].astype(int),
        'CONSTRUCTORID': te_df['CONSTRUCTORID'].astype(int),
        'WIN_PROB': te_df['WIN_PROB'].round(4),
        'PREDICTED_RANK': te_df['PREDICTED_RANK']
    })

    # Score 2026 Simulation Entries (if present)
    preds_all = [preds_2024]
    if not in2026_df.empty:
        # Synthetic Race ID for grouping
        in2026_df['RACEID'] = 202601
        in2026_raw = model.predict_proba(in2026_df[FEATS])[:, 1]
        in2026_df['RAW_LOGIT'] = np.log(np.clip(in2026_raw, 1e-9, 1 - 1e-9) / (1 - np.clip(in2026_raw, 1e-9, 1 - 1e-9)))
        in2026_df['WIN_PROB'] = race_softmax(in2026_df, score_col='RAW_LOGIT', group_col='RACEID')
        in2026_df['PREDICTED_RANK'] = in2026_df.groupby('RACEID')['WIN_PROB'].rank(ascending=False, method='first').astype(int)

        preds_2026 = pd.DataFrame({
            'RACE_NAME': in2026_df['RACE_NAME'],
            'YEAR': 2026,
            'SPLIT': 'PREDICT_2026',
            'DRIVERID': in2026_df['DRIVERID'].astype(int),
            'CONSTRUCTORID': in2026_df['CONSTRUCTORID'].astype(int),
            'WIN_PROB': in2026_df['WIN_PROB'].round(4),
            'PREDICTED_RANK': in2026_df['PREDICTED_RANK']
        })
        preds_all.append(preds_2026)

    # Write back to Snowflake ANALYTICS.PREDICTIONS table
    final_preds = pd.concat(preds_all, ignore_index=True)
    session.write_pandas(
        final_preds, 
        table_name='PREDICTIONS', 
        schema='ANALYTICS', 
        database='F1_DM',
        auto_create_table=False, 
        overwrite=True
    )
    print(f"[+] Successfully wrote {len(final_preds):,} predictions to F1_DM.ANALYTICS.PREDICTIONS.")

    return f"Training & Inference Successfully Executed. Total Predictions Written: {len(final_preds)}"

# -----------------------------------------------------------------------------
# REGISTRATION SNIPPET (To register as Snowflake Stored Procedure in SnowSQL):
# -----------------------------------------------------------------------------
# CREATE OR REPLACE PROCEDURE F1_DM.ANALYTICS.SP_TRAIN_AND_PREDICT_F1()
# RETURNS STRING
# LANGUAGE PYTHON
# RUNTIME_VERSION = '3.10'
# PACKAGES = ('xgboost', 'scikit-learn', 'pandas', 'numpy', 'snowflake-snowpark-python')
# HANDLER = 'run'
# AS $$
# ... [paste code above] ...
# $$;
