-- ============================================================================
-- FORMULA 1 RACE PERFORMANCE DATA WAREHOUSE — PURE STAR SCHEMA (DDL)
-- ============================================================================
-- Optimized for high-throughput OLAP analytics, Power BI slice-and-dice,
-- sub-10ms dashboard filtering, and telemetry time-series queries.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. DROP EXISTING STAR SCHEMA OBJECTS (FOR IDEMPOTENT EXECUTION)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS FACT_LAP_TIMES;
DROP TABLE IF EXISTS FACT_RACE_RESULTS;
DROP TABLE IF EXISTS DIM_SESSION;
DROP TABLE IF EXISTS DIM_TYRE_COMPOUND;
DROP TABLE IF EXISTS DIM_STATUS;
DROP TABLE IF EXISTS DIM_DATE;
DROP TABLE IF EXISTS DIM_RACE;
DROP TABLE IF EXISTS DIM_CONSTRUCTOR;
DROP TABLE IF EXISTS DIM_DRIVER;

-- ----------------------------------------------------------------------------
-- 2. CREATE DIMENSION TABLES (DENORMALIZED / FLAT)
-- ----------------------------------------------------------------------------

-- DIM_DRIVER: Driver profile and biographical dimension
CREATE TABLE DIM_DRIVER (
    driver_id INT PRIMARY KEY,
    driver_ref VARCHAR(50) NOT NULL UNIQUE,
    driver_code VARCHAR(3) NOT NULL,
    driver_name VARCHAR(100) NOT NULL,
    driver_number INT,
    driver_dob DATE,
    driver_nationality VARCHAR(50),
    driver_flag_code VARCHAR(5),
    headshot_url TEXT
);

-- DIM_CONSTRUCTOR: Formula 1 constructor / team dimension
CREATE TABLE DIM_CONSTRUCTOR (
    constructor_id INT PRIMARY KEY,
    constructor_ref VARCHAR(50) NOT NULL UNIQUE,
    constructor_name VARCHAR(100) NOT NULL,
    constructor_nationality VARCHAR(50),
    color_hex VARCHAR(10) NOT NULL,
    secondary_color_hex VARCHAR(10),
    team_principal VARCHAR(100),
    power_unit VARCHAR(50)
);

-- DIM_RACE: Race event dimension (Circuit attributes denormalized for flat Star access)
CREATE TABLE DIM_RACE (
    race_id INT PRIMARY KEY,
    season_year INT NOT NULL,
    round INT NOT NULL,
    race_name VARCHAR(100) NOT NULL,
    race_date DATE NOT NULL,
    race_start_time VARCHAR(20),
    
    -- Denormalized Circuit Attributes (Merged from Circuit entity)
    circuit_id INT NOT NULL,
    circuit_name VARCHAR(150) NOT NULL,
    circuit_location VARCHAR(100),
    circuit_country VARCHAR(100),
    circuit_latitude DECIMAL(9,6),
    circuit_longitude DECIMAL(9,6),
    circuit_altitude_m INT,
    circuit_length_km DECIMAL(5,3),
    total_race_laps INT NOT NULL,
    lap_record_time VARCHAR(20),
    lap_record_holder VARCHAR(100),
    lap_record_year INT,
    track_svg_path TEXT,
    
    CONSTRAINT uq_race_season_round UNIQUE (season_year, round)
);

-- DIM_DATE: Calendar date dimension for temporal roll-ups
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

-- DIM_SESSION: Grand Prix weekend session dimension
CREATE TABLE DIM_SESSION (
    session_id INT PRIMARY KEY,
    session_code VARCHAR(10) NOT NULL UNIQUE, -- 'FP1', 'FP2', 'FP3', 'QUAL', 'SPRINT', 'RACE'
    session_name VARCHAR(50) NOT NULL,
    session_type VARCHAR(20) NOT NULL -- 'Practice', 'Qualifying', 'Sprint', 'Race'
);

