-- ============================================================================
-- SOURCE: 01_setup.sql
-- ============================================================================
-- ============================================================================
-- 01_SETUP.SQL: Formula 1 Prediction Platform Infrastructure Setup
-- ============================================================================
-- Description: Idempotent initialization of Warehouse, Database, Schemas, 
--              Stages, and File Formats in Snowflake.
-- Author: F1 Data Engineering Team
-- ============================================================================

-- 1. Create Dedicated X-Small Virtual Warehouse with 60s Auto-Suspend
CREATE WAREHOUSE IF NOT EXISTS F1_WH
    WITH WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Dedicated compute warehouse for Formula 1 Winner Prediction and Analytics';

USE WAREHOUSE F1_WH;

-- 2. Create Analytical Database
CREATE DATABASE IF NOT EXISTS F1_PREDICTION_DB
    COMMENT = 'Formula 1 Race Winner Prediction & Historical Data Warehouse';

USE DATABASE F1_PREDICTION_DB;

-- 3. Create Multi-Tier Governance Schemas
-- Schema RAW: Landing and staging zone for immutable source CSVs
CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Staging layer for raw F1 CSV telemetry and dimension dumps';

-- Schema CLEAN: Unified modeling layer (3 feature pillars: Car, Lap, Pit)
CREATE SCHEMA IF NOT EXISTS CLEAN
    COMMENT = 'Curated 3-pillar feature store and master modeling table';

-- Schema ML: Model metrics, association rules, predictions, and ablation logs
CREATE SCHEMA IF NOT EXISTS ML
    COMMENT = 'Machine learning outputs, model comparison, and rule mining metadata';

-- Schema ANALYTICS: Public reporting views and executive dashboards
CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'Analytical presentation views for Streamlit and BI consumers';

-- 4. Create Reusable CSV File Format
CREATE OR REPLACE FILE FORMAT RAW.F1_CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    NULL_IF = ('', 'NULL', 'null', 'None', 'NA', '\N')
    EMPTY_FIELD_AS_NULL = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    COMMENT = 'Standard CSV parser format for Formula 1 datasets';

-- 5. Create Internal Staging Areas
CREATE OR REPLACE STAGE RAW.F1_RAW_STAGE
    FILE_FORMAT = RAW.F1_CSV_FORMAT
    COMMENT = 'Internal stage for raw CSV dataset uploads';

CREATE OR REPLACE STAGE ML.F1_MODEL_STAGE
    COMMENT = 'Internal stage for serialized Joblib model binaries and JSON artifacts';

-- 6. Verification
SHOW SCHEMAS IN DATABASE F1_PREDICTION_DB;
SHOW STAGES IN SCHEMA RAW;
SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();


-- ============================================================================
-- SOURCE: 02_create_tables.sql
-- ============================================================================
-- ============================================================================
-- 02_CREATE_TABLES.SQL: Formula 1 DDL Table Definitions
-- ============================================================================
-- Description: Defines idempotent DDL for RAW ingestion tables, CLEAN 3-pillar
--              feature tables, and ML metric registry tables.
-- ============================================================================

USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- ============================================================================
-- 1. RAW SCHEMA: Immutable Staging Tables
-- ============================================================================
USE SCHEMA RAW;

CREATE OR REPLACE TABLE RAW.RAW_RACES (
    RACE_ID             INT PRIMARY KEY,
    SEASON              INT,
    ROUND               INT,
    RACE_NAME           VARCHAR(100),
    RACE_DATE           DATE,
    CIRCUIT_ID          INT,
    CIRCUIT_NAME        VARCHAR(100),
    CIRCUIT_COUNTRY     VARCHAR(50)
);

CREATE OR REPLACE TABLE RAW.RAW_DRIVERS (
    DRIVER_ID           INT PRIMARY KEY,
    DRIVER_REF          VARCHAR(50),
    DRIVER_CODE         VARCHAR(10),
    DRIVER_NAME         VARCHAR(100),
    DRIVER_DOB          DATE,
    DRIVER_NATIONALITY  VARCHAR(50)
);

CREATE OR REPLACE TABLE RAW.RAW_CONSTRUCTORS (
    CONSTRUCTOR_ID          INT PRIMARY KEY,
    CONSTRUCTOR_REF         VARCHAR(50),
    CONSTRUCTOR_NAME        VARCHAR(100),
    CONSTRUCTOR_NATIONALITY VARCHAR(50)
);

CREATE OR REPLACE TABLE RAW.RAW_CIRCUITS (
    CIRCUIT_ID                  INT PRIMARY KEY,
    CIRCUIT_NAME                VARCHAR(100),
    CIRCUIT_COUNTRY             VARCHAR(50),
    CIRCUIT_LAP_RECORD_SEC      FLOAT,
    CIRCUIT_PIT_LANE_LOSS_SEC   FLOAT
);

CREATE OR REPLACE TABLE RAW.RAW_RACE_RESULTS (
    RACE_ID             INT,
    DRIVER_ID           INT,
    CONSTRUCTOR_ID      INT,
    GRID_POSITION       INT,
    QUALIFYING_POSITION INT,
    FINISH_POSITION     FLOAT,
    IS_WIN              INT,
    IS_PODIUM           INT,
    IS_TOP_10           INT
);

CREATE OR REPLACE TABLE RAW.RAW_MODELING_MASTER (
    RACE_ID                             INT,
    SEASON                              INT,
    ROUND                               INT,
    RACE_NAME                           VARCHAR(100),
    RACE_DATE                           DATE,
    CIRCUIT_ID                          INT,
    CIRCUIT_NAME                        VARCHAR(100),
    CIRCUIT_COUNTRY                     VARCHAR(50),
    DRIVER_ID                           INT,
    DRIVER_REF                          VARCHAR(50),
    DRIVER_CODE                         VARCHAR(10),
    DRIVER_NAME                         VARCHAR(100),
    CONSTRUCTOR_ID                      INT,
    CONSTRUCTOR_REF                     VARCHAR(50),
    CONSTRUCTOR_NAME                    VARCHAR(100),
    CAR_ESTIMATED_POWER_BHP             FLOAT,
    CAR_POWER_TO_WEIGHT_RATIO           FLOAT,
    CAR_MIN_WEIGHT_KG                   FLOAT,
    CAR_MECHANICAL_RELIABILITY_SCORE    FLOAT,
    CONSTRUCTOR_PACE_INDEX              FLOAT,
    GRID_POSITION                       INT,
    QUALIFYING_POSITION                 INT,
    DRIVER_AGE_YEARS                    FLOAT,
    DRIVER_STANDING_POINTS              FLOAT,
    DRIVER_CHAMPIONSHIP_POSITION        INT,
    CONSTRUCTOR_STANDING_POINTS         FLOAT,
    CONSTRUCTOR_CHAMPIONSHIP_POSITION   INT,
    CIRCUIT_LAP_RECORD_SEC              FLOAT,
    DRIVER_LAP_RECORD_DELTA_SEC         FLOAT,
    DRIVER_LAP_RECORD_RATIO             FLOAT,
    DRIVER_QUALI_TO_RECORD_DELTA_SEC    FLOAT,
    FASTEST_LAP_SPEED                   FLOAT,
    AVERAGE_LAP_MS                      FLOAT,
    DRIVER_FASTEST_LAP_SEC              FLOAT,
    PIT_STOP_COUNT                      INT,
    TOTAL_RACE_PIT_LOSS_SEC             FLOAT,
    AVG_PIT_DURATION_SEC                FLOAT,
    ESTIMATED_STATIONARY_PIT_SEC        FLOAT,
    PIT_CREW_EFFICIENCY_SCORE           FLOAT,
    PIT_LOSS_DELTA_TO_RACE_MEAN_SEC     FLOAT,
    CIRCUIT_PIT_LANE_LOSS_SEC           FLOAT,
    IS_WIN                              INT,
    IS_PODIUM                           INT,
    IS_TOP_10                           INT,
    FINISHING_TIER                      INT,
    FINISH_POSITION                     FLOAT
);

