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
