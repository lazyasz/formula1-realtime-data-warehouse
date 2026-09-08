-- =============================================================================
-- FORMULA 1 RACE PERFORMANCE DATA WAREHOUSE — 12 CORE OLAP QUERIES
-- Comprehensive Suite: Roll-Up, Drill-Down, Slice, Dice, Pivot, Window Ranking,
-- Pit Stop Strategy, Pole Conversion, DNF Reliability & Altitude Analytics.
-- Calibrated for the Official 2004-2024 F1 Master Data Warehouse (8,650 records).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- QUERY 1: OLAP ROLL-UP (Hierarchical Aggregation: Race -> Month -> Quarter -> Season)
-- Aggregates driver points, podiums, and wins up the calendar hierarchy.
-- -----------------------------------------------------------------------------
SELECT 
    d.year AS season_year,
    d.quarter,
    d.month_name,
    drv.driver_name,
    COUNT(f.result_id) AS total_races,
    SUM(f.is_win) AS total_wins,
    SUM(f.is_podium) AS total_podiums,
    ROUND(SUM(f.race_points), 2) AS total_points,
    ROUND(AVG(f.finish_position), 2) AS avg_finish_pos
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_DATE d ON f.date_id = d.date_id
JOIN DIM_DRIVER drv ON f.driver_id = drv.driver_id
WHERE d.year = 2024
GROUP BY d.year, d.quarter, d.month_name, drv.driver_name
HAVING SUM(f.race_points) > 15
ORDER BY d.quarter, d.month_name, total_points DESC;

-- -----------------------------------------------------------------------------
-- QUERY 2: OLAP DRILL-DOWN (Constructor Season Overview -> Circuit Specifics -> Driver Contribution)
-- Drills down from team season total to specific Grand Prix circuits and driver shares.
-- -----------------------------------------------------------------------------
SELECT 
    r.season_year,
    c.constructor_name,
    r.race_name,
    r.circuit_name,
    drv.driver_name,
    f.grid_position,
    f.finish_position,
    f.race_points,
    f.fastest_lap_speed
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
JOIN DIM_DRIVER drv ON f.driver_id = drv.driver_id
WHERE r.season_year = 2024 AND c.constructor_name IN ('Red Bull', 'McLaren', 'Ferrari', 'Mercedes')
ORDER BY r.round, c.constructor_name, f.finish_position;

-- -----------------------------------------------------------------------------
-- QUERY 3: OLAP SLICE (1-Dimensional Filtering: European Historic Circuits Slice)
-- Slices data exclusively for European races (Silverstone, Monza, Spa, Monaco, Catalunya, Red Bull Ring).
-- -----------------------------------------------------------------------------
SELECT 
    r.circuit_name,
    r.circuit_country,
    drv.driver_name,
    c.constructor_name,
    COUNT(*) AS races_participated,
    SUM(f.is_win) AS european_wins,
    SUM(f.is_podium) AS european_podiums,
    ROUND(SUM(f.race_points), 1) AS total_european_points,
    ROUND(AVG(f.race_completion_pct) * 100, 2) AS avg_completion_pct
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
JOIN DIM_DRIVER drv ON f.driver_id = drv.driver_id
JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
WHERE r.circuit_country IN ('UK', 'Italy', 'Belgium', 'Monaco', 'Spain', 'Austria')
GROUP BY r.circuit_name, r.circuit_country, drv.driver_name, c.constructor_name
HAVING SUM(f.race_points) >= 50
ORDER BY total_european_points DESC;

-- -----------------------------------------------------------------------------
-- QUERY 4: OLAP DICE (Multi-Dimensional Sub-Cube Filtering)
-- Dices: Seasons (2021, 2022, 2023, 2024) x Top 4 Constructors x Top-3 Qualifying Grid Starts.
-- -----------------------------------------------------------------------------
SELECT 
    r.season_year,
    c.constructor_name,
    drv.driver_name,
    COUNT(*) AS front_row_starts,
    SUM(f.is_win) AS wins_from_front_rows,
    SUM(f.is_podium) AS podiums_from_front_rows,
    ROUND(AVG(f.position_gain), 2) AS avg_position_delta,
    ROUND(SUM(f.race_points), 1) AS total_points_scored
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
JOIN DIM_DRIVER drv ON f.driver_id = drv.driver_id
WHERE r.season_year IN (2021, 2022, 2023, 2024)
  AND c.constructor_name IN ('Red Bull', 'Ferrari', 'Mercedes', 'McLaren')
  AND f.grid_position <= 3