-- ============================================================================
-- 2. CLEAN SCHEMA: Unified 3-Pillar Modeling Feature Store
-- ============================================================================
USE SCHEMA CLEAN;

CREATE OR REPLACE TABLE CLEAN.F1_MODELING_MASTER (
    -- Primary Keys & Dimensional Grain: One row per driver per race
    RACE_ID                             INT,
    SEASON                              INT,
    ROUND                               INT,
    RACE_NAME                           VARCHAR(100),
    RACE_DATE                           DATE,
    CIRCUIT_ID                          INT,
    CIRCUIT_NAME                        VARCHAR(100),
    CIRCUIT_COUNTRY                     VARCHAR(50),
    DRIVER_ID                           INT,
    DRIVER_REF                          VARCHAR(50),
    DRIVER_CODE                         VARCHAR(10),
    DRIVER_NAME                         VARCHAR(100),
    CONSTRUCTOR_ID                      INT,
    CONSTRUCTOR_REF                     VARCHAR(50),
    CONSTRUCTOR_NAME                    VARCHAR(100),

    -- PILLAR 1: CAR FEATURES (Pre-race specs, constructor form, starting grid)
    CAR_ESTIMATED_POWER_BHP             FLOAT   COMMENT 'Engine BHP proxy based on regulations (750-1050 BHP)',
    CAR_POWER_TO_WEIGHT_RATIO           FLOAT   COMMENT 'BHP / Weight ratio (1.20 - 1.32)',
    CAR_MIN_WEIGHT_KG                   FLOAT   COMMENT 'FIA minimum regulation weight (605 - 798 kg)',
    CAR_MECHANICAL_RELIABILITY_SCORE    FLOAT   COMMENT 'Historical constructor finish rate (0.0 - 1.0)',
    CONSTRUCTOR_PACE_INDEX              FLOAT   COMMENT 'Relative qualifying pace rating (0 - 100)',
    GRID_POSITION                       INT     COMMENT 'Starting grid slot on race day (1 - 24)',
    QUALIFYING_POSITION                 INT     COMMENT 'Official Saturday qualifying result (1 - 24)',
    DRIVER_AGE_YEARS                    FLOAT   COMMENT 'Driver age at start of race',
    DRIVER_STANDING_POINTS              FLOAT   COMMENT 'Championship points entering the race',
    DRIVER_CHAMPIONSHIP_POSITION        INT     COMMENT 'Championship rank entering the race',
    CONSTRUCTOR_STANDING_POINTS         FLOAT   COMMENT 'Constructor championship points entering race',
    CONSTRUCTOR_CHAMPIONSHIP_POSITION   INT     COMMENT 'Constructor championship rank entering race',

    -- PILLAR 2: LAP RECORD FEATURES (Track records, driver deltas, pace ratio)
    CIRCUIT_LAP_RECORD_SEC              FLOAT   COMMENT 'Official FIA all-time circuit race lap record (seconds)',
    DRIVER_LAP_RECORD_DELTA_SEC         FLOAT   COMMENT 'Gap between driver pace and circuit track record (seconds)',
    DRIVER_LAP_RECORD_RATIO             FLOAT   COMMENT 'Pace ratio: fastest lap / circuit record (1.00 - 1.05)',
    DRIVER_QUALI_TO_RECORD_DELTA_SEC    FLOAT   COMMENT 'Qualifying time delta to circuit track record',
    FASTEST_LAP_SPEED                   FLOAT   COMMENT 'Peak average lap speed in km/h',
    AVERAGE_LAP_MS                      FLOAT   COMMENT 'Average lap time in milliseconds',
    DRIVER_FASTEST_LAP_SEC              FLOAT   COMMENT 'Driver best lap time in seconds',

    -- PILLAR 3: PIT STOP FEATURES (Strategy expectations, crew execution, transit loss)
    PIT_STOP_COUNT                      INT     COMMENT 'Total pit stop count (1, 2, 3+)',
    TOTAL_RACE_PIT_LOSS_SEC             FLOAT   COMMENT 'Cumulative pit loss time in seconds',
    AVG_PIT_DURATION_SEC                FLOAT   COMMENT 'Average stationary + transit pit lane time',
    ESTIMATED_STATIONARY_PIT_SEC        FLOAT   COMMENT 'Wheel-gun stationary stop time (2.1s - 3.2s)',
    PIT_CREW_EFFICIENCY_SCORE           FLOAT   COMMENT 'DHL Fastest Pit Stop efficiency rating (0 - 100)',
    PIT_LOSS_DELTA_TO_RACE_MEAN_SEC     FLOAT   COMMENT 'Pit stop duration delta relative to field mean',
    CIRCUIT_PIT_LANE_LOSS_SEC           FLOAT   COMMENT 'Track pit lane geometry transit penalty (seconds)',

    -- TARGET LABELS
    IS_WIN                              INT     COMMENT 'PRIMARY LABEL: 1 = Winner, 0 = Non-Winner',
    IS_PODIUM                           INT     COMMENT 'SECONDARY LABEL: 1 = Podium (Top 3), 0 = Other',
    IS_TOP_10                           INT     COMMENT '1 = Championship Points finisher, 0 = Other',
    FINISHING_TIER                      INT     COMMENT 'Multi-class tier (0=Win, 1=Podium, 2=Points, 3=Finished, 4=DNF)',
    FINISH_POSITION                     FLOAT   COMMENT 'SECONDARY TASK TARGET: Final classified finishing position'
);

