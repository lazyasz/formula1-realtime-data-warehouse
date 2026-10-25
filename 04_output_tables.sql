-- ============================================================================
-- 04_OUTPUT_TABLES.SQL: 2026 INPUT OVERRIDES, PREDICTIONS & METRIC SINKS
-- ============================================================================
-- Project: Formula 1 Race Winner Prediction (Data Warehousing & Data Mining)
-- Schema: F1_DM.ANALYTICS
-- ============================================================================

USE DATABASE F1_DM;
USE SCHEMA F1_DM.ANALYTICS;
USE WAREHOUSE F1_WH;

-- 1. INPUT_2026: SIMULATED ENTRY TABLE FOR 2026 REGULATION ERA
-- Accommodates manual grid inputs, test form, and regulatory override flags
CREATE OR REPLACE TABLE INPUT_2026 (
    race_name STRING NOT NULL,
    circuitId INT NOT NULL,
    driverId INT NOT NULL,
    constructorId INT NOT NULL,
    grid INT NOT NULL,
    quali_gap_pct FLOAT NOT NULL,
    team_points_l5 FLOAT NOT NULL,
    team_dnf_rate_l10 FLOAT NOT NULL,
    team_quali_gap_l5 FLOAT NOT NULL,
    team_avg_pit_ms FLOAT NOT NULL,
    driver_win_rate_l10 FLOAT NOT NULL,
    driver_points_l5 FLOAT NOT NULL,
    driver_circuit_wins INT NOT NULL,
    circuit_lap_record_ms FLOAT NOT NULL,
    reg_era INT DEFAULT 5
);

-- 2. PREDICTIONS: PRODUCTION INFERENCE TABLE
CREATE OR REPLACE TABLE PREDICTIONS (
    run_ts TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    race_name STRING NOT NULL,
    year INT NOT NULL,
    split STRING NOT NULL, -- 'TEST_2024' or 'PREDICT_2026'
    driverId INT NOT NULL,
    constructorId INT NOT NULL,
    win_prob FLOAT NOT NULL,
    predicted_rank INT NOT NULL
);

-- 3. MODEL_METRICS: BENCHMARK EVALUATION RESULTS TABLE
CREATE OR REPLACE TABLE MODEL_METRICS (
    run_ts TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    model STRING NOT NULL,
    split STRING NOT NULL,
    accuracy FLOAT NOT NULL,
    precision_w FLOAT NOT NULL,
    recall_w FLOAT NOT NULL,
    f1_w FLOAT NOT NULL,
    roc_auc FLOAT NOT NULL,
    pr_auc FLOAT NOT NULL,
    top1_race_acc FLOAT NOT NULL,
    top3_hit FLOAT NOT NULL,
    log_loss FLOAT NOT NULL,
    brier FLOAT NOT NULL
);

-- 4. ASSOC_RULES: FREQUENT PATTERN MINING OUTPUTS TABLE
CREATE OR REPLACE TABLE ASSOC_RULES (
    algo STRING NOT NULL, -- 'Apriori' or 'FP-Growth'
    antecedents STRING NOT NULL,
    consequents STRING NOT NULL,
    support FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    lift FLOAT NOT NULL,
    runtime_s FLOAT NOT NULL,
    n_itemsets INT NOT NULL
);

-- Audit table existence
SHOW TABLES LIKE '%2026%' IN SCHEMA F1_DM.ANALYTICS;
SHOW TABLES LIKE '%METRICS%' IN SCHEMA F1_DM.ANALYTICS;
SHOW TABLES LIKE '%RULES%' IN SCHEMA F1_DM.ANALYTICS;
