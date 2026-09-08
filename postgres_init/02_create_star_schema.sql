-- =============================================================================
-- FORMULA 1 DATA WAREHOUSE — SERVING STAR SCHEMA (PostgreSQL DDL for Grafana)
-- =============================================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS fact_lap_times CASCADE;
DROP TABLE IF EXISTS fact_race_results CASCADE;
DROP TABLE IF EXISTS dim_driver CASCADE;
DROP TABLE IF EXISTS dim_team CASCADE;
DROP TABLE IF EXISTS dim_circuit CASCADE;
DROP TABLE IF EXISTS dim_race CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_session CASCADE;
DROP TABLE IF EXISTS dim_tyre_compound CASCADE;

-- 1. Dimension: Driver (Flat Dimension)
CREATE TABLE dim_driver (
    driver_id INT PRIMARY KEY,
    driver_ref VARCHAR(100) NOT NULL,
    driver_number INT,
    driver_code VARCHAR(3) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    driver_name VARCHAR(200) NOT NULL,
    dob DATE,
    nationality VARCHAR(50) NOT NULL,
    driver_age NUMERIC(5, 2)
);

-- 2. Dimension: Team / Constructor (Flat Dimension with Livery Colors)
CREATE TABLE dim_team (
    team_id INT PRIMARY KEY,
    constructor_ref VARCHAR(100) NOT NULL,
    team_name VARCHAR(150) NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    color_hex VARCHAR(7) NOT NULL,
    engine_supplier VARCHAR(100),
    team_principal VARCHAR(100),
    headquarters_country VARCHAR(100)
);

-- 3. Dimension: Circuit (Flat Dimension)
CREATE TABLE dim_circuit (
    circuit_id INT PRIMARY KEY,
    circuit_ref VARCHAR(100) NOT NULL,
    circuit_name VARCHAR(150) NOT NULL,
    location_city VARCHAR(100),
    circuit_country VARCHAR(100) NOT NULL,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    altitude_m INT,
    track_length_km NUMERIC(6, 3),
    total_corners INT
);

-- 4. Dimension: Race
CREATE TABLE dim_race (
    race_id INT PRIMARY KEY,
    season_year INT NOT NULL,
    round INT NOT NULL,
    race_name VARCHAR(150) NOT NULL,
    circuit_id INT NOT NULL REFERENCES dim_circuit(circuit_id),
    race_date DATE NOT NULL,
    total_race_laps INT NOT NULL
);

-- 5. Dimension: Calendar Date
CREATE TABLE dim_date (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN DEFAULT TRUE
);

-- 6. Dimension: Session
CREATE TABLE dim_session (
    session_id INT PRIMARY KEY,
    session_type VARCHAR(20) NOT NULL,
    session_name VARCHAR(50) NOT NULL
);

-- 7. Dimension: Tyre Compound
CREATE TABLE dim_tyre_compound (
    tyre_compound_id INT PRIMARY KEY,
    compound_name VARCHAR(50) NOT NULL,
    compound_code VARCHAR(10) NOT NULL,
    color_hex VARCHAR(7) NOT NULL
);

-- 8. Fact Table: Race Results (Grain: 1 row per driver per race)
CREATE TABLE fact_race_results (
    result_id SERIAL PRIMARY KEY,
    race_id INT NOT NULL REFERENCES dim_race(race_id),
    driver_id INT NOT NULL REFERENCES dim_driver(driver_id),
    team_id INT NOT NULL REFERENCES dim_team(team_id),
    circuit_id INT NOT NULL REFERENCES dim_circuit(circuit_id),
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    grid_position INT,
    finishing_position INT,
    points NUMERIC(6, 2) NOT NULL DEFAULT 0.0,
    laps_completed INT NOT NULL DEFAULT 0,
    fastest_lap_rank INT,
    fastest_lap_time_ms INT,
    avg_lap_time_ms INT,
    pit_stop_count INT DEFAULT 0,
    total_pit_time_ms INT DEFAULT 0,
    positions_gained INT DEFAULT 0,
    is_win INT DEFAULT 0,
    is_podium INT DEFAULT 0,
    is_pole INT DEFAULT 0,
    is_dnf INT DEFAULT 0,
    status_text VARCHAR(100) DEFAULT 'Finished',
    CONSTRAINT unq_fact_race_driver UNIQUE (race_id, driver_id)
);

-- 9. Fact Table: Lap Times & Telemetry (Grain: 1 row per driver per lap per session)
CREATE TABLE fact_lap_times (
    lap_id BIGSERIAL PRIMARY KEY,
    race_id INT NOT NULL REFERENCES dim_race(race_id),
    driver_id INT NOT NULL REFERENCES dim_driver(driver_id),
    team_id INT NOT NULL REFERENCES dim_team(team_id),
    session_id INT NOT NULL REFERENCES dim_session(session_id),
    lap_number INT NOT NULL,
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    tyre_compound_id INT REFERENCES dim_tyre_compound(tyre_compound_id),
    lap_time_ms INT NOT NULL,
    lap_position INT NOT NULL,
    sector1_ms INT,
    sector2_ms INT,
    sector3_ms INT,
    speed_trap_kmh NUMERIC(5, 2),
    tyre_age_laps INT DEFAULT 1,
    is_pit_lap INT DEFAULT 0,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unq_fact_lap UNIQUE (race_id, driver_id, session_id, lap_number)
);

-- High-performance composite indices for Grafana query acceleration
CREATE INDEX idx_fact_results_race_driver ON fact_race_results(race_id, driver_id);
CREATE INDEX idx_fact_results_driver ON fact_race_results(driver_id);
CREATE INDEX idx_fact_results_team ON fact_race_results(team_id);
CREATE INDEX idx_fact_results_circuit ON fact_race_results(circuit_id);

CREATE INDEX idx_fact_laps_race_driver_lap ON fact_lap_times(race_id, driver_id, lap_number);
CREATE INDEX idx_fact_laps_recorded_at ON fact_lap_times(recorded_at DESC);
CREATE INDEX idx_fact_laps_driver_time ON fact_lap_times(driver_id, recorded_at DESC);
CREATE INDEX idx_fact_laps_race ON fact_lap_times(race_id);
CREATE INDEX idx_dim_race_season ON dim_race(season_year);