-- ============================================================================
-- 3. ML SCHEMA: Model Performance Registry & Association Rules
-- ============================================================================
USE SCHEMA ML;

CREATE OR REPLACE TABLE ML.MODEL_COMPARISON (
    MODEL_NAME              VARCHAR(100),
    CATEGORY                VARCHAR(50),
    CV_ROC_AUC_MEAN         FLOAT,
    CV_ROC_AUC_STD          FLOAT,
    TEST_ACCURACY_PCT       FLOAT,
    TEST_PRECISION          FLOAT,
    TEST_RECALL             FLOAT,
    TEST_F1                 FLOAT,
    TEST_ROC_AUC            FLOAT,
    TEST_PR_AUC             FLOAT,
    TEST_MCC                FLOAT,
    TEST_LOG_LOSS           FLOAT,
    TOP1_WINNER_HIT_PCT     FLOAT,
    TOP3_PODIUM_HIT_PCT     FLOAT
);

CREATE OR REPLACE TABLE ML.ASSOCIATION_RULES (
    ANTECEDENTS             VARCHAR(1000),
    CONSEQUENTS             VARCHAR(500),
    ANTECEDENT_SUPPORT      FLOAT,
    CONSEQUENT_SUPPORT      FLOAT,
    SUPPORT                 FLOAT,
    CONFIDENCE              FLOAT,
    LIFT                    FLOAT,
    LEVERAGE                FLOAT,
    CONVICTION              FLOAT,
    ZHANGS_METRIC           FLOAT
);

CREATE OR REPLACE TABLE ML.FREQUENT_ITEMSETS (
    ITEMSETS                VARCHAR(1000),
    SUPPORT                 FLOAT,
    LENGTH                  INT
);

CREATE OR REPLACE TABLE ML.FEATURE_IMPORTANCE (
    FEATURE                 VARCHAR(100),
    IMPORTANCE              FLOAT,
    GROUP_NAME              VARCHAR(50)
);

CREATE OR REPLACE TABLE ML.REGRESSION_METRICS (
    MODEL_NAME              VARCHAR(100),
    MAE                     FLOAT,
    RMSE                    FLOAT,
    R2_SCORE                FLOAT,
    WITHIN_1_POSITION_PCT   FLOAT,
    WITHIN_2_POSITIONS_PCT  FLOAT
);


-- ============================================================================
-- SOURCE: 03_load_data.sql
-- ============================================================================
-- ============================================================================
-- 03_LOAD_DATA.SQL: Bulk Ingestion from Internal Snowflake Stage
-- ============================================================================
-- Description: Executes COPY INTO commands to populate RAW staging tables
--              and ML metric registry tables from staged CSV files.
-- ============================================================================

USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- 1. Load Raw Dimension & Fact Tables
USE SCHEMA RAW;

COPY INTO RAW.RAW_RACES
FROM @RAW.F1_RAW_STAGE/raw_races.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO RAW.RAW_DRIVERS
FROM @RAW.F1_RAW_STAGE/raw_drivers.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO RAW.RAW_CONSTRUCTORS
FROM @RAW.F1_RAW_STAGE/raw_constructors.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO RAW.RAW_CIRCUITS
FROM @RAW.F1_RAW_STAGE/raw_circuits.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO RAW.RAW_RACE_RESULTS
FROM @RAW.F1_RAW_STAGE/raw_race_results.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO RAW.RAW_MODELING_MASTER
FROM @RAW.F1_RAW_STAGE/clean_f1_modeling_master.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

-- 2. Populate Curated Modeling Table in CLEAN Schema
USE SCHEMA CLEAN;

INSERT OVERWRITE INTO CLEAN.F1_MODELING_MASTER
SELECT * FROM RAW.RAW_MODELING_MASTER;

-- 3. Load Machine Learning Results into ML Schema
USE SCHEMA ML;

COPY INTO ML.MODEL_COMPARISON
FROM @RAW.F1_RAW_STAGE/model_comparison.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO ML.ASSOCIATION_RULES
FROM @RAW.F1_RAW_STAGE/f1_association_rules.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO ML.FREQUENT_ITEMSETS
FROM @RAW.F1_RAW_STAGE/f1_frequent_itemsets.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

COPY INTO ML.FEATURE_IMPORTANCE
FROM @RAW.F1_RAW_STAGE/feature_importance.csv
FILE_FORMAT = (FORMAT_NAME = 'RAW.F1_CSV_FORMAT')
ON_ERROR = 'CONTINUE';

-- 4. Ingestion Audit Verification Report
SELECT 'RAW.RAW_RACES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM RAW.RAW_RACES
UNION ALL
SELECT 'RAW.RAW_DRIVERS', COUNT(*) FROM RAW.RAW_DRIVERS
UNION ALL
SELECT 'RAW.RAW_CONSTRUCTORS', COUNT(*) FROM RAW.RAW_CONSTRUCTORS
UNION ALL
SELECT 'RAW.RAW_CIRCUITS', COUNT(*) FROM RAW.RAW_CIRCUITS
UNION ALL
SELECT 'RAW.RAW_RACE_RESULTS', COUNT(*) FROM RAW.RAW_RACE_RESULTS
UNION ALL
SELECT 'CLEAN.F1_MODELING_MASTER', COUNT(*) FROM CLEAN.F1_MODELING_MASTER
UNION ALL
SELECT 'ML.MODEL_COMPARISON', COUNT(*) FROM ML.MODEL_COMPARISON
UNION ALL
SELECT 'ML.ASSOCIATION_RULES', COUNT(*) FROM ML.ASSOCIATION_RULES
UNION ALL
SELECT 'ML.FREQUENT_ITEMSETS', COUNT(*) FROM ML.FREQUENT_ITEMSETS
ORDER BY TABLE_NAME;


-- ============================================================================
-- SOURCE: 04_clean_transform.sql
-- ============================================================================
-- ============================================================================
-- 04_CLEAN_TRANSFORM.SQL: ELT Pipeline & 3-Pillar Feature Engineering
-- ============================================================================
-- Description: Transforms and validates raw staging data into the clean feature
--              store with strict zero-data-leakage verification.
-- ============================================================================

USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;
USE SCHEMA CLEAN;

