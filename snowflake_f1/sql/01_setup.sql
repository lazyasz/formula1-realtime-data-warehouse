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
