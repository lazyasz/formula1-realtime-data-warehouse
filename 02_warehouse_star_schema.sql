-- ============================================================================
-- 02_WAREHOUSE_STAR_SCHEMA.SQL: DIMENSIONAL STAR SCHEMA LAYER (2011+)
-- ============================================================================
-- Project: Formula 1 Race Winner Prediction (Data Warehousing & Data Mining)
-- Schema: F1_DM.ANALYTICS
-- Grain: One row per driver per Grand Prix (2011-2024 modern telemetry era)
-- ============================================================================

USE DATABASE F1_DM;
USE SCHEMA F1_DM.ANALYTICS;
USE WAREHOUSE F1_WH;

-- 1. CONFORMED DIMENSIONAL VIEWS
CREATE OR REPLACE VIEW DIM_DRIVER AS
SELECT 
    driverId,
    driverRef,
    code AS driver_code,
    forename || ' ' || surname AS driver_name,
    nationality AS driver_nationality,
    dob
FROM F1_DM.RAW.DRIVERS;

CREATE OR REPLACE VIEW DIM_CONSTRUCTOR AS
SELECT 
    constructorId,
    constructorRef,
    name AS team_name,
    nationality AS constructor_nationality
FROM F1_DM.RAW.CONSTRUCTORS;

CREATE OR REPLACE VIEW DIM_CIRCUIT AS
SELECT 
    c.circuitId,
    c.circuitRef,
    c.name AS circuit_name,
    c.location AS circuit_location,
    c.country AS circuit_country,
    c.lat,
    c.lng,
    c.alt
FROM F1_DM.RAW.CIRCUITS c;

-- 2. FACT_RACE_ENTRY: FACT TABLE FOR DRIVER RACE PERFORMANCE (2011+)
-- Note: Filtered to year >= 2011 because official FIA pit stop telemetry begins in 2011.
CREATE OR REPLACE TABLE FACT_RACE_ENTRY AS
SELECT 
    r.raceId,
    ra.year,
    ra.round,
    ra.name AS race_name,
    ra.date,
    ra.circuitId,
    r.driverId,
    r.constructorId,
    r.grid,
    r.positionOrder,
    r.points,
    -- PRIMARY BINARY TARGET LABEL
    IFF(r.positionOrder = 1, 1, 0) AS is_winner,
    -- SECONDARY MULTI-CLASS TARGET LABEL
    CASE 
        WHEN r.positionOrder = 1 THEN 'WIN'
        WHEN r.positionOrder <= 3 THEN 'PODIUM'
        WHEN r.positionOrder <= 10 THEN 'POINTS'
        ELSE 'NO_POINTS'
    END AS result_class,
    -- RELIABILITY DNF PROXY FLAG
    IFF(s.status = 'Finished' OR s.status LIKE '+%', 0, 1) AS dnf,
    r.fastestLapSpeed,
    r.milliseconds AS race_time_ms
FROM F1_DM.RAW.RESULTS r
JOIN F1_DM.RAW.RACES ra ON ra.raceId = r.raceId
JOIN F1_DM.RAW.STATUS s ON s.statusId = r.statusId
WHERE ra.year >= 2011
ORDER BY ra.date ASC, r.positionOrder ASC;

-- 3. INTEGRITY & DATA GRAIN CHECKS
SELECT 
    COUNT(*) AS total_entries,
    COUNT(DISTINCT raceId) AS total_races,
    MIN(year) AS min_season,
    MAX(year) AS max_season,
    SUM(is_winner) AS total_winners,
    ROUND(AVG(is_winner) * 100, 2) AS winner_prevalence_pct,
    COUNT(CASE WHEN result_class = 'PODIUM' THEN 1 END) AS total_podiums,
    COUNT(CASE WHEN result_class = 'POINTS' THEN 1 END) AS total_points_finishes,
    COUNT(CASE WHEN dnf = 1 THEN 1 END) AS total_dnfs
FROM FACT_RACE_ENTRY;