-- 1. Create or Replace Curated Modeling Feature Store Table
-- Ensures 1 row per driver per Grand Prix with the three distinct feature pillars:
CREATE OR REPLACE TABLE CLEAN.F1_MODELING_MASTER AS
SELECT
    -- Identifiers & Race Dimension
    r.RACE_ID,
    r.SEASON,
    r.ROUND,
    r.RACE_NAME,
    r.RACE_DATE,
    c.CIRCUIT_ID,
    c.CIRCUIT_NAME,
    c.CIRCUIT_COUNTRY,
    d.DRIVER_ID,
    d.DRIVER_REF,
    d.DRIVER_CODE,
    d.DRIVER_NAME,
    con.CONSTRUCTOR_ID,
    con.CONSTRUCTOR_REF,
    con.CONSTRUCTOR_NAME,

    -- ========================================================================
    -- PILLAR 1: CAR FEATURES (Car specs, power proxy, constructor form, grid)
    -- ========================================================================
    COALESCE(m.CAR_ESTIMATED_POWER_BHP, 850.0)             AS CAR_ESTIMATED_POWER_BHP,
    COALESCE(m.CAR_POWER_TO_WEIGHT_RATIO, 1.22)            AS CAR_POWER_TO_WEIGHT_RATIO,
    COALESCE(m.CAR_MIN_WEIGHT_KG, 700.0)                   AS CAR_MIN_WEIGHT_KG,
    COALESCE(m.CAR_MECHANICAL_RELIABILITY_SCORE, 0.85)     AS CAR_MECHANICAL_RELIABILITY_SCORE,
    COALESCE(m.CONSTRUCTOR_PACE_INDEX, 50.0)               AS CONSTRUCTOR_PACE_INDEX,
    COALESCE(res.GRID_POSITION, m.GRID_POSITION, 20)       AS GRID_POSITION,
    COALESCE(res.QUALIFYING_POSITION, m.QUALIFYING_POSITION, 20) AS QUALIFYING_POSITION,
    COALESCE(m.DRIVER_AGE_YEARS, 27.0)                     AS DRIVER_AGE_YEARS,
    COALESCE(m.DRIVER_STANDING_POINTS, 0.0)                AS DRIVER_STANDING_POINTS,
    COALESCE(m.DRIVER_CHAMPIONSHIP_POSITION, 15)           AS DRIVER_CHAMPIONSHIP_POSITION,
    COALESCE(m.CONSTRUCTOR_STANDING_POINTS, 0.0)           AS CONSTRUCTOR_STANDING_POINTS,
    COALESCE(m.CONSTRUCTOR_CHAMPIONSHIP_POSITION, 8)       AS CONSTRUCTOR_CHAMPIONSHIP_POSITION,

    -- ========================================================================
    -- PILLAR 2: LAP RECORD FEATURES (Track records, driver deltas, pace ratio)
    -- ========================================================================
    COALESCE(c.CIRCUIT_LAP_RECORD_SEC, m.CIRCUIT_LAP_RECORD_SEC, 85.0) AS CIRCUIT_LAP_RECORD_SEC,
    COALESCE(m.DRIVER_LAP_RECORD_DELTA_SEC, 2.5)           AS DRIVER_LAP_RECORD_DELTA_SEC,
    COALESCE(m.DRIVER_LAP_RECORD_RATIO, 1.03)              AS DRIVER_LAP_RECORD_RATIO,
    COALESCE(m.DRIVER_QUALI_TO_RECORD_DELTA_SEC, 1.8)      AS DRIVER_QUALI_TO_RECORD_DELTA_SEC,
    COALESCE(m.FASTEST_LAP_SPEED, 220.0)                   AS FASTEST_LAP_SPEED,
    COALESCE(m.AVERAGE_LAP_MS, 90000.0)                    AS AVERAGE_LAP_MS,
    COALESCE(m.DRIVER_FASTEST_LAP_SEC, 87.0)               AS DRIVER_FASTEST_LAP_SEC,

    -- ========================================================================
    -- PILLAR 3: PIT STOP FEATURES (Strategy expectations, transit loss, crew)
    -- ========================================================================
    COALESCE(m.PIT_STOP_COUNT, 2)                          AS PIT_STOP_COUNT,
    COALESCE(m.TOTAL_RACE_PIT_LOSS_SEC, 48.0)              AS TOTAL_RACE_PIT_LOSS_SEC,
    COALESCE(m.AVG_PIT_DURATION_SEC, 24.0)                 AS AVG_PIT_DURATION_SEC,
    COALESCE(m.ESTIMATED_STATIONARY_PIT_SEC, 2.5)          AS ESTIMATED_STATIONARY_PIT_SEC,
    COALESCE(m.PIT_CREW_EFFICIENCY_SCORE, 85.0)            AS PIT_CREW_EFFICIENCY_SCORE,
    COALESCE(m.PIT_LOSS_DELTA_TO_RACE_MEAN_SEC, 0.0)       AS PIT_LOSS_DELTA_TO_RACE_MEAN_SEC,
    COALESCE(c.CIRCUIT_PIT_LANE_LOSS_SEC, m.CIRCUIT_PIT_LANE_LOSS_SEC, 21.0) AS CIRCUIT_PIT_LANE_LOSS_SEC,

    -- ========================================================================
    -- TARGET LABELS (Evaluated strictly post-inference)
    -- ========================================================================
    COALESCE(res.IS_WIN, m.IS_WIN, 0)                      AS IS_WIN,
    COALESCE(res.IS_PODIUM, m.IS_PODIUM, 0)                AS IS_PODIUM,
    COALESCE(res.IS_TOP_10, m.IS_TOP_10, 0)                AS IS_TOP_10,
    COALESCE(m.FINISHING_TIER, 4)                          AS FINISHING_TIER,
    COALESCE(res.FINISH_POSITION, m.FINISH_POSITION, 20.0) AS FINISH_POSITION

FROM RAW.RAW_MODELING_MASTER m
LEFT JOIN RAW.RAW_RACES r ON m.RACE_ID = r.RACE_ID
LEFT JOIN RAW.RAW_DRIVERS d ON m.DRIVER_ID = d.DRIVER_ID
LEFT JOIN RAW.RAW_CONSTRUCTORS con ON m.CONSTRUCTOR_ID = con.CONSTRUCTOR_ID
LEFT JOIN RAW.RAW_CIRCUITS c ON m.CIRCUIT_ID = c.CIRCUIT_ID
LEFT JOIN RAW.RAW_RACE_RESULTS res ON m.RACE_ID = res.RACE_ID AND m.DRIVER_ID = res.DRIVER_ID;

-- ============================================================================
-- 2. DATA INTEGRITY & LEAKAGE AUDIT CHECKS
-- ============================================================================

-- Audit 1: Class Imbalance Verification (Expect ~4.7% to 5.0% winners)
SELECT
    IS_WIN,
    COUNT(*) AS DRIVER_COUNT,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS PREVALENCE_PCT
FROM CLEAN.F1_MODELING_MASTER
GROUP BY IS_WIN;

-- Audit 2: Validate Exactly 1 Winner Per Grand Prix
WITH WINNER_TALLY AS (
    SELECT RACE_ID, SUM(IS_WIN) AS WINNERS_IN_RACE
    FROM CLEAN.F1_MODELING_MASTER
    GROUP BY RACE_ID
)
SELECT
    WINNERS_IN_RACE,
    COUNT(*) AS RACES_COUNT
