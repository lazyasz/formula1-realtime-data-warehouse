-- ============================================================================
-- FORMULA 1 RACE PERFORMANCE DATA WAREHOUSE — SNOWFLAKE SCHEMA (DDL)
-- ============================================================================
-- Normalized variant designed for Master Data Governance, ETL staging,
-- and low-redundancy storage before dimensional flattening into the Star Schema.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. DROP EXISTING SNOWFLAKE OBJECTS (FOR IDEMPOTENT EXECUTION)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS FACT_LAP_TIMES_SNOWFLAKE;
DROP TABLE IF EXISTS FACT_RACE_RESULTS_SNOWFLAKE;
DROP TABLE IF EXISTS DIM_RACE_SNOWFLAKE;
DROP TABLE IF EXISTS DIM_CIRCUIT_LAYOUT_HISTORY;
DROP TABLE IF EXISTS DIM_CIRCUIT_SNOWFLAKE;
DROP TABLE IF EXISTS DIM_COUNTRY;
DROP TABLE IF EXISTS DIM_DRIVER_NUMBER_HISTORY;
DROP TABLE IF EXISTS DIM_DRIVER_SNOWFLAKE;
DROP TABLE IF EXISTS DIM_NATIONALITY;
DROP TABLE IF EXISTS DIM_LIVERY_SPONSOR;
DROP TABLE IF EXISTS DIM_TEAM_PRINCIPAL;
DROP TABLE IF EXISTS DIM_ENGINE_SUPPLIER;
DROP TABLE IF EXISTS DIM_CONSTRUCTOR_SNOWFLAKE;
DROP TABLE IF EXISTS DIM_DATE_SNOWFLAKE;
DROP TABLE IF EXISTS DIM_SEASON;

-- ----------------------------------------------------------------------------
-- 2. CREATE OUTLYING / NORMALIZED SUB-DIMENSIONS
-- ----------------------------------------------------------------------------

-- DIM_NATIONALITY: Normalized nationality reference table
CREATE TABLE DIM_NATIONALITY (
    nationality_id INT PRIMARY KEY,
    nationality_name VARCHAR(50) NOT NULL UNIQUE,
    country_code VARCHAR(3) NOT NULL,
    continent VARCHAR(30) NOT NULL
);

-- DIM_ENGINE_SUPPLIER: Power unit manufacturers
CREATE TABLE DIM_ENGINE_SUPPLIER (
    engine_supplier_id INT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL UNIQUE,
    headquarters_country VARCHAR(50) NOT NULL,
    engine_architecture VARCHAR(50) NOT NULL DEFAULT '1.6L V6 Turbo Hybrid'
);

-- DIM_TEAM_PRINCIPAL: Team management personnel
CREATE TABLE DIM_TEAM_PRINCIPAL (
    principal_id INT PRIMARY KEY,
    principal_name VARCHAR(100) NOT NULL,
    nationality_id INT REFERENCES DIM_NATIONALITY(nationality_id),
    appointment_year INT NOT NULL
);

-- DIM_LIVERY_SPONSOR: Title sponsors & liveries
CREATE TABLE DIM_LIVERY_SPONSOR (
    sponsor_id INT PRIMARY KEY,
    sponsor_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    contract_start_year INT
);

-- DIM_COUNTRY: Normalized country reference for circuits
CREATE TABLE DIM_COUNTRY (
    country_id INT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    alpha2_code VARCHAR(2) NOT NULL,
    alpha3_code VARCHAR(3) NOT NULL,
    region VARCHAR(50) NOT NULL
);