-- DIM_TYRE_COMPOUND: Pirelli tyre compound dimension
CREATE TABLE DIM_TYRE_COMPOUND (
    compound_id INT PRIMARY KEY,
    compound_code VARCHAR(10) NOT NULL UNIQUE, -- 'SOFT', 'MEDIUM', 'HARD', 'INTER', 'WET'
    compound_name VARCHAR(30) NOT NULL,
    color_hex VARCHAR(10) NOT NULL,
    compound_type VARCHAR(20) NOT NULL -- 'Dry', 'Wet'
);

-- DIM_STATUS: Race classification and retirement status dimension
CREATE TABLE DIM_STATUS (
    status_id INT PRIMARY KEY,
    status_description VARCHAR(100) NOT NULL UNIQUE,
    is_classified INT NOT NULL CHECK (is_classified IN (0, 1))
);

-- ----------------------------------------------------------------------------
-- 3. CREATE FACT TABLES
-- ----------------------------------------------------------------------------

-- FACT_RACE_RESULTS: Central grain — One row per driver per race event
CREATE TABLE FACT_RACE_RESULTS (
    result_id INT PRIMARY KEY,
    race_id INT NOT NULL REFERENCES DIM_RACE(race_id),
    driver_id INT NOT NULL REFERENCES DIM_DRIVER(driver_id),
    constructor_id INT NOT NULL REFERENCES DIM_CONSTRUCTOR(constructor_id),
    date_id INT NOT NULL REFERENCES DIM_DATE(date_id),
    status_id INT NOT NULL REFERENCES DIM_STATUS(status_id),
    
    -- Race Performance Measures
    car_number INT,
    grid_position INT NOT NULL,
    qualifying_position INT,
    qualifying_best_time_sec DECIMAL(6,3),
    finish_position INT, -- NULL or >20 if DNF
    finish_position_text VARCHAR(10),
    race_points DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    race_laps INT NOT NULL,
    race_time VARCHAR(20),
    race_milliseconds BIGINT,
    
    -- Fastest Lap & Pit Stop Summary Measures
    fastest_lap_number INT,
    fastest_lap_rank INT,
    fastest_lap_time VARCHAR(20),
    fastest_lap_speed DECIMAL(6,3),
    pit_stop_count INT NOT NULL DEFAULT 0,
    total_pit_duration_sec DECIMAL(7,3) NOT NULL DEFAULT 0.000,
    avg_pit_duration_sec DECIMAL(6,3) NOT NULL DEFAULT 0.000,
    fastest_pit_duration_sec DECIMAL(6,3) NOT NULL DEFAULT 0.000,
    last_pit_lap INT NOT NULL DEFAULT 0,
    
    -- Cumulative Championship Standings (Up to this round)
    driver_standing_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    driver_championship_position INT,
    driver_championship_wins INT NOT NULL DEFAULT 0,
    constructor_standing_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    constructor_championship_position INT,
    constructor_championship_wins INT NOT NULL DEFAULT 0,
    driver_standing_gap_to_leader DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    constructor_standing_gap_to_leader DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    
    -- Positioning Deltas & Flags
    position_gain INT,
    qualifying_to_finish_delta INT,
    is_pole INT NOT NULL CHECK (is_pole IN (0, 1)),
    is_podium INT NOT NULL CHECK (is_podium IN (0, 1)),
    is_win INT NOT NULL CHECK (is_win IN (0, 1)),
    is_top_10 INT NOT NULL CHECK (is_top_10 IN (0, 1)),
    is_dnf INT NOT NULL CHECK (is_dnf IN (0, 1)),
    
    CONSTRAINT uq_race_driver UNIQUE (race_id, driver_id)
);