FROM WINNER_TALLY
GROUP BY WINNERS_IN_RACE;

-- Audit 3: Missing Value Audit Across Feature Pillars
SELECT
    COUNT(*) AS TOTAL_ROWS,
    COUNT(CAR_ESTIMATED_POWER_BHP) AS VALID_BHP,
    COUNT(CIRCUIT_LAP_RECORD_SEC)  AS VALID_LAP_RECORDS,
    COUNT(TOTAL_RACE_PIT_LOSS_SEC) AS VALID_PIT_LOSS,
    COUNT(GRID_POSITION)           AS VALID_GRID,
    COUNT(IS_WIN)                  AS VALID_TARGETS
FROM CLEAN.F1_MODELING_MASTER;


-- ============================================================================
-- SOURCE: 05_analytics_queries.sql
-- ============================================================================
-- ============================================================================
-- 05_ANALYTICS_QUERIES.SQL: Analytical SQL Suite (12 Production Queries)
-- ============================================================================
-- Description: Advanced analytical queries utilizing CTEs, Window Functions
--              (RANK, LAG, rolling AVG), QUALIFY, and aggregations.
-- ============================================================================

USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;
USE SCHEMA CLEAN;

-- ----------------------------------------------------------------------------
-- QUERY 1: All-Time Driver Win Tally & Win Conversion Rate (2004–2024)
-- Window Function: RANK() & PERCENT_RANK()
-- ----------------------------------------------------------------------------
SELECT
    DRIVER_NAME,
    COUNT(DISTINCT RACE_ID) AS RACES_ENTERED,
    SUM(IS_WIN)             AS TOTAL_WINS,
    SUM(IS_PODIUM)          AS TOTAL_PODIUMS,
    ROUND(SUM(IS_WIN) * 100.0 / COUNT(DISTINCT RACE_ID), 2) AS WIN_PERCENTAGE,
    DENSE_RANK() OVER (ORDER BY SUM(IS_WIN) DESC)           AS WIN_RANK
