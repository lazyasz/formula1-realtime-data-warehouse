import os
import sys
import time
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch, execute_values
from datetime import datetime, date

# Database connection parameters from Environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "f1_warehouse")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
CSV_PATH = os.getenv("CSV_PATH", "/app/F1_Warehouse_Master_65_Columns_2004_2024.csv")

# Fallback local paths if running outside docker container
if not os.path.exists(CSV_PATH):
    local_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "F1_Warehouse_Master_65_Columns_2004_2024.csv")
    if os.path.exists(local_csv):
        CSV_PATH = local_csv

def get_postgres_connection(max_retries=15, retry_delay_sec=2):
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            conn.autocommit = False
            print(f">>> [ETL] Successfully connected to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
            return conn
        except Exception as e:
            print(f">>> [ETL] Waiting for PostgreSQL ({i+1}/{max_retries}): {e}")
            time.sleep(retry_delay_sec)
    raise Exception(">>> [ETL ERROR] Failed to connect to PostgreSQL after multiple retries.")

def run_master_etl():
    print("=" * 80)
    print("  FORMULA 1 DATA WAREHOUSE — MASTER ETL & SEEDING PIPELINE")
    print("=" * 80)
    print(f">>> Reading master CSV dataset from: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    print(f">>> Loaded master dataset: {len(df):,} race result rows across seasons {df['season_year'].min()} to {df['season_year'].max()}.")

    conn = get_postgres_connection()
    cur = conn.cursor()

    # -------------------------------------------------------------------------
    # 1. SEED DIM_TYRE_COMPOUND & DIM_SESSION
    # -------------------------------------------------------------------------
    print(">>> [1/6] Seeding Dimensions: Compounds & Sessions...")
    compounds = [
        (1, 'Soft', 'S', '#FF1801'),
        (2, 'Medium', 'M', '#FFD800'),
        (3, 'Hard', 'H', '#FFFFFF'),
        (4, 'Intermediate', 'I', '#39B54A'),
        (5, 'Wet', 'W', '#00AEEF')
    ]
    execute_values(cur, """
        INSERT INTO dim_tyre_compound (tyre_compound_id, compound_name, compound_code, color_hex)
        VALUES %s
        ON CONFLICT (tyre_compound_id) DO UPDATE SET compound_name = EXCLUDED.compound_name, color_hex = EXCLUDED.color_hex;
    """, compounds)

    sessions = [
        (1, 'FP1', 'Practice 1'),
        (2, 'FP2', 'Practice 2'),
        (3, 'FP3', 'Practice 3'),
        (4, 'QUALI', 'Qualifying Session'),
        (5, 'SPRINT', 'Sprint Race'),
        (6, 'RACE', 'Grand Prix Main Race')
    ]
    execute_values(cur, """
        INSERT INTO dim_session (session_id, session_type, session_name)
        VALUES %s
        ON CONFLICT (session_id) DO UPDATE SET session_type = EXCLUDED.session_type;
    """, sessions)

    # -------------------------------------------------------------------------
    # 2. SEED DIM_CIRCUIT & DIM_RACE
    # -------------------------------------------------------------------------
    print(">>> [2/6] Seeding Dimensions: Circuits & Races...")
    circuit_records = []
    seen_circuits = set()
    for _, row in df.iterrows():
        c_id = int(row['circuit_id'])
        if c_id not in seen_circuits:
            seen_circuits.add(c_id)
            circuit_records.append((
                c_id,
                str(row.get('circuit_ref', f'circuit_{c_id}')),
                str(row['circuit_name']),
                str(row.get('circuit_location', 'N/A')),
                str(row.get('circuit_country', 'N/A')),
                float(row.get('circuit_lat', 0.0)) if pd.notnull(row.get('circuit_lat')) else None,
                float(row.get('circuit_lng', 0.0)) if pd.notnull(row.get('circuit_lng')) else None,
                int(row.get('circuit_alt', 0)) if pd.notnull(row.get('circuit_alt')) else 0,
                5.380, # default track length km
                16     # default corner count
            ))
    execute_values(cur, """
        INSERT INTO dim_circuit (circuit_id, circuit_ref, circuit_name, location_city, circuit_country, latitude, longitude, altitude_m, track_length_km, total_corners)
        VALUES %s
        ON CONFLICT (circuit_id) DO UPDATE SET circuit_name = EXCLUDED.circuit_name, circuit_country = EXCLUDED.circuit_country;
    """, circuit_records)

    race_records = []
    seen_races = set()
    for _, row in df.iterrows():
        r_id = int(row['race_id'])
        if r_id not in seen_races:
            seen_races.add(r_id)
            race_records.append((
                r_id,
                int(row['season_year']),
                int(row['round']),
                str(row['race_name']),
                int(row['circuit_id']),
                str(row['race_date']),
                int(row['total_race_laps']) if pd.notnull(row.get('total_race_laps')) and int(row.get('total_race_laps', 0)) > 0 else 52
            ))
    execute_values(cur, """
        INSERT INTO dim_race (race_id, season_year, round, race_name, circuit_id, race_date, total_race_laps)
        VALUES %s
        ON CONFLICT (race_id) DO UPDATE SET race_name = EXCLUDED.race_name, total_race_laps = EXCLUDED.total_race_laps;
    """, race_records)

    # -------------------------------------------------------------------------
    # 3. SEED DIM_DATE
    # -------------------------------------------------------------------------
    print(">>> [3/6] Seeding Dimension: Calendar Dates...")
    date_records = []
    seen_dates = set()
    for _, row in df.iterrows():
        d_id = int(row['date_id'])
        if d_id not in seen_dates:
            seen_dates.add(d_id)
            d_str = str(row['race_date'])
            try:
                dt = datetime.strptime(d_str, '%Y-%m-%d')
            except Exception:
                dt = datetime(2024, 1, 1)
            date_records.append((
                d_id,
                dt.date(),
                dt.year,
                (dt.month - 1) // 3 + 1,
                dt.month,
                dt.strftime('%B'),
                dt.day,
                dt.strftime('%A'),
                dt.weekday() >= 5
            ))
    execute_values(cur, """
        INSERT INTO dim_date (date_id, full_date, year, quarter, month, month_name, day, day_name, is_weekend)
        VALUES %s
        ON CONFLICT (date_id) DO UPDATE SET full_date = EXCLUDED.full_date;
    """, date_records)

    # -------------------------------------------------------------------------
    # 4. SEED DIM_DRIVER & DIM_TEAM
    # -------------------------------------------------------------------------
    print(">>> [4/6] Seeding Dimensions: Drivers & Teams with Brand Liveries...")
    TEAM_COLORS = {
        'Red Bull': '#3671C6',
        'Mercedes': '#27F4D2',
        'Ferrari': '#E8002D',
        'McLaren': '#FF8000',
        'Aston Martin': '#229971',
        'Alpine': '#0093CC',
        'Williams': '#64C4FF',
        'RB': '#6692FF',
        'Toro Rosso': '#6692FF',
        'AlphaTauri': '#6692FF',
        'Kick Sauber': '#52E252',
        'Sauber': '#52E252',
        'Alfa Romeo': '#900000',
        'Haas': '#B6BABD',
        'Renault': '#FFF500',
        'Racing Point': '#F596C8',
        'Force India': '#FF8034',
        'Lotus': '#E5C467',
        'Brawn': '#B8FD38',
        'Toyota': '#TF0000',
        'BMW Sauber': '#001489'
    }

    team_records = []
    seen_teams = set()
    for _, row in df.iterrows():
        t_id = int(row['constructor_id'])
        if t_id not in seen_teams:
            seen_teams.add(t_id)
            t_name = str(row['constructor_name'])
            color = str(row.get('constructor_color_hex', ''))
            if not color or not color.startswith('#'):
                color = TEAM_COLORS.get(t_name, '#E10600')
            team_records.append((
                t_id,
                str(row.get('constructor_ref', t_name.lower().replace(' ', '_'))),
                t_name,
                str(row.get('constructor_nationality', 'British')),
                color,
                str(row.get('engine_supplier', 'Ferrari' if 'Ferrari' in t_name else ('Mercedes' if 'Mercedes' in t_name or 'McLaren' in t_name else 'Honda RBPT'))),
                str(row.get('team_principal', 'Team Principal')),
                str(row.get('constructor_nationality', 'United Kingdom'))
            ))
    execute_values(cur, """
        INSERT INTO dim_team (team_id, constructor_ref, team_name, nationality, color_hex, engine_supplier, team_principal, headquarters_country)
        VALUES %s
        ON CONFLICT (team_id) DO UPDATE SET team_name = EXCLUDED.team_name, color_hex = EXCLUDED.color_hex;
    """, team_records)

    driver_records = []
    seen_drivers = set()
    for _, row in df.iterrows():
        d_id = int(row['driver_id'])
        if d_id not in seen_drivers:
            seen_drivers.add(d_id)
            d_code = str(row.get('driver_code', 'DRV'))
            if not d_code or len(d_code) > 3:
                d_code = str(row.get('driver_code_clean', d_code[:3].upper()))
            driver_records.append((
                d_id,
                str(row.get('driver_ref', f'driver_{d_id}')),
                int(row['driver_number']) if pd.notnull(row.get('driver_number')) else d_id,
                d_code[:3].upper(),
                str(row.get('driver_first_name', '')),
                str(row.get('driver_last_name', '')),
                str(row['driver_name']),
                str(row['driver_dob']) if pd.notnull(row.get('driver_dob')) else None,
                str(row.get('driver_nationality', 'British')),
                float(row.get('driver_age_years', 28.0)) if pd.notnull(row.get('driver_age_years')) else 28.0
            ))
    execute_values(cur, """
        INSERT INTO dim_driver (driver_id, driver_ref, driver_number, driver_code, first_name, last_name, driver_name, dob, nationality, driver_age)
        VALUES %s
        ON CONFLICT (driver_id) DO UPDATE SET driver_name = EXCLUDED.driver_name, driver_code = EXCLUDED.driver_code;
    """, driver_records)

    # -------------------------------------------------------------------------
    # 5. SEED FACT_RACE_RESULTS
    # -------------------------------------------------------------------------
    print(f">>> [5/6] Ingesting {len(df):,} FACT_RACE_RESULTS records...")
    fact_results = []
    for _, row in df.iterrows():
        grid = int(row['grid_position']) if pd.notnull(row.get('grid_position')) else 20
        finish = int(row['finish_position']) if pd.notnull(row.get('finish_position')) else None
        gain = int(row.get('position_gain', (grid - finish) if finish else 0))
        pts = float(row['race_points']) if pd.notnull(row.get('race_points')) else 0.0

        fact_results.append((
            int(row['race_id']),
            int(row['driver_id']),
            int(row['constructor_id']),
            int(row['circuit_id']),
            int(row['date_id']),
            grid,
            finish,
            pts,
            int(row['laps_completed']) if pd.notnull(row.get('laps_completed')) else 52,
            int(row['fastest_lap_rank']) if pd.notnull(row.get('fastest_lap_rank')) else None,
            int(row['fastest_recorded_lap_ms']) if pd.notnull(row.get('fastest_recorded_lap_ms')) else 88500,
            int(row['average_lap_ms']) if pd.notnull(row.get('average_lap_ms')) else 91200,
            int(row['pit_stop_count']) if pd.notnull(row.get('pit_stop_count')) else 1,
            int(float(row.get('total_pit_duration_sec', 24.5)) * 1000) if pd.notnull(row.get('total_pit_duration_sec')) else 24500,
            gain,
            int(row.get('is_win', 1 if finish == 1 else 0)),
            int(row.get('is_podium', 1 if finish and finish <= 3 else 0)),
            int(row.get('is_pole', 1 if grid == 1 else 0)),
            int(row.get('is_dnf', 1 if not finish or finish > 20 else 0)),
            str(row.get('status_name', 'Finished' if finish and finish <= 20 else 'Retired'))
        ))

    execute_values(cur, """
        INSERT INTO fact_race_results (
            race_id, driver_id, team_id, circuit_id, date_id,
            grid_position, finishing_position, points, laps_completed,
            fastest_lap_rank, fastest_lap_time_ms, avg_lap_time_ms,
            pit_stop_count, total_pit_time_ms, positions_gained,
            is_win, is_podium, is_pole, is_dnf, status_text
        ) VALUES %s
        ON CONFLICT (race_id, driver_id) DO UPDATE SET points = EXCLUDED.points, finishing_position = EXCLUDED.finishing_position;
    """, fact_results)

    # -------------------------------------------------------------------------
    # 6. SEED FACT_LAP_TIMES (TELEMETRY SEEDING)
    # -------------------------------------------------------------------------
    print(">>> [6/6] Generating and seeding high-resolution telemetry lap records...")
    # Select races for detailed telemetry (2024, 2023, and key historical rounds)
    cur.execute("SELECT race_id, date_id FROM dim_race WHERE season_year >= 2023 ORDER BY race_id ASC;")
    telemetry_races = cur.fetchall()

    lap_records = []
    base_timestamp = datetime.now()

    for r_idx, (r_id, d_id) in enumerate(telemetry_races):
        # Top 10 drivers in this race
        cur.execute("SELECT driver_id, team_id, finishing_position FROM fact_race_results WHERE race_id = %s ORDER BY finishing_position ASC LIMIT 10;", (r_id,))
        drivers = cur.fetchall()

        for d_id_val, t_id_val, fin_pos in drivers:
            pos = fin_pos if fin_pos else 10
            base_lap_ms = 86000 + (pos * 350)

            for lap in range(1, 53):
                # Variance
                s1 = int(base_lap_ms * 0.32) + ((lap * 17 + pos * 5) % 800)
                s2 = int(base_lap_ms * 0.38) + ((lap * 23 + pos * 7) % 900)
                s3 = int(base_lap_ms * 0.30) + ((lap * 13 + pos * 3) % 700)
                total_lap = s1 + s2 + s3
                speed = 315.0 + ((lap * 7 + pos * 11) % 30) * 0.8
                is_pit = 1 if lap in [18, 38] else 0
                tyre_age = lap if lap < 18 else (lap - 18 if lap < 38 else lap - 38)
                compound_id = 1 if lap < 18 else (3 if lap < 38 else 2)

                # Generate realistic recorded_at timestamps (offset minutes in past)
                recorded_at = base_timestamp - pd.Timedelta(seconds=(52 - lap) * 90 + (r_idx * 3600))

                lap_records.append((
                    r_id,
                    d_id_val,
                    t_id_val,
                    6, # session_id = RACE
                    lap,
                    d_id,
                    compound_id,
                    total_lap,
                    pos,
                    s1,
                    s2,
                    s3,
                    speed,
                    tyre_age,
                    is_pit,
                    recorded_at
                ))

    print(f">>> Inserting {len(lap_records):,} telemetry rows into FACT_LAP_TIMES...")
    execute_values(cur, """
        INSERT INTO fact_lap_times (
            race_id, driver_id, team_id, session_id, lap_number, date_id,
            tyre_compound_id, lap_time_ms, lap_position, sector1_ms, sector2_ms,
            sector3_ms, speed_trap_kmh, tyre_age_laps, is_pit_lap, recorded_at
        ) VALUES %s
        ON CONFLICT (race_id, driver_id, session_id, lap_number) DO NOTHING;
    """, lap_records)

    conn.commit()
    conn.close()
    print(">>> [SUCCESS] Master ETL & Database Seeding Completed Cleanly!")

if __name__ == "__main__":
    run_master_etl()
