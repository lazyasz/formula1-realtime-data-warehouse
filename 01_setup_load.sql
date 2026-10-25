-- ============================================================================
-- 01_SETUP_LOAD.SQL: SNOWFLAKE SETUP, DATABASE, SCHEMAS & RAW DATA INGESTION
-- ============================================================================
-- Project: Formula 1 Race Winner Prediction (Data Warehousing & Data Mining)
-- Platform: Snowflake (F1_DM.RAW, F1_DM.STAGING, F1_DM.ANALYTICS)
-- Warehouse: F1_WH (XSMALL, Auto-Suspend 60s)
-- ============================================================================

-- 1. DATABASE, SCHEMAS AND VIRTUAL WAREHOUSE PROVISIONING
CREATE DATABASE IF NOT EXISTS F1_DM;
CREATE SCHEMA IF NOT EXISTS F1_DM.RAW;
CREATE SCHEMA IF NOT EXISTS F1_DM.STAGING;
CREATE SCHEMA IF NOT EXISTS F1_DM.ANALYTICS;

CREATE WAREHOUSE IF NOT EXISTS F1_WH
    WITH 
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Dedicated virtual warehouse for F1 Data Warehousing and Data Mining workloads';

USE WAREHOUSE F1_WH;
USE DATABASE F1_DM;
USE SCHEMA F1_DM.RAW;

-- 2. FILE FORMAT & NAMED INTERNAL STAGE
CREATE OR REPLACE FILE FORMAT F1_CSV
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('\\N', '', 'NULL', 'null')
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    COMMENT = 'CSV parser format for Ergast / Jolpica F1 dataset exports';

CREATE OR REPLACE STAGE F1_STAGE
    FILE_FORMAT = F1_CSV
    COMMENT = 'Internal stage for landing Kaggle Formula 1 World Championship 1950-2024 CSV files';

-- To stage local CSVs from SnowSQL or client:
-- PUT file:///path/to/ergast/*.csv @F1_STAGE AUTO_COMPRESS=TRUE;

-- 3. RAW INGESTION DDL (9 CORE ERGAST TABLES)

CREATE OR REPLACE TABLE RACES (
    raceId INT PRIMARY KEY,
    year INT NOT NULL,
    round INT NOT NULL,
    circuitId INT NOT NULL,
    name STRING NOT NULL,
    date DATE NOT NULL,
    time STRING,
    url STRING
);

CREATE OR REPLACE TABLE CIRCUITS (
    circuitId INT PRIMARY KEY,
    circuitRef STRING NOT NULL,
    name STRING NOT NULL,
    location STRING,
    country STRING,
    lat FLOAT,
    lng FLOAT,
    alt INT,
    url STRING
);

CREATE OR REPLACE TABLE DRIVERS (
    driverId INT PRIMARY KEY,
    driverRef STRING NOT NULL,
    number STRING,
    code STRING,
    forename STRING NOT NULL,
    surname STRING NOT NULL,
    dob DATE,
    nationality STRING,
    url STRING
);

CREATE OR REPLACE TABLE CONSTRUCTORS (
    constructorId INT PRIMARY KEY,
    constructorRef STRING NOT NULL,
    name STRING NOT NULL,
    nationality STRING,
    url STRING
);

CREATE OR REPLACE TABLE RESULTS (
    resultId INT PRIMARY KEY,
    raceId INT NOT NULL,
    driverId INT NOT NULL,
    constructorId INT NOT NULL,
    number STRING,
    grid INT NOT NULL,
    position STRING,
    positionText STRING,
    positionOrder INT NOT NULL,
    points FLOAT NOT NULL,
    laps INT NOT NULL,
    time STRING,
    milliseconds INT,
    fastestLap INT,
    rank INT,
    fastestLapTime STRING,
    fastestLapSpeed FLOAT,
    statusId INT NOT NULL
);

CREATE OR REPLACE TABLE QUALIFYING (
    qualifyId INT PRIMARY KEY,
    raceId INT NOT NULL,
    driverId INT NOT NULL,
    constructorId INT NOT NULL,
    number STRING,
    position INT NOT NULL,
    q1 STRING,
    q2 STRING,
    q3 STRING
);

CREATE OR REPLACE TABLE LAP_TIMES (
    raceId INT NOT NULL,
    driverId INT NOT NULL,
    lap INT NOT NULL,
    position INT,
    time STRING,
    milliseconds INT NOT NULL,
    PRIMARY KEY (raceId, driverId, lap)
);

CREATE OR REPLACE TABLE PIT_STOPS (
    raceId INT NOT NULL,
    driverId INT NOT NULL,
    stop INT NOT NULL,
    lap INT NOT NULL,
    time STRING,
    duration STRING,
    milliseconds INT NOT NULL,
    PRIMARY KEY (raceId, driverId, stop)
);

CREATE OR REPLACE TABLE STATUS (
    statusId INT PRIMARY KEY,
    status STRING NOT NULL
);

-- 4. COPY INTO EXECUTION COMMANDS (IDEMPOTENT DATA LOAD)
COPY INTO RACES FROM @F1_STAGE/races.csv ON_ERROR = 'CONTINUE';
COPY INTO CIRCUITS FROM @F1_STAGE/circuits.csv ON_ERROR = 'CONTINUE';
COPY INTO DRIVERS FROM @F1_STAGE/drivers.csv ON_ERROR = 'CONTINUE';
COPY INTO CONSTRUCTORS FROM @F1_STAGE/constructors.csv ON_ERROR = 'CONTINUE';
COPY INTO RESULTS FROM @F1_STAGE/results.csv ON_ERROR = 'CONTINUE';
COPY INTO QUALIFYING FROM @F1_STAGE/qualifying.csv ON_ERROR = 'CONTINUE';
COPY INTO LAP_TIMES FROM @F1_STAGE/lap_times.csv ON_ERROR = 'CONTINUE';
COPY INTO PIT_STOPS FROM @F1_STAGE/pit_stops.csv ON_ERROR = 'CONTINUE';
COPY INTO STATUS FROM @F1_STAGE/status.csv ON_ERROR = 'CONTINUE';

-- 5. VALIDATION CHECKS (AUDIT RECORD COUNTS)
SELECT 'RACES' AS table_name, COUNT(*) AS row_count FROM RACES
UNION ALL
SELECT 'CIRCUITS', COUNT(*) FROM CIRCUITS
UNION ALL
SELECT 'DRIVERS', COUNT(*) FROM DRIVERS
UNION ALL
SELECT 'CONSTRUCTORS', COUNT(*) FROM CONSTRUCTORS
UNION ALL
SELECT 'RESULTS', COUNT(*) FROM RESULTS
UNION ALL
SELECT 'QUALIFYING', COUNT(*) FROM QUALIFYING
UNION ALL
SELECT 'LAP_TIMES', COUNT(*) FROM LAP_TIMES
UNION ALL
SELECT 'PIT_STOPS', COUNT(*) FROM PIT_STOPS
UNION ALL
SELECT 'STATUS', COUNT(*) FROM STATUS;