GROUP BY r.season_year, c.constructor_name, drv.driver_name
HAVING COUNT(*) >= 5
ORDER BY r.season_year DESC, total_points_scored DESC;

-- -----------------------------------------------------------------------------
-- QUERY 5: OLAP PIVOT / CROSSTAB (Constructors x Multi-Era Points Matrix)
-- Pivots across championship eras (2008 V8 Era, 2014 Hybrid Dawn, 2021 Title Fight, 2024 Ground Effect).
-- -----------------------------------------------------------------------------
SELECT 
    c.constructor_name,
    ROUND(SUM(CASE WHEN r.season_year = 2008 THEN f.race_points ELSE 0 END), 1) AS pts_2008,
    ROUND(SUM(CASE WHEN r.season_year = 2014 THEN f.race_points ELSE 0 END), 1) AS pts_2014,
    ROUND(SUM(CASE WHEN r.season_year = 2021 THEN f.race_points ELSE 0 END), 1) AS pts_2021,
    ROUND(SUM(CASE WHEN r.season_year = 2024 THEN f.race_points ELSE 0 END), 1) AS pts_2024,
    ROUND(SUM(f.race_points), 1) AS grand_total_points_2004_2024,
    SUM(f.is_win) AS total_era_wins
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
GROUP BY c.constructor_name
HAVING SUM(f.race_points) > 500
ORDER BY grand_total_points_2004_2024 DESC;

-- -----------------------------------------------------------------------------
-- QUERY 6: WINDOW FUNCTION & DENSE RANKING (Driver Championship Standings Per Season)
-- Ranks drivers within each championship season using DENSE_RANK() over total points.
-- -----------------------------------------------------------------------------
WITH DriverSeasonTotals AS (
    SELECT 
        r.season_year,
        drv.driver_name,
        c.constructor_name,
        SUM(f.race_points) AS total_season_points,
        SUM(f.is_win) AS season_wins,
        SUM(f.is_podium) AS season_podiums,
        COUNT(f.result_id) AS total_races_entered
    FROM FACT_RACE_RESULTS_STAR f
    JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
    JOIN DIM_DRIVER drv ON f.driver_id = drv.driver_id
    JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
    GROUP BY r.season_year, drv.driver_name, c.constructor_name
)
SELECT 
    season_year,
    DENSE_RANK() OVER (PARTITION BY season_year ORDER BY total_season_points DESC, season_wins DESC) AS championship_rank,
    driver_name,
    constructor_name,
    total_season_points,
    season_wins,
    season_podiums,
    ROUND(total_season_points / total_races_entered, 2) AS points_per_race
FROM DriverSeasonTotals
WHERE season_year IN (2008, 2014, 2021, 2024)
ORDER BY season_year DESC, championship_rank ASC;

-- -----------------------------------------------------------------------------
-- QUERY 7: PIT STOP STRATEGY & OVERTAKE EFFICIENCY (Pit Metrics vs Position Delta)
-- Evaluates pit stop execution count and average pit duration against positions gained.
-- -----------------------------------------------------------------------------
SELECT 
    f.pit_stop_count,
    COUNT(f.result_id) AS total_race_instances,
    ROUND(AVG(f.total_pit_duration_sec), 2) AS avg_total_pit_sec,
    ROUND(AVG(f.fastest_pit_duration_sec), 2) AS avg_fastest_pit_stop,
    ROUND(AVG(f.position_gain), 2) AS avg_positions_gained,
    ROUND(AVG(f.race_points), 2) AS avg_points_earned,
    SUM(f.is_podium) AS total_podiums_achieved
FROM FACT_RACE_RESULTS_STAR f
WHERE f.is_dnf = 0
GROUP BY f.pit_stop_count
ORDER BY f.pit_stop_count ASC;

-- -----------------------------------------------------------------------------
-- QUERY 8: POLE-TO-WIN CONVERSION RATE ANALYSIS
-- Calculates conversion percentage of Pole Positions (Grid 1) into Race Wins (Finish 1).
-- -----------------------------------------------------------------------------
SELECT 
    drv.driver_name,
    c.constructor_name,
    SUM(f.is_pole) AS total_pole_positions,
    SUM(CASE WHEN f.is_pole = 1 AND f.is_win = 1 THEN 1 ELSE 0 END) AS pole_and_win_conversions,
    ROUND(
        (SUM(CASE WHEN f.is_pole = 1 AND f.is_win = 1 THEN 1.0 ELSE 0.0 END) / 
         NULLIF(SUM(f.is_pole), 0)) * 100.0, 
    2) AS pole_to_win_conversion_pct,
    ROUND(AVG(CASE WHEN f.is_pole = 1 THEN f.finish_position ELSE NULL END), 2) AS avg_finish_from_pole
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_DRIVER drv ON f.driver_id = drv.driver_id
JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
GROUP BY drv.driver_name, c.constructor_name
HAVING SUM(f.is_pole) >= 10
ORDER BY total_pole_positions DESC, pole_to_win_conversion_pct DESC;

