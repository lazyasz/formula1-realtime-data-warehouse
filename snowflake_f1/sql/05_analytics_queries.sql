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
