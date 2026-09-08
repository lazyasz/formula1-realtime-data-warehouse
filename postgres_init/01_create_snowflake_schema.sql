-- =============================================================================
-- FORMULA 1 DATA WAREHOUSE — UPSTREAM 3NF SNOWFLAKE SCHEMA (PostgreSQL DDL)
-- =============================================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS fact_lap_times_snowflake CASCADE;
DROP TABLE IF EXISTS fact_race_results_snowflake CASCADE;
DROP TABLE IF EXISTS dim_driver_snowflake CASCADE;
DROP TABLE IF EXISTS dim_team_snowflake CASCADE;
DROP TABLE IF EXISTS dim_circuit_layout_history CASCADE;
DROP TABLE IF EXISTS dim_circuit_snowflake CASCADE;
DROP TABLE IF EXISTS dim_race_snowflake CASCADE;
DROP TABLE IF EXISTS dim_date_snowflake CASCADE;
DROP TABLE IF EXISTS dim_season CASCADE;
DROP TABLE IF EXISTS dim_livery_sponsor CASCADE;
DROP TABLE IF EXISTS dim_team_principal CASCADE;
DROP TABLE IF EXISTS dim_engine_supplier CASCADE;
DROP TABLE IF EXISTS dim_country CASCADE;
DROP TABLE IF EXISTS dim_nationality CASCADE;
DROP TABLE IF EXISTS dim_tyre_compound_snowflake CASCADE;
DROP TABLE IF EXISTS dim_session_snowflake CASCADE;

-- 1. Dimension: Driver Nationalities (3NF Normalized)
CREATE TABLE dim_nationality (
    nationality_id SERIAL PRIMARY KEY,
    nationality_name VARCHAR(50) NOT NULL UNIQUE,
    demonym VARCHAR(50) NOT NULL,
    iso_alpha2_code VARCHAR(2),
    iso_alpha3_code VARCHAR(3)
);

-- 2. Dimension: Countries (3NF Normalized)
CREATE TABLE dim_country (
    country_id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    iso_alpha2_code VARCHAR(2),
    iso_alpha3_code VARCHAR(3),
    un_continent VARCHAR(50) NOT NULL
);

-- 3. Dimension: Engine Suppliers
CREATE TABLE dim_engine_supplier (
    engine_supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL UNIQUE,
    headquarters_country VARCHAR(100),
    engine_architecture VARCHAR(50) DEFAULT '1.6L V6 Turbo Hybrid',
    is_active_manufacturer BOOLEAN DEFAULT TRUE
);

-- 4. Dimension: Team Principals
CREATE TABLE dim_team_principal (
    team_principal_id SERIAL PRIMARY KEY,
    principal_name VARCHAR(100) NOT NULL,
    nationality_id INT REFERENCES dim_nationality(nationality_id),
    appointed_year INT NOT NULL,
    prior_f1_role VARCHAR(100)
);

-- 5. Dimension: Livery Title Sponsors
CREATE TABLE dim_livery_sponsor (
    livery_sponsor_id SERIAL PRIMARY KEY,
    sponsor_name VARCHAR(100) NOT NULL,
    industry_sector VARCHAR(100),
    contract_start_year INT,
    contract_end_year INT
);

-- 6. Dimension: Seasons
CREATE TABLE dim_season (
    season_year INT PRIMARY KEY,
    total_rounds INT NOT NULL,
    technical_regulations_era VARCHAR(100) NOT NULL,
    budget_cap_usd NUMERIC(15, 2),
    sprint_race_format_version VARCHAR(50)
);

-- 7. Dimension: Circuits (Normalized with Country FK)
CREATE TABLE dim_circuit_snowflake (
    circuit_id INT PRIMARY KEY,
    circuit_ref VARCHAR(100) NOT NULL,
    circuit_name VARCHAR(150) NOT NULL,
    location_city VARCHAR(100),
    country_id INT NOT NULL REFERENCES dim_country(country_id),
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    altitude_m INT,
    track_direction VARCHAR(20) DEFAULT 'Clockwise'
);

-- 8. Dimension: Circuit Layout History (Type 2 SCD)
CREATE TABLE dim_circuit_layout_history (
    layout_id SERIAL PRIMARY KEY,
    circuit_id INT NOT NULL REFERENCES dim_circuit_snowflake(circuit_id),
    layout_name VARCHAR(100),
    track_length_km NUMERIC(6, 3) NOT NULL,
    total_corners INT NOT NULL,
    drs_zones_count INT DEFAULT 2,
    valid_from_year INT NOT NULL,
    valid_to_year INT
);

