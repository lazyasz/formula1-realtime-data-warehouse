-- ============================================================================
-- 05_DASHBOARD_VIEWS.SQL: ANALYTICAL VIEWS FOR STREAMLIT IN SNOWFLAKE
-- ============================================================================
-- Project: Formula 1 Race Winner Prediction (Data Warehousing & Data Mining)
-- Schema: F1_DM.ANALYTICS
-- ============================================================================

USE DATABASE F1_DM;
USE SCHEMA F1_DM.ANALYTICS;
USE WAREHOUSE F1_WH;

-- 1. V_TOP_PICKS: ENRICHED PREDICTIONS WITH DRIVER & CONSTRUCTOR NAMES
CREATE OR REPLACE VIEW V_TOP_PICKS AS
SELECT 
    p.race_name, 
    p.year, 
    p.split,
    d.driver_name, 
    d.driver_code,
    c.team_name, 
    p.win_prob, 
    p.predicted_rank
FROM F1_DM.ANALYTICS.PREDICTIONS p 
JOIN F1_DM.ANALYTICS.DIM_DRIVER d ON p.driverId = d.driverId 
JOIN F1_DM.ANALYTICS.DIM_CONSTRUCTOR c ON p.constructorId = c.constructorId;

-- 2. V_TEAM_PROB: AGGREGATE TEAM / CONSTRUCTOR WIN PROBABILITIES
CREATE OR REPLACE VIEW V_TEAM_PROB AS
SELECT 
    race_name, 
    year, 
    split,
    team_name, 
    SUM(win_prob) AS team_win_prob,
    RANK() OVER (PARTITION BY race_name, year, split ORDER BY SUM(win_prob) DESC) AS team_predicted_rank
FROM V_TOP_PICKS 
GROUP BY race_name, year, split, team_name;

-- 3. V_LAP_RECORD: CIRCUIT OFFICIAL RACE BEST LAP RECORDS IN SECONDS
CREATE OR REPLACE VIEW V_LAP_RECORD AS
SELECT 
    ci.circuit_name, 
    ci.circuit_country,
    ROUND(MIN(lr.race_best_ms) / 1000.0, 3) AS lap_record_s
FROM F1_DM.ANALYTICS.CIRCUIT_LAP_RECORD lr 
JOIN F1_DM.ANALYTICS.DIM_CIRCUIT ci ON lr.circuitId = ci.circuitId 
GROUP BY ci.circuit_name, ci.circuit_country;

-- 4. V_PIT_BY_TEAM: HISTORICAL PIT STOP EXECUTION SECONDS BY TEAM
CREATE OR REPLACE VIEW V_PIT_BY_TEAM AS
SELECT 
    f.year, 
    c.team_name, 
    ROUND(AVG(tp.avg_pit_ms) / 1000.0, 3) AS avg_pit_s,
    COUNT(tp.raceId) AS races_stints_recorded
FROM F1_DM.ANALYTICS.TEAM_PIT_RACE tp 
JOIN F1_DM.ANALYTICS.FACT_RACE_ENTRY f ON f.raceId = tp.raceId AND f.constructorId = tp.constructorId
JOIN F1_DM.ANALYTICS.DIM_CONSTRUCTOR c ON c.constructorId = tp.constructorId 
GROUP BY f.year, c.team_name;
