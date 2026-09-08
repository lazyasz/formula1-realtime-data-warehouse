-- PostgreSQL DDL script for F1 Race Performance Data Warehouse
-- NOTE: This file implements the Star Schema by default.
-- For the explicit Star and Snowflake implementations, please reference:
-- 1. Star Schema: create_star_schema.sql (DIM_CIRCUIT merged into DIM_RACE)
-- 2. Snowflake Schema: create_snowflake_schema.sql (DIM_CIRCUIT normalized out of DIM_RACE)

BEGIN;

--------------------------------------------------------------------------------
-- 1. DROP EXISTING TABLES (FOR IDEMPOTENT EXECUTION)
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS FACT_RACE_RESULTS CASCADE;
DROP TABLE IF EXISTS DIM_DATE CASCADE;
DROP TABLE IF EXISTS DIM_STATUS CASCADE;
DROP TABLE IF EXISTS DIM_RACE CASCADE;
DROP TABLE IF EXISTS DIM_CONSTRUCTOR CASCADE;
DROP TABLE IF EXISTS DIM_DRIVER CASCADE;

--------------------------------------------------------------------------------
-- 2. CREATE DIMENSION TABLES (Star Schema - Circuit denormalized into Race)
--------------------------------------------------------------------------------

-- DIM_DRIVER: Details of drivers participating in F1
CREATE TABLE DIM_DRIVER (
    driver_id INT PRIMARY KEY,
    driver_ref VARCHAR(50) NOT NULL UNIQUE,
    driver_code VARCHAR(3),
    driver_name VARCHAR(100) NOT NULL,
    driver_dob DATE,
    driver_nationality VARCHAR(50)
);

-- DIM_CONSTRUCTOR: Details of constructors/teams participating in F1
CREATE TABLE DIM_CONSTRUCTOR (
    constructor_id INT PRIMARY KEY,
    constructor_ref VARCHAR(50) NOT NULL UNIQUE,
    constructor_name VARCHAR(100) NOT NULL,
    constructor_nationality VARCHAR(50)
);

-- DIM_RACE: Details of races scheduled across seasons (includes denormalized Circuit details)
CREATE TABLE DIM_RACE (
    race_id INT PRIMARY KEY,
    season_year INT NOT NULL,
    round INT NOT NULL,
    race_name VARCHAR(100) NOT NULL,
    race_date DATE NOT NULL,
    race_start_time TIME,
    
    -- Denormalized Circuit Attributes (Merged from DIM_CIRCUIT to form a flat Star Schema)
    circuit_id INT NOT NULL,
    circuit_name VARCHAR(150) NOT NULL,
    circuit_location VARCHAR(100),
    circuit_country VARCHAR(100),
    circuit_latitude DECIMAL(9,6),
    circuit_longitude DECIMAL(9,6),
    circuit_altitude_m INT,
    
    CONSTRAINT uq_race_season_round UNIQUE (season_year, round)
);

-- DIM_STATUS: Map of status descriptions (Finished, DNF reasons, etc.)
CREATE TABLE DIM_STATUS (
    status_id SERIAL PRIMARY KEY,
    status_description VARCHAR(100) NOT NULL UNIQUE
);

-- DIM_DATE: Calendar date dimension for time-slice analysis
CREATE TABLE DIM_DATE (
    date_id INT PRIMARY KEY, -- Format: YYYYMMDD
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name VARCHAR(20) NOT NULL,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    day_name VARCHAR(20) NOT NULL
);

--------------------------------------------------------------------------------
-- 3. CREATE FACT TABLE
--------------------------------------------------------------------------------