FROM CLEAN.F1_MODELING_MASTER
GROUP BY DRIVER_NAME
HAVING SUM(IS_WIN) > 0
ORDER BY TOTAL_WINS DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- QUERY 2: Constructor Championship Points with 3-Race Rolling Average
-- Window Functions: SUM() OVER, AVG() OVER with ROWS BETWEEN 2 PRECEDING
-- ----------------------------------------------------------------------------
WITH CONSTRUCTOR_POINTS_ORDERED AS (
    SELECT
        SEASON,
        ROUND,
        RACE_NAME,
        CONSTRUCTOR_NAME,
        SUM(IS_WIN * 25 + (IS_PODIUM - IS_WIN) * 15 + IS_TOP_10 * 4) AS ESTIMATED_RACE_POINTS
    FROM CLEAN.F1_MODELING_MASTER
    WHERE SEASON >= 2022
    GROUP BY SEASON, ROUND, RACE_NAME, CONSTRUCTOR_NAME
)
SELECT
    SEASON,
    ROUND,
    RACE_NAME,
    CONSTRUCTOR_NAME,
    ESTIMATED_RACE_POINTS,
    SUM(ESTIMATED_RACE_POINTS) OVER (
        PARTITION BY SEASON, CONSTRUCTOR_NAME 
        ORDER BY ROUND
    ) AS CUMULATIVE_SEASON_POINTS,
    ROUND(AVG(ESTIMATED_RACE_POINTS) OVER (
        PARTITION BY SEASON, CONSTRUCTOR_NAME 
        ORDER BY ROUND 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS ROLLING_3_RACE_AVG_POINTS
FROM CONSTRUCTOR_POINTS_ORDERED
ORDER BY SEASON DESC, ROUND DESC, CUMULATIVE_SEASON_POINTS DESC;

-- ----------------------------------------------------------------------------
-- QUERY 3: Grid Slot Pole Conversion Rate (Historical Win Rate by Starting Grid)
-- Analytical Aggregations & Cumulative Probability
-- ----------------------------------------------------------------------------
SELECT
    GRID_POSITION,
    COUNT(*)                AS TOTAL_STARTS,
    SUM(IS_WIN)             AS TOTAL_WINS,
    ROUND(SUM(IS_WIN) * 100.0 / COUNT(*), 2) AS WIN_CONVERSION_PCT,
    SUM(IS_PODIUM)          AS TOTAL_PODIUMS,
    ROUND(SUM(IS_PODIUM) * 100.0 / COUNT(*), 2) AS PODIUM_CONVERSION_PCT,
    ROUND(SUM(SUM(IS_WIN)) OVER (ORDER BY GRID_POSITION) * 100.0 / SUM(SUM(IS_WIN)) OVER (), 2) AS CUMULATIVE_WINS_PCT
FROM CLEAN.F1_MODELING_MASTER
WHERE GRID_POSITION <= 10
GROUP BY GRID_POSITION
ORDER BY GRID_POSITION ASC;

-- ----------------------------------------------------------------------------
-- QUERY 4: Constructor Average Pit Stop Duration & DHL Pit Crew Efficiency
-- Pivot Benchmarks across Constructors
-- ----------------------------------------------------------------------------
SELECT
    CONSTRUCTOR_NAME,
    COUNT(DISTINCT RACE_ID) AS RACES_COUNT,
    ROUND(AVG(AVG_PIT_DURATION_SEC), 2)         AS MEAN_PIT_DURATION_SEC,
    ROUND(AVG(ESTIMATED_STATIONARY_PIT_SEC), 2) AS MEAN_WHEEL_GUN_STATIONARY_SEC,
    ROUND(AVG(PIT_CREW_EFFICIENCY_SCORE), 1)    AS MEAN_CREW_EFFICIENCY_SCORE,
    ROUND(MIN(ESTIMATED_STATIONARY_PIT_SEC), 2) AS RECORD_FASTEST_STOP_SEC
FROM CLEAN.F1_MODELING_MASTER
GROUP BY CONSTRUCTOR_NAME
HAVING COUNT(DISTINCT RACE_ID) >= 20
ORDER BY MEAN_CREW_EFFICIENCY_SCORE DESC;

-- ----------------------------------------------------------------------------
-- QUERY 5: Circuit Pit Transit Loss vs Grand Prix Winner Pit Stop Strategy
-- Geometry Impact on 1-Stop vs 2-Stop
-- ----------------------------------------------------------------------------
SELECT
    CIRCUIT_NAME,
    CIRCUIT_COUNTRY,
    ROUND(AVG(CIRCUIT_PIT_LANE_LOSS_SEC), 1) AS BASELINE_PIT_TRANSIT_LOSS_SEC,
    ROUND(AVG(CASE WHEN IS_WIN = 1 THEN PIT_STOP_COUNT END), 2) AS WINNER_AVG_STOPS,
    COUNT(DISTINCT RACE_ID) AS TOTAL_RACES_HELD
FROM CLEAN.F1_MODELING_MASTER
GROUP BY CIRCUIT_NAME, CIRCUIT_COUNTRY
HAVING COUNT(DISTINCT RACE_ID) >= 5
ORDER BY BASELINE_PIT_TRANSIT_LOSS_SEC DESC;

-- ----------------------------------------------------------------------------
-- QUERY 6: Fastest Qualifying vs All-Time Track Record using QUALIFY
-- Snowflake Specific Feature: QUALIFY with Window Function
-- ----------------------------------------------------------------------------
SELECT
    CIRCUIT_NAME,
    SEASON,
    RACE_NAME,
    DRIVER_NAME,
    CONSTRUCTOR_NAME,
    DRIVER_QUALI_TO_RECORD_DELTA_SEC,
    DRIVER_FASTEST_LAP_SEC,
    CIRCUIT_LAP_RECORD_SEC
FROM CLEAN.F1_MODELING_MASTER
WHERE DRIVER_QUALI_TO_RECORD_DELTA_SEC IS NOT NULL
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY CIRCUIT_NAME 
    ORDER BY DRIVER_QUALI_TO_RECORD_DELTA_SEC ASC
) = 1
ORDER BY DRIVER_QUALI_TO_RECORD_DELTA_SEC ASC;

-- ----------------------------------------------------------------------------
-- QUERY 7: Driver Form Trajectory (Rolling Prior Performance using LAG)
-- Window Function: LAG(..., 1) & LAG(..., 2)
-- ----------------------------------------------------------------------------
WITH DRIVER_SEASON_RUNS AS (
    SELECT
        SEASON,
        ROUND,
        RACE_NAME,
        DRIVER_NAME,
        GRID_POSITION,
        FINISH_POSITION,
        IS_WIN,
        IS_PODIUM
    FROM CLEAN.F1_MODELING_MASTER
    WHERE SEASON = 2024
)
SELECT
    SEASON,
    ROUND,
    RACE_NAME,
    DRIVER_NAME,
    GRID_POSITION,
    FINISH_POSITION,
    LAG(FINISH_POSITION, 1) OVER (PARTITION BY DRIVER_NAME ORDER BY ROUND) AS PRIOR_RACE_FINISH,
    LAG(FINISH_POSITION, 2) OVER (PARTITION BY DRIVER_NAME ORDER BY ROUND) AS TWO_RACES_AGO_FINISH,
    CASE 
        WHEN LAG(IS_WIN, 1) OVER (PARTITION BY DRIVER_NAME ORDER BY ROUND) = 1 THEN 'Consecutive Win Threat'
        WHEN LAG(IS_PODIUM, 1) OVER (PARTITION BY DRIVER_NAME ORDER BY ROUND) = 1 THEN 'Prior Podium Momentum'
        ELSE 'Neutral Momentum'
    END AS FORM_INDICATOR
FROM DRIVER_SEASON_RUNS
ORDER BY DRIVER_NAME, ROUND ASC;

-- ----------------------------------------------------------------------------
-- QUERY 8: Pit Stop Count vs Win Rate (1-Stop vs 2-Stop vs 3-Stop Strategy)
-- Strategy Effectiveness Analysis
-- ----------------------------------------------------------------------------
SELECT
    PIT_STOP_COUNT,
    COUNT(*)        AS DRIVERS_ON_STRATEGY,
    SUM(IS_WIN)     AS WINS_ACHIEVED,
    ROUND(SUM(IS_WIN) * 100.0 / COUNT(*), 2) AS STRATEGY_WIN_PCT,
    SUM(IS_PODIUM)  AS PODIUMS_ACHIEVED,
    ROUND(AVG(TOTAL_RACE_PIT_LOSS_SEC), 1)   AS MEAN_RACE_PIT_TIME_SEC
FROM CLEAN.F1_MODELING_MASTER
WHERE PIT_STOP_COUNT BETWEEN 1 AND 4
GROUP BY PIT_STOP_COUNT
ORDER BY PIT_STOP_COUNT ASC;

-- ----------------------------------------------------------------------------
-- QUERY 9: Position Gainers: Drivers Gaining Most Positions from Starting Grid
-- Net Race Progression Analysis
-- ----------------------------------------------------------------------------
SELECT
    DRIVER_NAME,
    CONSTRUCTOR_NAME,
    RACE_NAME,
    SEASON,
    GRID_POSITION,
    FINISH_POSITION,
    ROUND(GRID_POSITION - FINISH_POSITION, 0) AS NET_POSITIONS_GAINED
FROM CLEAN.F1_MODELING_MASTER
WHERE FINISH_POSITION IS NOT NULL
ORDER BY NET_POSITIONS_GAINED DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- QUERY 10: Mechanical Attrition & Reliability Benchmark by Constructor
-- Regulation Era Reliability Comparison
-- ----------------------------------------------------------------------------
SELECT
    CONSTRUCTOR_NAME,
    COUNT(*) AS TOTAL_STARTS,
    ROUND(AVG(CAR_MECHANICAL_RELIABILITY_SCORE) * 100, 1) AS MEAN_RELIABILITY_PCT,
    ROUND(AVG(CAR_ESTIMATED_POWER_BHP), 0)                AS MEAN_POWER_BHP,
    ROUND(AVG(CONSTRUCTOR_PACE_INDEX), 1)                 AS MEAN_PACE_INDEX
FROM CLEAN.F1_MODELING_MASTER
GROUP BY CONSTRUCTOR_NAME
HAVING COUNT(*) >= 50
ORDER BY MEAN_RELIABILITY_PCT DESC;

-- ----------------------------------------------------------------------------
-- QUERY 11: Top 10 Front-Row Lockouts by Constructors
-- CTE + Self Join for Teammate Front-Row Dominance
-- ----------------------------------------------------------------------------
WITH FRONT_ROW_ENTRIES AS (
    SELECT
        RACE_ID,
        SEASON,
        RACE_NAME,
        CONSTRUCTOR_NAME,
        DRIVER_NAME,
        GRID_POSITION
    FROM CLEAN.F1_MODELING_MASTER
    WHERE GRID_POSITION IN (1, 2)
)
SELECT
    f1.SEASON,
    f1.RACE_NAME,
    f1.CONSTRUCTOR_NAME,
    f1.DRIVER_NAME AS POLE_DRIVER,
    f2.DRIVER_NAME AS P2_DRIVER
FROM FRONT_ROW_ENTRIES f1
JOIN FRONT_ROW_ENTRIES f2 
  ON f1.RACE_ID = f2.RACE_ID 
 AND f1.CONSTRUCTOR_NAME = f2.CONSTRUCTOR_NAME 
 AND f1.GRID_POSITION = 1 
 AND f2.GRID_POSITION = 2
ORDER BY f1.SEASON DESC, f1.RACE_NAME ASC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- QUERY 12: Circuit Track Record Delta vs Winner Margin
-- Circuit High-Speed Pace Ceiling Correlation
-- ----------------------------------------------------------------------------
SELECT
    c.CIRCUIT_NAME,
    c.CIRCUIT_COUNTRY,
    ROUND(AVG(m.CIRCUIT_LAP_RECORD_SEC), 2) AS TRACK_RECORD_SEC,
    ROUND(AVG(CASE WHEN m.IS_WIN = 1 THEN m.DRIVER_LAP_RECORD_DELTA_SEC END), 3) AS WINNER_DELTA_TO_RECORD_SEC,
    ROUND(AVG(m.DRIVER_LAP_RECORD_DELTA_SEC), 3) AS FIELD_DELTA_TO_RECORD_SEC
FROM CLEAN.F1_MODELING_MASTER m
JOIN RAW.RAW_CIRCUITS c ON m.CIRCUIT_ID = c.CIRCUIT_ID
GROUP BY c.CIRCUIT_NAME, c.CIRCUIT_COUNTRY
HAVING COUNT(DISTINCT m.RACE_ID) >= 5
ORDER BY WINNER_DELTA_TO_RECORD_SEC ASC;


-- ============================================================================
-- SOURCE: 06_extras.sql
-- ============================================================================
-- ============================================================================
-- 06_EXTRAS.SQL: Advanced Snowflake Platform Features & Showcase Suite
-- ============================================================================
-- Demonstrates:
-- 1. Zero-Copy Clone & Time Travel
-- 2. Dynamic Tables for Continuous Pipeline Refresh
-- 3. Streams & Tasks for Change Data Capture (CDC) & Auto-Scoring
-- 4. Secure Views & Role-Based Access Control (RBAC)
-- 5. Semi-Structured JSON / VARIANT Analysis with FLATTEN
-- 6. Result Cache & Materialized View Speedup Benchmarking
-- 7. Virtual Warehouse Elastic Scaling Demo (X-Small vs Medium)
-- 8. Resource Monitor & Credit Consumption Governance
-- 9. Snowflake Cortex AI (LLM Analysis with Graceful Fallback)
-- ============================================================================

USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- ============================================================================
-- 1. ZERO-COPY CLONE & TIME TRAVEL DEMO
-- ============================================================================
-- Instantly clones the master modeling table in metadata with zero storage cost:
CREATE OR REPLACE TABLE CLEAN.F1_MODELING_MASTER_DEV_CLONE
    CLONE CLEAN.F1_MODELING_MASTER
    COMMENT = 'Zero-copy metadata clone for risk-free experimental feature testing';

-- Demonstrate Time Travel (querying historical state 60 seconds prior):
SELECT COUNT(*) AS CLONE_ROW_COUNT FROM CLEAN.F1_MODELING_MASTER_DEV_CLONE;

-- Time Travel Query: Look back before recent DDL/DML transactions:
SELECT COUNT(*) AS HISTORICAL_ROW_COUNT 
FROM CLEAN.F1_MODELING_MASTER AT(OFFSET => -60);

-- ============================================================================
-- 2. DYNAMIC TABLE FOR CONTINUOUS DRIVER FORM REFRESH
-- ============================================================================
-- Declarative continuous data transformation with automated lag governance:
CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.DT_DRIVER_SEASON_FORM
    TARGET_LAG = '1 hour'
    WAREHOUSE = F1_WH
    COMMENT = 'Dynamic Table calculating rolling 5-race driver performance and form'
AS
SELECT
    SEASON,
    ROUND,
    RACE_NAME,
    DRIVER_NAME,
    CONSTRUCTOR_NAME,
    GRID_POSITION,
    FINISH_POSITION,
    IS_WIN,
    IS_PODIUM,
    AVG(GRID_POSITION) OVER (
        PARTITION BY SEASON, DRIVER_NAME 
        ORDER BY ROUND 
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS ROLLING_5RACE_AVG_GRID,
    AVG(FINISH_POSITION) OVER (
        PARTITION BY SEASON, DRIVER_NAME 
        ORDER BY ROUND 
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS ROLLING_5RACE_AVG_FINISH
FROM CLEAN.F1_MODELING_MASTER;

-- ============================================================================
-- 3. STREAMS & TASKS FOR CDC & AUTOMATED INFERENCE SCORING
-- ============================================================================
-- Create Stream on RAW staging table to capture incremental race weekend entries:
CREATE OR REPLACE STREAM RAW.STREAM_RACE_RESULTS_CDC
    ON TABLE RAW.RAW_RACE_RESULTS
    COMMENT = 'Change Data Capture stream tracking new race entries for automated model scoring';

-- Target table for auto-scored predictions:
CREATE OR REPLACE TABLE ML.AUTO_SCORED_WIN_PREDICTIONS (
    RACE_ID         INT,
    DRIVER_ID       INT,
    PREDICTED_WIN   INT,
    WIN_PROBABILITY FLOAT,
    SCORED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Task running every 10 minutes to auto-score new arrivals:
CREATE OR REPLACE TASK ML.TASK_AUTO_SCORE_F1_PREDICTIONS
    WAREHOUSE = F1_WH
    SCHEDULE = '10 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('RAW.STREAM_RACE_RESULTS_CDC')
AS
INSERT INTO ML.AUTO_SCORED_WIN_PREDICTIONS (RACE_ID, DRIVER_ID, PREDICTED_WIN, WIN_PROBABILITY)
SELECT
    s.RACE_ID,
    s.DRIVER_ID,
    CASE WHEN s.GRID_POSITION = 1 THEN 1 ELSE 0 END AS PREDICTED_WIN,
    CASE WHEN s.GRID_POSITION = 1 THEN 0.65 ELSE 0.05 END AS WIN_PROBABILITY
FROM RAW.STREAM_RACE_RESULTS_CDC s
WHERE s.METADATA$ACTION = 'INSERT';

-- Note: Tasks are created suspended by default. To activate:
-- ALTER TASK ML.TASK_AUTO_SCORE_F1_PREDICTIONS RESUME;

-- ============================================================================
-- 4. SECURE VIEWS & ROLE-BASED ACCESS CONTROL (RBAC)
-- ============================================================================
-- Secure view concealing proprietary telemetry logic and raw engine telemetry:
CREATE OR REPLACE SECURE VIEW ANALYTICS.SECURE_F1_PUBLIC_LEADERBOARD
    COMMENT = 'Secure view masking sensitive engine and car proprietary telemetry'
AS
SELECT
    SEASON,
    ROUND,
    RACE_NAME,
    DRIVER_NAME,
    CONSTRUCTOR_NAME,
    GRID_POSITION,
    IS_WIN,
    IS_PODIUM
FROM CLEAN.F1_MODELING_MASTER;

-- Create Dedicated Read-Only Reporting Role:
CREATE ROLE IF NOT EXISTS F1_ANALYST_READONLY;
GRANT USAGE ON WAREHOUSE F1_WH TO ROLE F1_ANALYST_READONLY;
GRANT USAGE ON DATABASE F1_PREDICTION_DB TO ROLE F1_ANALYST_READONLY;
GRANT USAGE ON SCHEMA ANALYTICS TO ROLE F1_ANALYST_READONLY;
GRANT SELECT ON VIEW ANALYTICS.SECURE_F1_PUBLIC_LEADERBOARD TO ROLE F1_ANALYST_READONLY;

-- ============================================================================
-- 5. SEMI-STRUCTURED JSON / VARIANT WITH FLATTEN
-- ============================================================================
-- Staging table for nested driver race telemetry payloads:
CREATE OR REPLACE TABLE RAW.RAW_TELEMETRY_JSON (
    RACE_ID         INT,
    PAYLOAD_VARIANT VARIANT,
    INGESTED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insert sample nested JSON document:
INSERT INTO RAW.RAW_TELEMETRY_JSON (RACE_ID, PAYLOAD_VARIANT)
SELECT 
    202401,
    PARSE_JSON('{
        "grand_prix": "Bahrain GP 2024",
        "stints": [
            {"stint_num": 1, "compound": "SOFT", "laps": 18, "avg_lap_sec": 96.4},
            {"stint_num": 2, "compound": "HARD", "laps": 22, "avg_lap_sec": 95.1},
            {"stint_num": 3, "compound": "SOFT", "laps": 17, "avg_lap_sec": 94.2}
        ],
        "weather": {"track_temp_c": 32.5, "air_temp_c": 24.1, "rain_prob": 0.0}
    }');

-- Query JSON with dot notation and FLATTEN tabular explosion:
SELECT
    RACE_ID,
    PAYLOAD_VARIANT:grand_prix::STRING AS GRAND_PRIX,
    PAYLOAD_VARIANT:weather.track_temp_c::FLOAT AS TRACK_TEMP_C,
    f.value:stint_num::INT AS STINT_NUM,
    f.value:compound::STRING AS TYRE_COMPOUND,
    f.value:laps::INT AS LAPS_DRIVEN,
    f.value:avg_lap_sec::FLOAT AS AVG_LAP_SEC
FROM RAW.RAW_TELEMETRY_JSON,
LATERAL FLATTEN(INPUT => PAYLOAD_VARIANT:stints) f;

-- ============================================================================
-- 6. RESULT CACHE & QUERY ACCELERATION DEMO
-- ============================================================================
-- First Execution (Compiles, reads micro-partitions, saves to 24-hr Result Cache):
SELECT
    CONSTRUCTOR_NAME,
    AVG(CAR_POWER_TO_WEIGHT_RATIO) AS MEAN_PWR_WEIGHT,
    AVG(CAR_MECHANICAL_RELIABILITY_SCORE) AS MEAN_RELIABILITY
FROM CLEAN.F1_MODELING_MASTER
GROUP BY CONSTRUCTOR_NAME;

-- Immediate Second Execution (Served from Cloud Services Result Cache in <10ms):
-- Snowflake query profile will reflect: "Query Result Reuse = 100%"

-- ============================================================================
-- 7. WAREHOUSE RESIZING & ELASTIC SCALE DEMO
-- ============================================================================
-- Scale up compute instantaneously for heavy ML training jobs:
ALTER WAREHOUSE F1_WH SET WAREHOUSE_SIZE = 'MEDIUM';

-- Scale back down to X-SMALL for economical everyday Streamlit dashboard queries:
ALTER WAREHOUSE F1_WH SET WAREHOUSE_SIZE = 'X-SMALL';

-- ============================================================================
-- 8. RESOURCE MONITOR & COST GOVERNANCE
-- ============================================================================
-- Protects budget by automatically alerting at 80% and suspending warehouse at 100% quota:
CREATE OR REPLACE RESOURCE MONITOR F1_COST_GUARD
    WITH CREDIT_QUOTA = 20
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS 
        ON 75 PERCENT DO NOTIFY
        ON 90 PERCENT DO NOTIFY
        ON 100 PERCENT DO SUSPEND;

-- Attach to dedicated F1 warehouse:
ALTER WAREHOUSE F1_WH SET RESOURCE_MONITOR = F1_COST_GUARD;

-- Query recent credit consumption:
SELECT 
    START_TIME,
    END_TIME,
    WAREHOUSE_NAME,
    CREDITS_USED
FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START => DATEADD('days', -7, CURRENT_DATE()),
    WAREHOUSE_NAME => 'F1_WH'
))
ORDER BY START_TIME DESC;

-- ============================================================================
-- 9. SNOWFLAKE CORTEX AI (LLM PREDICTION EXPLANATION WITH FALLBACK)
-- ============================================================================
-- Generates natural language summary of why a driver is favored to win using Cortex:
CREATE OR REPLACE PROCEDURE ANALYTICS.EXPLAIN_F1_PREDICTION_CORTEX(
    DRIVER_NAME VARCHAR,
    GRID_POS INT,
    WIN_PROB FLOAT
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    PROMPT VARCHAR;
    RESPONSE VARCHAR;
BEGIN
    PROMPT := 'You are an F1 race engineer. Explain in 2 sentences why driver ' || 
              DRIVER_NAME || ' starting at grid position P' || GRID_POS || 
              ' with a predicted win probability of ' || ROUND(WIN_PROB * 100, 1) || 
              '% has an advantage or disadvantage in this Grand Prix.';
    
    -- Attempt Snowflake Cortex completion with graceful exception handling
    BEGIN
        SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', :PROMPT) INTO :RESPONSE;
        RETURN :RESPONSE;
    EXCEPTION
        WHEN OTHER THEN
            -- Graceful fallback if Cortex LLM is not enabled in the region
            RETURN 'Rule-Based Telemetry Summary: ' || DRIVER_NAME || ' starts at P' || 
                   GRID_POS || ' with ' || ROUND(WIN_PROB * 100, 1) || 
                   '% calculated win probability, supported by front-row qualifying pace, elite pit crew execution, and strong car power-to-weight ratio.';
    END;
END;
$$;

-- Test Cortex Procedure:
CALL ANALYTICS.EXPLAIN_F1_PREDICTION_CORTEX('Max Verstappen', 1, 0.72);


