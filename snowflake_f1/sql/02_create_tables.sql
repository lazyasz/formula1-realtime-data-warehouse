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
