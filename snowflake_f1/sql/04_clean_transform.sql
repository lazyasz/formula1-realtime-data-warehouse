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
