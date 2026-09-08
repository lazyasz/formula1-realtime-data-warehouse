"""
Formula 1 Race Performance Data Warehouse — Master ETL & Database Ingestion Engine
Ingests the official 68-column master dataset (2004-2024, 8,650 records),
extracts conformed dimension tables, generates date dimensions, creates surrogate keys,
and deploys both Star Schema and Snowflake Schema into SQLite/PostgreSQL warehouse.
"""

import sqlite3
import pandas as pd
import numpy as np
import datetime
import os

CSV_PATH = "F1_Warehouse_Master_65_Columns_2004_2024.csv"
DB_PATH = "f1_warehouse.db"

def run_master_etl():
    print("================================================================================")
    print("  FORMULA 1 RACE PERFORMANCE DATA WAREHOUSE — MASTER ETL INGESTION (2004-2024)")
    print("================================================================================")

    # 1. EXTRACT
    print(f"\n>>> [Phase 1: Extraction] Reading master dataset from '{CSV_PATH}'...")
    df_raw = pd.read_csv(CSV_PATH)
    total_records = len(df_raw)
    print(f"    Loaded {total_records:,} rows and {len(df_raw.columns)} columns.")
    print(f"    Seasons covered: {df_raw['season'].min()} to {df_raw['season'].max()} ({df_raw['season'].nunique()} distinct seasons).")

    # 2. TRANSFORM CONFORMED DIMENSIONS
    print("\n>>> [Phase 2: Dimension Modeling & Transformation] Extracting conformed dimensions...")

    # A. DIM_DRIVER
    df_driver = df_raw[[
        'driver_id', 'driver_ref', 'driver_code', 'driver_name', 'driver_dob', 'driver_nationality'
    ]].drop_duplicates(subset=['driver_id']).sort_values('driver_id').reset_index(drop=True)
    print(f"    [DIM_DRIVER] Extracted {len(df_driver)} unique drivers.")

    # B. DIM_CONSTRUCTOR
    df_constructor = df_raw[[
        'constructor_id', 'constructor_ref', 'constructor_name', 'constructor_nationality'
    ]].drop_duplicates(subset=['constructor_id']).sort_values('constructor_id').reset_index(drop=True)
    print(f"    [DIM_CONSTRUCTOR] Extracted {len(df_constructor)} unique constructors.")

    # C. DIM_CIRCUIT (Snowflake sub-dimension)
    df_circuit = df_raw[[
        'circuit_id', 'circuit_name', 'circuit_location', 'circuit_country', 
        'circuit_latitude', 'circuit_longitude', 'circuit_altitude_m'
    ]].drop_duplicates(subset=['circuit_id']).sort_values('circuit_id').reset_index(drop=True)
    print(f"    [DIM_CIRCUIT] Extracted {len(df_circuit)} unique circuits.")

    # D. DIM_STATUS
    unique_statuses = sorted(df_raw['race_status'].unique())
    status_mapping = {status: idx + 1 for idx, status in enumerate(unique_statuses)}
    df_status = pd.DataFrame([
        {'status_id': status_mapping[s], 'status_description': s} for s in unique_statuses
    ])
    print(f"    [DIM_STATUS] Extracted {len(df_status)} distinct race finish/DNF status descriptions.")

    # E. DIM_DATE (Calendar Dimension)
    unique_dates = sorted(df_raw['race_date'].unique())
    date_records = []
    for rdate in unique_dates:
        dt = datetime.datetime.strptime(rdate, '%Y-%m-%d')
        date_key = int(rdate.replace('-', ''))
        date_records.append({
            'date_id': date_key,
            'full_date': rdate,
            'year': dt.year,
            'quarter': (dt.month - 1) // 3 + 1,
            'month': dt.month,
            'month_name': dt.strftime('%B'),
            'day_of_week': dt.isoweekday(),
            'day_name': dt.strftime('%A')
        })
    df_date_dim = pd.DataFrame(date_records)
    print(f"    [DIM_DATE] Generated {len(df_date_dim)} unique calendar date dimension records.")

    # F. DIM_RACE_STAR (Denormalized with Circuit metadata)
    df_race_star = df_raw[[
        'race_id', 'season', 'round', 'race_name', 'race_date', 'race_start_time',
        'circuit_id', 'circuit_name', 'circuit_location', 'circuit_country',
        'circuit_latitude', 'circuit_longitude', 'circuit_altitude_m'
    ]].drop_duplicates(subset=['race_id']).rename(columns={'season': 'season_year'}).sort_values('race_id').reset_index(drop=True)
    print(f"    [DIM_RACE_STAR] Extracted {len(df_race_star)} distinct Grand Prix races (Denormalized).")

    # G. DIM_RACE_SNOWFLAKE (Normalized with circuit_id FK)
    df_race_snowflake = df_raw[[
        'race_id', 'season', 'round', 'race_name', 'circuit_id', 'race_date', 'race_start_time'
    ]].drop_duplicates(subset=['race_id']).rename(columns={'season': 'season_year'}).sort_values('race_id').reset_index(drop=True)
    print(f"    [DIM_RACE_SNOWFLAKE] Extracted {len(df_race_snowflake)} distinct Grand Prix races (Normalized).")

    # 3. TRANSFORM FACT TABLE
    print("\n>>> [Phase 3: Fact Modeling & Metric Mapping] Mapping measures and foreign keys...")
    df_fact = df_raw.copy()
    
    # Map status_id
    df_fact['status_id'] = df_fact['race_status'].map(status_mapping)
    
    # Map date_id
    df_fact['date_id'] = df_fact['race_date'].str.replace('-', '').astype(int)

    # Reorder/select Fact columns
    fact_columns = [
        'race_id', 'driver_id', 'constructor_id', 'date_id', 'status_id',
        'car_number', 'grid_position', 'qualifying_position', 'qualifying_best_time_sec',
        'finish_position', 'finish_position_text', 'race_points', 'race_laps', 'race_time', 'race_milliseconds',
        'fastest_lap_number', 'fastest_lap_rank', 'fastest_lap_time', 'fastest_lap_speed',
        'pit_stop_count', 'total_pit_duration_sec', 'avg_pit_duration_sec', 'fastest_pit_duration_sec', 'last_pit_lap',
        'laps_recorded', 'fastest_recorded_lap_ms', 'average_lap_ms',
        'sprint_position', 'sprint_points',
        'driver_standing_points', 'driver_championship_position', 'driver_championship_wins',
        'constructor_standing_points', 'constructor_championship_position', 'constructor_championship_wins', 'constructor_race_points',
        'driver_standing_gap_to_leader', 'constructor_standing_gap_to_leader',
        'position_gain', 'qualifying_to_finish_delta',
        'is_pole', 'is_podium', 'is_win', 'is_top_10', 'is_dnf',
        'points_per_lap', 'race_completion_pct', 'driver_age_years', 'driver_age_at_race'
    ]
    df_fact_clean = df_fact[fact_columns].copy()
    df_fact_clean.insert(0, 'result_id', range(1, len(df_fact_clean) + 1))
    print(f"    Prepared {len(df_fact_clean):,} fact records across 50 analytical metric columns.")

    # 4. LOAD INTO DATA WAREHOUSE (SQLite / PostgreSQL Compatible DDL)
    print(f"\n>>> [Phase 4: Warehouse Loading] Deploying schemas and loading into '{DB_PATH}'...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create Tables
    cursor.executescript("""
    -- =========================================================================
    -- 1. CONFORMED DIMENSIONS
    -- =========================================================================
    CREATE TABLE DIM_DRIVER (
        driver_id INTEGER PRIMARY KEY,
        driver_ref TEXT NOT NULL UNIQUE,
        driver_code TEXT,
        driver_name TEXT NOT NULL,
        driver_dob TEXT,
        driver_nationality TEXT
    );

    CREATE TABLE DIM_CONSTRUCTOR (
        constructor_id INTEGER PRIMARY KEY,
        constructor_ref TEXT NOT NULL UNIQUE,
        constructor_name TEXT NOT NULL,
        constructor_nationality TEXT
    );

    CREATE TABLE DIM_STATUS (
        status_id INTEGER PRIMARY KEY,
        status_description TEXT NOT NULL UNIQUE
    );

    CREATE TABLE DIM_DATE (
        date_id INTEGER PRIMARY KEY,
        full_date TEXT NOT NULL UNIQUE,
        year INTEGER NOT NULL,
        quarter INTEGER NOT NULL,
        month INTEGER NOT NULL,
        month_name TEXT NOT NULL,
        day_of_week INTEGER NOT NULL,
        day_name TEXT NOT NULL
    );

    -- =========================================================================
    -- 2. STAR SCHEMA (Denormalized)
    -- =========================================================================
    CREATE TABLE DIM_RACE_STAR (
        race_id INTEGER PRIMARY KEY,
        season_year INTEGER NOT NULL,
        round INTEGER NOT NULL,
        race_name TEXT NOT NULL,
        race_date TEXT NOT NULL,
        race_start_time TEXT,
        circuit_id INTEGER NOT NULL,
        circuit_name TEXT NOT NULL,
        circuit_location TEXT,
        circuit_country TEXT,
        circuit_latitude REAL,
        circuit_longitude REAL,
        circuit_altitude_m INTEGER
    );

    CREATE TABLE FACT_RACE_RESULTS_STAR (
        result_id INTEGER PRIMARY KEY,
        race_id INTEGER NOT NULL REFERENCES DIM_RACE_STAR(race_id),
        driver_id INTEGER NOT NULL REFERENCES DIM_DRIVER(driver_id),
        constructor_id INTEGER NOT NULL REFERENCES DIM_CONSTRUCTOR(constructor_id),
        date_id INTEGER NOT NULL REFERENCES DIM_DATE(date_id),
        status_id INTEGER NOT NULL REFERENCES DIM_STATUS(status_id),
        car_number INTEGER,
        grid_position INTEGER NOT NULL,
        qualifying_position INTEGER,
        qualifying_best_time_sec REAL,
        finish_position INTEGER,
        finish_position_text TEXT,
        race_points REAL NOT NULL DEFAULT 0.0,
        race_laps INTEGER NOT NULL,
        race_time TEXT,
        race_milliseconds REAL,
        fastest_lap_number INTEGER,
        fastest_lap_rank INTEGER,
        fastest_lap_time TEXT,
        fastest_lap_speed REAL,
        pit_stop_count INTEGER NOT NULL DEFAULT 0,
        total_pit_duration_sec REAL NOT NULL DEFAULT 0.0,
        avg_pit_duration_sec REAL NOT NULL DEFAULT 0.0,
        fastest_pit_duration_sec REAL NOT NULL DEFAULT 0.0,
        last_pit_lap INTEGER NOT NULL DEFAULT 0,
        laps_recorded INTEGER,
        fastest_recorded_lap_ms REAL,
        average_lap_ms REAL,
        sprint_position REAL,
        sprint_points REAL DEFAULT 0.0,
        driver_standing_points REAL NOT NULL DEFAULT 0.0,
        driver_championship_position INTEGER,
        driver_championship_wins INTEGER NOT NULL DEFAULT 0,
        constructor_standing_points REAL NOT NULL DEFAULT 0.0,
        constructor_championship_position INTEGER,
        constructor_championship_wins INTEGER NOT NULL DEFAULT 0,
        constructor_race_points REAL NOT NULL DEFAULT 0.0,
        driver_standing_gap_to_leader REAL DEFAULT 0.0,
        constructor_standing_gap_to_leader REAL DEFAULT 0.0,
        position_gain INTEGER,
        qualifying_to_finish_delta INTEGER,
        is_pole INTEGER NOT NULL CHECK (is_pole IN (0, 1)),
        is_podium INTEGER NOT NULL CHECK (is_podium IN (0, 1)),
        is_win INTEGER NOT NULL CHECK (is_win IN (0, 1)),
        is_top_10 INTEGER NOT NULL CHECK (is_top_10 IN (0, 1)),
        is_dnf INTEGER NOT NULL CHECK (is_dnf IN (0, 1)),
        points_per_lap REAL,
        race_completion_pct REAL,
        driver_age_years REAL,
        driver_age_at_race REAL
    );

    -- =========================================================================
    -- 3. SNOWFLAKE SCHEMA (Normalized)
    -- =========================================================================
    CREATE TABLE DIM_CIRCUIT_SNOWFLAKE (
        circuit_id INTEGER PRIMARY KEY,
        circuit_name TEXT NOT NULL,
        circuit_location TEXT,
        circuit_country TEXT,
        circuit_latitude REAL,
        circuit_longitude REAL,
        circuit_altitude_m INTEGER
    );

    CREATE TABLE DIM_RACE_SNOWFLAKE (
        race_id INTEGER PRIMARY KEY,
        season_year INTEGER NOT NULL,
        round INTEGER NOT NULL,
        race_name TEXT NOT NULL,
        circuit_id INTEGER NOT NULL REFERENCES DIM_CIRCUIT_SNOWFLAKE(circuit_id),
        race_date TEXT NOT NULL,
        race_start_time TEXT
    );

    CREATE TABLE FACT_RACE_RESULTS_SNOWFLAKE (
        result_id INTEGER PRIMARY KEY,
        race_id INTEGER NOT NULL REFERENCES DIM_RACE_SNOWFLAKE(race_id),
        driver_id INTEGER NOT NULL REFERENCES DIM_DRIVER(driver_id),
        constructor_id INTEGER NOT NULL REFERENCES DIM_CONSTRUCTOR(constructor_id),
        date_id INTEGER NOT NULL REFERENCES DIM_DATE(date_id),
        status_id INTEGER NOT NULL REFERENCES DIM_STATUS(status_id),
        car_number INTEGER,
        grid_position INTEGER NOT NULL,
        qualifying_position INTEGER,
        qualifying_best_time_sec REAL,
        finish_position INTEGER,
        finish_position_text TEXT,
        race_points REAL NOT NULL DEFAULT 0.0,
        race_laps INTEGER NOT NULL,
        race_time TEXT,
        race_milliseconds REAL,
        fastest_lap_number INTEGER,
        fastest_lap_rank INTEGER,
        fastest_lap_time TEXT,
        fastest_lap_speed REAL,
        pit_stop_count INTEGER NOT NULL DEFAULT 0,
        total_pit_duration_sec REAL NOT NULL DEFAULT 0.0,
        avg_pit_duration_sec REAL NOT NULL DEFAULT 0.0,
        fastest_pit_duration_sec REAL NOT NULL DEFAULT 0.0,
        last_pit_lap INTEGER NOT NULL DEFAULT 0,
        laps_recorded INTEGER,
        fastest_recorded_lap_ms REAL,
        average_lap_ms REAL,
        sprint_position REAL,
        sprint_points REAL DEFAULT 0.0,
        driver_standing_points REAL NOT NULL DEFAULT 0.0,
        driver_championship_position INTEGER,
        driver_championship_wins INTEGER NOT NULL DEFAULT 0,
        constructor_standing_points REAL NOT NULL DEFAULT 0.0,
        constructor_championship_position INTEGER,
        constructor_championship_wins INTEGER NOT NULL DEFAULT 0,
        constructor_race_points REAL NOT NULL DEFAULT 0.0,
        driver_standing_gap_to_leader REAL DEFAULT 0.0,
        constructor_standing_gap_to_leader REAL DEFAULT 0.0,
        position_gain INTEGER,
        qualifying_to_finish_delta INTEGER,
        is_pole INTEGER NOT NULL CHECK (is_pole IN (0, 1)),
        is_podium INTEGER NOT NULL CHECK (is_podium IN (0, 1)),
        is_win INTEGER NOT NULL CHECK (is_win IN (0, 1)),
        is_top_10 INTEGER NOT NULL CHECK (is_top_10 IN (0, 1)),
        is_dnf INTEGER NOT NULL CHECK (is_dnf IN (0, 1)),
        points_per_lap REAL,
        race_completion_pct REAL,
        driver_age_years REAL,
        driver_age_at_race REAL
    );

    -- =========================================================================
    -- 4. PERFORMANCE INDEXES
    -- =========================================================================
    CREATE INDEX idx_star_driver ON FACT_RACE_RESULTS_STAR(driver_id);
    CREATE INDEX idx_star_constructor ON FACT_RACE_RESULTS_STAR(constructor_id);
    CREATE INDEX idx_star_race ON FACT_RACE_RESULTS_STAR(race_id);
    CREATE INDEX idx_star_date ON FACT_RACE_RESULTS_STAR(date_id);
    CREATE INDEX idx_star_status ON FACT_RACE_RESULTS_STAR(status_id);

    CREATE INDEX idx_snow_driver ON FACT_RACE_RESULTS_SNOWFLAKE(driver_id);
    CREATE INDEX idx_snow_constructor ON FACT_RACE_RESULTS_SNOWFLAKE(constructor_id);
    CREATE INDEX idx_snow_race ON FACT_RACE_RESULTS_SNOWFLAKE(race_id);
    CREATE INDEX idx_snow_date ON FACT_RACE_RESULTS_SNOWFLAKE(date_id);
    CREATE INDEX idx_snow_status ON FACT_RACE_RESULTS_SNOWFLAKE(status_id);
    """)

    # Populate Conformed Dimensions
    df_driver.to_sql('DIM_DRIVER', conn, if_exists='append', index=False)
    df_constructor.to_sql('DIM_CONSTRUCTOR', conn, if_exists='append', index=False)
    df_status.to_sql('DIM_STATUS', conn, if_exists='append', index=False)
    df_date_dim.to_sql('DIM_DATE', conn, if_exists='append', index=False)

    # Populate Star Schema
    df_race_star.to_sql('DIM_RACE_STAR', conn, if_exists='append', index=False)
    df_fact_clean.to_sql('FACT_RACE_RESULTS_STAR', conn, if_exists='append', index=False)

    # Populate Snowflake Schema
    df_circuit.to_sql('DIM_CIRCUIT_SNOWFLAKE', conn, if_exists='append', index=False)
    df_race_snowflake.to_sql('DIM_RACE_SNOWFLAKE', conn, if_exists='append', index=False)
    df_fact_clean.to_sql('FACT_RACE_RESULTS_SNOWFLAKE', conn, if_exists='append', index=False)

    conn.commit()

    # Verification
    cursor.execute("SELECT COUNT(*) FROM FACT_RACE_RESULTS_STAR;")
    star_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM FACT_RACE_RESULTS_SNOWFLAKE;")
    snow_count = cursor.fetchone()[0]
    
    print("\n>>> [Verification Summary]")
    print(f"    • DIM_DRIVER:            {len(df_driver):,} records")
    print(f"    • DIM_CONSTRUCTOR:       {len(df_constructor):,} records")
    print(f"    • DIM_CIRCUIT:           {len(df_circuit):,} records")
    print(f"    • DIM_RACE:              {len(df_race_star):,} records")
    print(f"    • DIM_STATUS:            {len(df_status):,} records")
    print(f"    • DIM_DATE:              {len(df_date_dim):,} records")
    print(f"    • FACT_RESULTS_STAR:     {star_count:,} records (100% Loaded)")
    print(f"    • FACT_RESULTS_SNOWFLAKE:{snow_count:,} records (100% Loaded)")

    conn.close()
    print("\n================================================================================")
    print("  ETL & DATA WAREHOUSE INGESTION COMPLETED SUCCESSFULLY!")
    print("================================================================================\n")

if __name__ == "__main__":
    run_master_etl()