-- DIM_SEASON: Season championship metadata, regulations era, points rules
CREATE TABLE DIM_SEASON (
    season_year INT PRIMARY KEY,
    technical_regulations_era VARCHAR(50) NOT NULL,
    points_system_version VARCHAR(50) NOT NULL,
    sprint_format_type VARCHAR(50),
    total_rounds_scheduled INT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. CREATE PRIMARY NORMALIZED DIMENSIONS
-- ----------------------------------------------------------------------------

-- DIM_DRIVER_SNOWFLAKE: Normalized Driver entity (references DIM_NATIONALITY)
CREATE TABLE DIM_DRIVER_SNOWFLAKE (
    driver_id INT PRIMARY KEY,
    driver_ref VARCHAR(50) NOT NULL UNIQUE,
    driver_code VARCHAR(3) NOT NULL,
    driver_name VARCHAR(100) NOT NULL,
    driver_dob DATE,
    nationality_id INT NOT NULL REFERENCES DIM_NATIONALITY(nationality_id),
    headshot_url TEXT
);

-- DIM_DRIVER_NUMBER_HISTORY: Slowly Changing Dimension for permanent/car numbers
CREATE TABLE DIM_DRIVER_NUMBER_HISTORY (
    history_id INT PRIMARY KEY,
    driver_id INT NOT NULL REFERENCES DIM_DRIVER_SNOWFLAKE(driver_id),
    season_year INT NOT NULL REFERENCES DIM_SEASON(season_year),
    permanent_car_number INT NOT NULL,
    is_reigning_champion_override INT DEFAULT 0
);

-- DIM_CONSTRUCTOR_SNOWFLAKE: Normalized Team entity (references Principal & Engine)
CREATE TABLE DIM_CONSTRUCTOR_SNOWFLAKE (
    constructor_id INT PRIMARY KEY,
    constructor_ref VARCHAR(50) NOT NULL UNIQUE,
    constructor_name VARCHAR(100) NOT NULL,
    nationality_id INT NOT NULL REFERENCES DIM_NATIONALITY(nationality_id),
    engine_supplier_id INT NOT NULL REFERENCES DIM_ENGINE_SUPPLIER(engine_supplier_id),
    principal_id INT REFERENCES DIM_TEAM_PRINCIPAL(principal_id),
    sponsor_id INT REFERENCES DIM_LIVERY_SPONSOR(sponsor_id),
    color_hex VARCHAR(10) NOT NULL
);

-- DIM_CIRCUIT_SNOWFLAKE: Normalized Track entity (references DIM_COUNTRY)
CREATE TABLE DIM_CIRCUIT_SNOWFLAKE (
    circuit_id INT PRIMARY KEY,
    circuit_ref VARCHAR(50) NOT NULL UNIQUE,
    circuit_name VARCHAR(150) NOT NULL,
    circuit_location VARCHAR(100),
    country_id INT NOT NULL REFERENCES DIM_COUNTRY(country_id),
    circuit_latitude DECIMAL(9,6),
    circuit_longitude DECIMAL(9,6),
    circuit_altitude_m INT
);

-- DIM_CIRCUIT_LAYOUT_HISTORY: Track length / turn revisions across seasons
CREATE TABLE DIM_CIRCUIT_LAYOUT_HISTORY (
    layout_id INT PRIMARY KEY,
    circuit_id INT NOT NULL REFERENCES DIM_CIRCUIT_SNOWFLAKE(circuit_id),
    layout_version_name VARCHAR(50) NOT NULL,
    length_km DECIMAL(5,3) NOT NULL,
    number_of_corners INT NOT NULL,
    drs_zones_count INT NOT NULL,
    valid_from_year INT NOT NULL,
    valid_to_year INT
);

-- DIM_RACE_SNOWFLAKE: Normalized Race event (references Circuit & Season)
CREATE TABLE DIM_RACE_SNOWFLAKE (
    race_id INT PRIMARY KEY,
    season_year INT NOT NULL REFERENCES DIM_SEASON(season_year),
    round INT NOT NULL,
    race_name VARCHAR(100) NOT NULL,
    circuit_id INT NOT NULL REFERENCES DIM_CIRCUIT_SNOWFLAKE(circuit_id),
    layout_id INT REFERENCES DIM_CIRCUIT_LAYOUT_HISTORY(layout_id),
    race_date DATE NOT NULL,
    race_start_time VARCHAR(20),
    total_race_laps INT NOT NULL
);

-- DIM_DATE_SNOWFLAKE: Calendar dimension linked to DIM_SEASON
CREATE TABLE DIM_DATE_SNOWFLAKE (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    season_year INT NOT NULL REFERENCES DIM_SEASON(season_year),
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. CREATE NORMALIZED FACT TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE FACT_RACE_RESULTS_SNOWFLAKE (
    result_id INT PRIMARY KEY,
    race_id INT NOT NULL REFERENCES DIM_RACE_SNOWFLAKE(race_id),
    driver_id INT NOT NULL REFERENCES DIM_DRIVER_SNOWFLAKE(driver_id),
    constructor_id INT NOT NULL REFERENCES DIM_CONSTRUCTOR_SNOWFLAKE(constructor_id),
    date_id INT NOT NULL REFERENCES DIM_DATE_SNOWFLAKE(date_id),
    status_id INT NOT NULL,
    
    grid_position INT NOT NULL,
    finish_position INT,
    race_points DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    race_laps INT NOT NULL,
    fastest_lap_time VARCHAR(20),
    pit_stop_count INT NOT NULL DEFAULT 0,
    total_pit_duration_sec DECIMAL(7,3) NOT NULL DEFAULT 0.000,
    driver_standing_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    is_win INT NOT NULL,
    is_podium INT NOT NULL
);

CREATE TABLE FACT_LAP_TIMES_SNOWFLAKE (
    lap_id INT PRIMARY KEY,
    race_id INT NOT NULL REFERENCES DIM_RACE_SNOWFLAKE(race_id),
    driver_id INT NOT NULL REFERENCES DIM_DRIVER_SNOWFLAKE(driver_id),
    constructor_id INT NOT NULL REFERENCES DIM_CONSTRUCTOR_SNOWFLAKE(constructor_id),
    date_id INT NOT NULL REFERENCES DIM_DATE_SNOWFLAKE(date_id),
    
    lap_number INT NOT NULL,
    lap_position INT NOT NULL,
    lap_time_ms INT NOT NULL,
    sector1_ms INT NOT NULL,
    sector2_ms INT NOT NULL,
    sector3_ms INT NOT NULL,
    tyre_age_laps INT NOT NULL,
    is_pit_lap INT NOT NULL DEFAULT 0
);