-- 9. Dimension: Races (Snowflake)
CREATE TABLE dim_race_snowflake (
    race_id INT PRIMARY KEY,
    season_year INT NOT NULL REFERENCES dim_season(season_year),
    round INT NOT NULL,
    circuit_id INT NOT NULL REFERENCES dim_circuit_snowflake(circuit_id),
    race_name VARCHAR(150) NOT NULL,
    race_date DATE NOT NULL,
    total_race_laps INT NOT NULL
);

-- 10. Dimension: Calendar Date
CREATE TABLE dim_date_snowflake (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    season_year INT NOT NULL REFERENCES dim_season(season_year),
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    quarter INT NOT NULL
);

-- 11. Dimension: Tyre Compounds (Snowflake)
CREATE TABLE dim_tyre_compound_snowflake (
    tyre_compound_id INT PRIMARY KEY,
    compound_name VARCHAR(50) NOT NULL,
    compound_code VARCHAR(10) NOT NULL,
    pirelli_classification VARCHAR(10),
    color_hex VARCHAR(7) NOT NULL
);

-- 12. Dimension: Sessions (Snowflake)
CREATE TABLE dim_session_snowflake (
    session_id INT PRIMARY KEY,
    session_type VARCHAR(20) NOT NULL,
    session_name VARCHAR(50) NOT NULL,
    points_awarded BOOLEAN DEFAULT FALSE
);

-- 13. Dimension: Teams / Constructors (Snowflake)
CREATE TABLE dim_team_snowflake (
    team_id INT PRIMARY KEY,
    constructor_ref VARCHAR(100) NOT NULL,
    team_name VARCHAR(150) NOT NULL,
    nationality_id INT NOT NULL REFERENCES dim_nationality(nationality_id),
    engine_supplier_id INT REFERENCES dim_engine_supplier(engine_supplier_id),
    team_principal_id INT REFERENCES dim_team_principal(team_principal_id),
    livery_sponsor_id INT REFERENCES dim_livery_sponsor(livery_sponsor_id),
    color_hex VARCHAR(7) NOT NULL,
    headquarters_location VARCHAR(150)
);

-- 14. Dimension: Drivers (Snowflake)
CREATE TABLE dim_driver_snowflake (
    driver_id INT PRIMARY KEY,
    driver_ref VARCHAR(100) NOT NULL,
    driver_number INT,
    driver_code VARCHAR(3) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    driver_name VARCHAR(200) NOT NULL,
    dob DATE,
    nationality_id INT NOT NULL REFERENCES dim_nationality(nationality_id)
);

-- 15. Fact Table: Race Results (Snowflake)
CREATE TABLE fact_race_results_snowflake (
    result_id SERIAL PRIMARY KEY,
    race_id INT NOT NULL REFERENCES dim_race_snowflake(race_id),
    driver_id INT NOT NULL REFERENCES dim_driver_snowflake(driver_id),
    team_id INT NOT NULL REFERENCES dim_team_snowflake(team_id),
    date_id INT NOT NULL REFERENCES dim_date_snowflake(date_id),
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
    CONSTRAINT unq_snowflake_race_driver UNIQUE (race_id, driver_id)
);

-- 16. Fact Table: Lap Times & Telemetry (Snowflake)
CREATE TABLE fact_lap_times_snowflake (
    lap_id BIGSERIAL PRIMARY KEY,
    race_id INT NOT NULL REFERENCES dim_race_snowflake(race_id),
    driver_id INT NOT NULL REFERENCES dim_driver_snowflake(driver_id),
    team_id INT NOT NULL REFERENCES dim_team_snowflake(team_id),
    session_id INT NOT NULL REFERENCES dim_session_snowflake(session_id),
    tyre_compound_id INT REFERENCES dim_tyre_compound_snowflake(tyre_compound_id),
    date_id INT NOT NULL REFERENCES dim_date_snowflake(date_id),
    lap_number INT NOT NULL,
    lap_time_ms INT NOT NULL,
    lap_position INT NOT NULL,
    sector1_ms INT,
    sector2_ms INT,
    sector3_ms INT,
    speed_trap_kmh NUMERIC(5, 2),
    tyre_age_laps INT DEFAULT 1,
    is_pit_lap INT DEFAULT 0,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unq_snowflake_lap UNIQUE (race_id, driver_id, session_id, lap_number)
);