-- FACT_RACE_RESULTS: Central fact table storing results, qualifying, pit summaries,
-- standings and indicators. Links directly to all 5 flat dimensions.
CREATE TABLE FACT_RACE_RESULTS (
    result_id SERIAL PRIMARY KEY,
    race_id INT NOT NULL REFERENCES DIM_RACE(race_id),
    driver_id INT NOT NULL REFERENCES DIM_DRIVER(driver_id),
    constructor_id INT NOT NULL REFERENCES DIM_CONSTRUCTOR(constructor_id),
    date_id INT NOT NULL REFERENCES DIM_DATE(date_id),
    status_id INT NOT NULL REFERENCES DIM_STATUS(status_id),
    
    -- Race Performance Metrics
    car_number INT,
    grid_position INT NOT NULL,
    qualifying_position INT,
    qualifying_best_time_sec DECIMAL(6,3),
    finish_position INT, -- NULL if DNF
    finish_position_text VARCHAR(10),
    race_points DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    race_laps INT NOT NULL,
    race_time VARCHAR(20),
    race_milliseconds BIGINT,
    
    -- Fastest Lap & Pit Stop Summary Metrics
    fastest_lap_number INT,
    fastest_lap_rank INT,
    fastest_lap_time VARCHAR(20),
    fastest_lap_speed DECIMAL(6,3),
    pit_stop_count INT NOT NULL DEFAULT 0,
    total_pit_duration_sec DECIMAL(7,3) NOT NULL DEFAULT 0.000,
    avg_pit_duration_sec DECIMAL(6,3) NOT NULL DEFAULT 0.000,
    fastest_pit_duration_sec DECIMAL(6,3) NOT NULL DEFAULT 0.000,
    last_pit_lap INT NOT NULL DEFAULT 0,
    
    -- Lap timing aggregates
    laps_recorded INT NOT NULL DEFAULT 0,
    fastest_recorded_lap_ms INT,
    average_lap_ms INT,
    
    -- Standings & Championship Metrics (Cumulative up to this race)
    driver_standing_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    driver_championship_position INT,
    driver_championship_wins INT NOT NULL DEFAULT 0,
    constructor_standing_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    constructor_championship_position INT,
    constructor_championship_wins INT NOT NULL DEFAULT 0,
    constructor_race_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    driver_standing_gap_to_leader DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    constructor_standing_gap_to_leader DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    
    -- Sprint & Positioning Deltas
    sprint_position INT,
    sprint_points DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    position_gain INT,
    qualifying_to_finish_delta INT,
    
    -- Indicators & Derived metrics
    is_pole INT NOT NULL CHECK (is_pole IN (0, 1)),
    is_podium INT NOT NULL CHECK (is_podium IN (0, 1)),
    is_win INT NOT NULL CHECK (is_win IN (0, 1)),
    is_top_10 INT NOT NULL CHECK (is_top_10 IN (0, 1)),
    is_dnf INT NOT NULL CHECK (is_dnf IN (0, 1)),
    points_per_lap DECIMAL(6,4),
    race_completion_pct DECIMAL(5,4),
    driver_age_years DECIMAL(5,2),
    
    CONSTRAINT uq_race_driver UNIQUE (race_id, driver_id)
);

--------------------------------------------------------------------------------
-- 4. CREATE INDEXES ON FOREIGN KEYS & COMMON QUERY COLUMNS
--------------------------------------------------------------------------------

-- Dimension Indexes
CREATE INDEX idx_dim_race_season ON DIM_RACE(season_year);

-- FACT_RACE_RESULTS Indexes
CREATE INDEX idx_fact_results_race ON FACT_RACE_RESULTS(race_id);
CREATE INDEX idx_fact_results_driver ON FACT_RACE_RESULTS(driver_id);
CREATE INDEX idx_fact_results_constructor ON FACT_RACE_RESULTS(constructor_id);
CREATE INDEX idx_fact_results_date ON FACT_RACE_RESULTS(date_id);
CREATE INDEX idx_fact_results_status ON FACT_RACE_RESULTS(status_id);

-- Performance Composite Indexes
CREATE INDEX idx_fact_results_season_driver ON FACT_RACE_RESULTS(race_id, driver_id);

COMMIT;
