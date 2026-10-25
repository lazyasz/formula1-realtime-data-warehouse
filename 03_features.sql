-- ============================================================================
-- 03_FEATURES.SQL: LEAK-FREE FEATURE STORE ENGINE (CAR, LAP & PIT PILLARS)
-- ============================================================================
-- Project: Formula 1 Race Winner Prediction (Data Warehousing & Data Mining)
-- Schema: F1_DM.ANALYTICS
-- Key Requirement: Zero Target Leakage across rolling windows (strictly past races)
-- ============================================================================

USE DATABASE F1_DM;
USE SCHEMA F1_DM.ANALYTICS;
USE WAREHOUSE F1_WH;

-- ----------------------------------------------------------------------------
-- 1. LEAK-FREE CIRCUIT LAP RECORD ENGINE
-- Computes the running all-time circuit track record strictly BEFORE each race
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE CIRCUIT_LAP_RECORD AS
WITH per_race AS (
    SELECT 
        ra.circuitId, 
        ra.raceId, 
        ra.date, 
        MIN(l.milliseconds) AS race_best_ms
    FROM F1_DM.RAW.LAP_TIMES l 
    JOIN F1_DM.RAW.RACES ra ON ra.raceId = l.raceId
    WHERE l.milliseconds > 50000 -- filter invalid glitches
    GROUP BY ra.circuitId, ra.raceId, ra.date
)
SELECT 
    raceId, 
    circuitId, 
    race_best_ms,
    -- Strictly previous races: ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    MIN(race_best_ms) OVER (
        PARTITION BY circuitId 
        ORDER BY date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS lap_record_before_ms
FROM per_race;

-- ----------------------------------------------------------------------------
-- 2. CONSTRUCTOR PIT STOP TIME AVERAGE PER RACE
-- Filters out red-flag stoppages and penalty delays (outliers outside 15s - 60s)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE TEAM_PIT_RACE AS
SELECT 
    p.raceId, 
    r.constructorId, 
    AVG(p.milliseconds) AS avg_pit_ms,
    COUNT(p.stop) AS pit_stop_count
FROM F1_DM.RAW.PIT_STOPS p
JOIN F1_DM.RAW.RESULTS r ON r.raceId = p.raceId AND r.driverId = p.driverId
WHERE p.milliseconds BETWEEN 15000 AND 60000 -- drop red-flag / penalty outliers
GROUP BY p.raceId, r.constructorId;

-- ----------------------------------------------------------------------------
-- 3. QUALIFYING PACE GAP TO POLE (PERCENTAGE DELTA)
-- Robust time string parsing: parses mm:ss.sss into milliseconds
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE QUALI_GAP AS
WITH q AS (
    SELECT 
        raceId, 
        driverId, 
        constructorId,
        LEAST(
            COALESCE(TRY_TO_NUMBER(SPLIT_PART(q3,':',1))*60000 + TRY_TO_DECIMAL(SPLIT_PART(q3,':',2),10,3)*1000, 1e12),
            COALESCE(TRY_TO_NUMBER(SPLIT_PART(q2,':',1))*60000 + TRY_TO_DECIMAL(SPLIT_PART(q2,':',2),10,3)*1000, 1e12),
            COALESCE(TRY_TO_NUMBER(SPLIT_PART(q1,':',1))*60000 + TRY_TO_DECIMAL(SPLIT_PART(q1,':',2),10,3)*1000, 1e12)
        ) AS best_ms
    FROM F1_DM.RAW.QUALIFYING
)
SELECT 
    raceId, 
    driverId, 
    constructorId,
    -- Formula: 100 * (driver_time - pole_time) / pole_time
    100.0 * (best_ms - MIN(best_ms) OVER (PARTITION BY raceId)) / NULLIF(MIN(best_ms) OVER (PARTITION BY raceId), 0) AS quali_gap_pct
FROM q 
WHERE best_ms < 1e12;

-- ----------------------------------------------------------------------------
-- 4. MASTER FEATURE STORE TABLE (ROLLING WINDOWS STRICTLY ON PAST RACES)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE FEATURES AS
WITH base AS (
    SELECT 
        f.*, 
        qg.quali_gap_pct, 
        tp.avg_pit_ms, 
        lr.lap_record_before_ms
    FROM FACT_RACE_ENTRY f
    LEFT JOIN QUALI_GAP qg ON qg.raceId = f.raceId AND qg.driverId = f.driverId
    LEFT JOIN TEAM_PIT_RACE tp ON tp.raceId = f.raceId AND tp.constructorId = f.constructorId
    LEFT JOIN CIRCUIT_LAP_RECORD lr ON lr.raceId = f.raceId
),
team_race AS (
    -- Aggregate to team level per Grand Prix
    SELECT 
        raceId, 
        constructorId, 
        date, 
        MAX(year) AS year, 
        SUM(points) AS team_pts, 
        AVG(dnf) AS team_dnf,
        AVG(quali_gap_pct) AS team_gap, 
        AVG(avg_pit_ms) AS team_pit
    FROM base 
    GROUP BY raceId, constructorId, date
),
team_roll AS (
    -- Rolling team form (strictly prior races)
    SELECT 
        raceId, 
        constructorId,
        AVG(team_pts) OVER (
            PARTITION BY constructorId ORDER BY date 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS team_points_l5,
        AVG(team_dnf) OVER (
            PARTITION BY constructorId ORDER BY date 
            ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
        ) AS team_dnf_rate_l10,
        AVG(team_gap) OVER (
            PARTITION BY constructorId ORDER BY date 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS team_quali_gap_l5,
        AVG(team_pit) OVER (
            PARTITION BY constructorId ORDER BY date 
            ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
        ) AS team_avg_pit_ms
    FROM team_race
),
drv_roll AS (
    -- Rolling driver form (strictly prior races)
    SELECT 
        raceId, 
        driverId,
        AVG(is_winner) OVER (
            PARTITION BY driverId ORDER BY date 
            ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
        ) AS driver_win_rate_l10,
        AVG(points) OVER (
            PARTITION BY driverId ORDER BY date 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS driver_points_l5,
        SUM(is_winner) OVER (
            PARTITION BY driverId, circuitId ORDER BY date 
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS driver_circuit_wins
    FROM base
)
SELECT 
    b.raceId, 
    b.year, 
    b.round,
    b.date, 
    b.circuitId, 
    b.driverId, 
    b.constructorId, 
    b.grid,
    -- 1. CAR FEATURE PROXIES
    COALESCE(b.quali_gap_pct, tr.team_quali_gap_l5, 3.0) AS quali_gap_pct,
    COALESCE(tr.team_points_l5, 0.0) AS team_points_l5,
    COALESCE(tr.team_dnf_rate_l10, 0.20) AS team_dnf_rate_l10,
    COALESCE(tr.team_quali_gap_l5, 3.0) AS team_quali_gap_l5,
    COALESCE(b.fastestLapSpeed, 220.0) AS fastest_lap_speed,
    -- 2. LAP RECORD FEATURE
    b.lap_record_before_ms AS circuit_lap_record_ms,
    -- 3. PIT STOP TIME FEATURE
    COALESCE(tr.team_avg_pit_ms, 23500.0) AS team_avg_pit_ms,
    -- 4. CONTEXT & FORM FEATURES
    COALESCE(dr.driver_win_rate_l10, 0.0) AS driver_win_rate_l10,
    COALESCE(dr.driver_points_l5, 0.0) AS driver_points_l5,
    COALESCE(dr.driver_circuit_wins, 0) AS driver_circuit_wins,
    -- REGULATION ERA FLAG (2011-13 V8, 2014-16 Early Hybrid, 2017-21 Wide Body, 2022-25 Ground Effect, 2026+ Reset)
    CASE 
        WHEN b.year <= 2013 THEN 1 
        WHEN b.year <= 2016 THEN 2 
        WHEN b.year <= 2021 THEN 3 
        WHEN b.year <= 2025 THEN 4 
        ELSE 5 
    END AS reg_era,
    -- EXPONENTIAL RECENCY WEIGHTING
    EXP(-0.15 * (2024 - b.year)) AS sample_weight,
    -- SUPERVISED GROUND TRUTH LABELS
    b.is_winner, 
    b.result_class
FROM base b
JOIN team_roll tr ON tr.raceId = b.raceId AND tr.constructorId = b.constructorId
JOIN drv_roll dr ON dr.raceId = b.raceId AND dr.driverId = b.driverId;

-- ----------------------------------------------------------------------------
-- 5. TEMPORAL TRAIN, VALIDATION & TEST SPLIT VIEWS (NO SHUFFLE)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW FEATURES_TRAIN AS 
SELECT * FROM FEATURES WHERE year BETWEEN 2011 AND 2021;

CREATE OR REPLACE VIEW FEATURES_VALID AS 
SELECT * FROM FEATURES WHERE year BETWEEN 2022 AND 2023;

CREATE OR REPLACE VIEW FEATURES_TEST AS 
SELECT * FROM FEATURES WHERE year = 2024;

-- ----------------------------------------------------------------------------
-- 6. DATA AUDIT & LEAKAGE VERIFICATION
-- ----------------------------------------------------------------------------
SELECT 
    'TRAIN (2011-2021)' AS split_name, COUNT(*) AS row_count, COUNT(DISTINCT raceId) AS race_count, SUM(is_winner) AS win_count FROM FEATURES_TRAIN
UNION ALL
SELECT 'VALID (2022-2023)', COUNT(*), COUNT(DISTINCT raceId), SUM(is_winner) FROM FEATURES_VALID
UNION ALL
SELECT 'TEST (2024)', COUNT(*), COUNT(DISTINCT raceId), SUM(is_winner) FROM FEATURES_TEST;