-- FACT_LAP_TIMES: Telemetry grain — One row per driver per lap per session
CREATE TABLE FACT_LAP_TIMES (
    lap_id INT PRIMARY KEY,
    race_id INT NOT NULL REFERENCES DIM_RACE(race_id),
    driver_id INT NOT NULL REFERENCES DIM_DRIVER(driver_id),
    constructor_id INT NOT NULL REFERENCES DIM_CONSTRUCTOR(constructor_id),
    session_id INT NOT NULL REFERENCES DIM_SESSION(session_id),
    date_id INT NOT NULL REFERENCES DIM_DATE(date_id),
    compound_id INT NOT NULL REFERENCES DIM_TYRE_COMPOUND(compound_id),
    
    -- Lap & Timing Measures
    lap_number INT NOT NULL,
    lap_position INT NOT NULL,
    lap_time_str VARCHAR(20) NOT NULL,
    lap_time_ms INT NOT NULL,
    sector1_ms INT NOT NULL,
    sector2_ms INT NOT NULL,
    sector3_ms INT NOT NULL,
    sector1_str VARCHAR(15),
    sector2_str VARCHAR(15),
    sector3_str VARCHAR(15),
    
    -- Telemetry & Mechanical Metrics
    speed_trap_kmh DECIMAL(5,2),
    avg_speed_kmh DECIMAL(5,2),
    tyre_age_laps INT NOT NULL,
    tyre_wear_pct DECIMAL(5,2),
    stint_number INT NOT NULL DEFAULT 1,
    is_pit_lap INT NOT NULL DEFAULT 0 CHECK (is_pit_lap IN (0, 1)),
    pit_duration_ms INT DEFAULT 0,
    gap_to_leader_ms INT NOT NULL DEFAULT 0,
    interval_to_ahead_ms INT NOT NULL DEFAULT 0,
    
    -- Telemetry Aggregates (Engine / Driver Input)
    throttle_pct_full DECIMAL(4,1),
    brake_events_count INT,
    gear_shifts_count INT,
    drs_activated INT DEFAULT 0 CHECK (drs_activated IN (0, 1)),
    
    -- Sector Delta Indicators
    s1_is_purple INT DEFAULT 0 CHECK (s1_is_purple IN (0, 1)),
    s2_is_purple INT DEFAULT 0 CHECK (s2_is_purple IN (0, 1)),
    s3_is_purple INT DEFAULT 0 CHECK (s3_is_purple IN (0, 1)),
    lap_is_fastest INT DEFAULT 0 CHECK (lap_is_fastest IN (0, 1)),
    
    CONSTRAINT uq_lap_driver_race_session UNIQUE (race_id, session_id, driver_id, lap_number)
);

-- ----------------------------------------------------------------------------
-- 4. CREATE HIGH-PERFORMANCE INDEXES FOR SLICING & DICING
-- ----------------------------------------------------------------------------

-- FACT_RACE_RESULTS Foreign Key & Composite Indexes
CREATE INDEX idx_frr_race ON FACT_RACE_RESULTS(race_id);
CREATE INDEX idx_frr_driver ON FACT_RACE_RESULTS(driver_id);
CREATE INDEX idx_frr_constructor ON FACT_RACE_RESULTS(constructor_id);
CREATE INDEX idx_frr_date ON FACT_RACE_RESULTS(date_id);
CREATE INDEX idx_frr_status ON FACT_RACE_RESULTS(status_id);
CREATE INDEX idx_frr_composite ON FACT_RACE_RESULTS(race_id, driver_id, constructor_id);

-- FACT_LAP_TIMES Foreign Key & Composite Indexes (Critical for sub-10ms Telemetry Queries)
CREATE INDEX idx_flt_race ON FACT_LAP_TIMES(race_id);
CREATE INDEX idx_flt_driver ON FACT_LAP_TIMES(driver_id);
CREATE INDEX idx_flt_constructor ON FACT_LAP_TIMES(constructor_id);
CREATE INDEX idx_flt_session ON FACT_LAP_TIMES(session_id);
CREATE INDEX idx_flt_compound ON FACT_LAP_TIMES(compound_id);
CREATE INDEX idx_flt_race_lap ON FACT_LAP_TIMES(race_id, lap_number);
CREATE INDEX idx_flt_race_driver_lap ON FACT_LAP_TIMES(race_id, driver_id, lap_number);
CREATE INDEX idx_flt_race_compound ON FACT_LAP_TIMES(race_id, compound_id);

-- DIM_RACE indexes
CREATE INDEX idx_dr_season ON DIM_RACE(season_year);
CREATE INDEX idx_dr_circuit ON DIM_RACE(circuit_id);