-- -----------------------------------------------------------------------------
-- QUERY 9: RELIABILITY & DNF CAUSE BREAKDOWN (Failure Categorization)
-- Analyzes non-finishing mechanical and collision reasons across top constructors.
-- -----------------------------------------------------------------------------
SELECT 
    s.status_description AS dnf_cause,
    c.constructor_name,
    COUNT(f.result_id) AS incident_count,
    ROUND(AVG(f.driver_age_years), 1) AS avg_driver_age,
    ROUND(AVG(f.race_laps), 1) AS avg_laps_completed_before_failure
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_STATUS s ON f.status_id = s.status_id
JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
WHERE f.is_dnf = 1 AND s.status_description NOT LIKE '+%'
GROUP BY s.status_description, c.constructor_name
HAVING COUNT(f.result_id) >= 5
ORDER BY incident_count DESC;

-- -----------------------------------------------------------------------------
-- QUERY 10: CUMULATIVE CONSTRUCTOR DOMINANCE & MOVING AVERAGE
-- Tracks running team score and point trajectories across race rounds.
-- -----------------------------------------------------------------------------
SELECT 
    r.season_year,
    r.round,
    r.race_name,
    c.constructor_name,
    SUM(f.race_points) AS round_points,
    MAX(f.constructor_standing_points) AS cumulative_season_points,
    ROUND(AVG(SUM(f.race_points)) OVER (
        PARTITION BY r.season_year, c.constructor_name 
        ORDER BY r.round 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3race_avg_points
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
WHERE r.season_year = 2024 AND c.constructor_name IN ('Red Bull', 'McLaren', 'Ferrari', 'Mercedes')
GROUP BY r.season_year, r.round, r.race_name, c.constructor_name
ORDER BY r.season_year, r.round, cumulative_season_points DESC;

-- -----------------------------------------------------------------------------
-- QUERY 11: CIRCUIT ELEVATION & HIGH-ALTITUDE PERFORMANCE CORRELATION
-- Analyzes engine/cooling performance variance across altitude tiers (<50m, 50-300m, >500m).
-- -----------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN r.circuit_altitude_m < 50 THEN 'Low Altitude (< 50m)'
        WHEN r.circuit_altitude_m BETWEEN 50 AND 300 THEN 'Mid Altitude (50m - 300m)'
        ELSE 'High Altitude (> 300m - Mexico/Austria/Spa)'
    END AS altitude_category,
    COUNT(DISTINCT r.circuit_name) AS circuit_count,
    COUNT(f.result_id) AS race_entries,
    ROUND(AVG(f.fastest_lap_speed), 2) AS avg_fastest_lap_speed_kmh,
    ROUND(AVG(f.total_pit_duration_sec), 2) AS avg_pit_duration_sec,
    SUM(f.is_dnf) AS total_dnfs,
    ROUND((SUM(f.is_dnf) * 1.0 / COUNT(f.result_id)) * 100.0, 2) AS dnf_rate_pct
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
GROUP BY altitude_category
ORDER BY avg_fastest_lap_speed_kmh DESC;

-- -----------------------------------------------------------------------------
-- QUERY 12: QUALIFYING-TO-FINISH DELTA & OVERTAKING MASTERY
-- Highlights drivers who consistently improve upon their qualifying grid position.
-- -----------------------------------------------------------------------------
SELECT 
    drv.driver_name,
    COUNT(f.result_id) AS total_races,
    ROUND(AVG(f.grid_position), 2) AS avg_grid_position,
    ROUND(AVG(f.finish_position), 2) AS avg_finish_position,
    ROUND(AVG(f.position_gain), 2) AS net_avg_positions_gained,
    SUM(CASE WHEN f.position_gain > 0 THEN 1 ELSE 0 END) AS races_gained_places,
    ROUND((SUM(CASE WHEN f.position_gain > 0 THEN 1.0 ELSE 0.0 END) / COUNT(f.result_id)) * 100, 2) AS gain_consistency_pct
FROM FACT_RACE_RESULTS_STAR f
JOIN DIM_DRIVER drv ON f.driver_id = drv.driver_id
WHERE f.is_dnf = 0
GROUP BY drv.driver_name
HAVING COUNT(f.result_id) >= 50
ORDER BY net_avg_positions_gained DESC;
