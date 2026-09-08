"""
Formula 1 Data Warehouse — Master ETL & Seeding Pipeline (2004-2024 Full Dataset)
Ingests the official master dataset F1_Warehouse_Master_65_Columns_2004_2024.csv (8,650 records)
and deploys pure Star Schema, high-density telemetry, and 3NF Snowflake Schema in SQLite (f1_warehouse.db).
"""

import sqlite3
import pandas as pd
import numpy as np
import datetime
import random
import os

CSV_PATH = "F1_Warehouse_Master_65_Columns_2004_2024.csv"
DB_PATH = "f1_warehouse.db"

# Team brand colors mapping across eras
CONSTRUCTOR_COLORS = {
    'red_bull': ('#3671C6', '#1E3D7B', 'Christian Horner', 'Honda RBPT'),
    'ferrari': ('#E8002D', '#9A001E', 'Frédéric Vasseur', 'Ferrari'),
    'mclaren': ('#FF8000', '#B35A00', 'Andrea Stella', 'Mercedes'),
    'mercedes': ('#27F4D2', '#00A389', 'Toto Wolff', 'Mercedes'),
    'aston_martin': ('#229971', '#136147', 'Mike Krack', 'Mercedes'),
    'alpine': ('#FF87BC', '#0090FF', 'Oliver Oakes', 'Renault'),
    'williams': ('#64C4FF', '#005AFF', 'James Vowles', 'Mercedes'),
    'rb': ('#6692FF', '#16348C', 'Laurent Mekies', 'Honda RBPT'),
    'alphatauri': ('#5E8FAA', '#00293F', 'Franz Tost', 'Honda RBPT'),
    'toro_rosso': ('#469BFF', '#001A30', 'Franz Tost', 'Ferrari'),
    'sauber': ('#52E252', '#000000', 'Mattia Binotto', 'Ferrari'),
    'alfa': ('#900000', '#000000', 'Frédéric Vasseur', 'Ferrari'),
    'haas': ('#B6BABD', '#E6002B', 'Ayao Komatsu', 'Ferrari'),
    'renault': ('#FFF500', '#111111', 'Cyril Abiteboul', 'Renault'),
    'force_india': ('#F596C8', '#FF8000', 'Vijay Mallya', 'Mercedes'),
    'racing_point': ('#F596C8', '#005AFF', 'Otmar Szafnauer', 'Mercedes'),
    'lotus_f1': ('#FFB800', '#111111', 'Gerard Lopez', 'Renault'),
    'lotus_racing': ('#004225', '#FFB800', 'Tony Fernandes', 'Renault'),
    'brawn': ('#BFFF00', '#FFFFFF', 'Ross Brawn', 'Mercedes'),
    'bmw_sauber': ('#002B49', '#FFFFFF', 'Mario Theissen', 'BMW'),
    'toyota': ('#EE1C25', '#FFFFFF', 'John Howett', 'Toyota'),
    'honda': ('#FFFFFF', '#EE1C25', 'Nick Fry', 'Honda'),
    'super_aguri': ('#CC0000', '#FFFFFF', 'Aguri Suzuki', 'Honda'),
    'marussia': ('#6E0000', '#000000', 'John Booth', 'Ferrari'),
    'manor': ('#0055A5', '#FF7F00', 'Dave Ryan', 'Mercedes'),
    'caterham': ('#00502F', '#A39382', 'Cyril Abiteboul', 'Renault'),
    'virgin': ('#000000', '#E50000', 'John Booth', 'Cosworth'),
    'hrt': ('#B89F5B', '#4D4D4D', 'Colin Kolles', 'Cosworth')
}

CIRCUIT_SVG_PATHS = {
    1: 'M150 150 C200 100 300 100 350 150 C400 200 380 350 320 400 C250 450 180 420 130 350 C90 280 100 200 150 150 Z', # Melbourne
    2: 'M120 180 L320 180 C360 200 380 240 360 280 L220 280 L250 350 L190 380 L140 330 L110 240 Z', # Sepang
    3: 'M120 180 L280 180 C310 180 340 200 340 230 L340 310 C340 340 310 360 280 360 L180 360 L140 400 L110 370 L110 240 Z', # Bahrain
    4: 'M140 180 L320 180 C360 210 340 270 300 290 L220 290 C190 330 220 380 280 380 C320 380 340 420 300 440 L160 440 C110 380 110 240 140 180 Z', # Catalunya
    6: 'M160 220 L260 220 C290 220 320 250 300 290 L240 320 L280 380 L220 420 L160 380 L180 300 L140 260 Z', # Monaco
    7: 'M120 180 L380 180 C400 210 390 240 360 250 L180 250 C150 280 160 320 200 330 L360 330 C390 350 380 390 340 400 L120 400 C90 350 90 230 120 180 Z', # Montreal
    9: 'M110 260 L240 160 C290 140 340 170 360 220 L380 320 C360 370 300 420 240 390 L180 410 C130 410 90 340 110 260 Z', # Silverstone
    13: 'M120 320 L160 180 C200 120 280 100 350 140 L400 240 C420 320 360 410 280 430 L180 410 C130 390 100 360 120 320 Z', # Spa
    14: 'M100 280 L180 140 C240 110 340 120 390 180 L420 320 C400 400 320 440 220 410 L130 390 C90 360 80 320 100 280 Z', # Monza
    15: 'M140 180 L320 180 C360 210 350 280 310 310 L240 310 L260 380 L200 420 L150 380 L170 270 L120 230 Z', # Singapore
    18: 'M120 290 L220 140 C280 120 360 160 380 230 L360 340 C320 410 250 430 190 390 L140 400 L110 340 Z', # Interlagos
    22: 'M120 200 C150 120 250 120 300 180 C350 240 300 320 250 300 C200 280 180 350 140 380 C100 410 80 280 120 200 Z', # Suzuka
    24: 'M130 200 L310 180 C360 200 370 270 330 310 L240 320 L270 390 L190 420 L150 370 L170 290 L110 250 Z', # Abu Dhabi
    70: 'M140 240 L340 160 C370 170 380 210 350 240 L260 290 C290 330 330 340 320 390 L180 410 C140 380 120 300 140 240 Z'  # Red Bull Ring
}

def seed_full_warehouse():
    print("================================================================================")
    print("  FORMULA 1 DATA WAREHOUSE — MASTER INGESTION & SEEDING (2004-2024)")
    print("================================================================================")

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Master CSV file '{CSV_PATH}' not found in workspace!")

    print(f"\n>>> [1/5] Loading master dataset '{CSV_PATH}'...")
    df = pd.read_csv(CSV_PATH)
    print(f"    Loaded {len(df):,} records spanning {df['season'].min()} to {df['season'].max()}.")

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")

    # Run DDL scripts
    with open("create_star_schema.sql", "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    with open("create_snowflake_schema.sql", "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    conn.commit()

    # 1. DIM_NATIONALITY (Snowflake)
    print(">>> [2/5] Seeding Snowflake Reference Dimensions...")
    unique_nats = sorted(df['driver_nationality'].dropna().unique())
    nat_rows = []
    nat_map = {}
    for idx, nat in enumerate(unique_nats, 1):
        nat_map[nat] = idx
        nat_rows.append((idx, nat, nat[:3].upper(), 'Global'))
    cur.executemany("INSERT INTO DIM_NATIONALITY (nationality_id, nationality_name, country_code, continent) VALUES (?, ?, ?, ?)", nat_rows)

    # 2. DIM_COUNTRY (Snowflake)
    unique_countries = sorted(df['circuit_country'].dropna().unique())
    country_rows = []
    country_map = {}
    for idx, ctry in enumerate(unique_countries, 1):
        country_map[ctry] = idx
        country_rows.append((idx, ctry, ctry[:2].upper(), ctry[:3].upper(), 'World'))
    cur.executemany("INSERT INTO DIM_COUNTRY (country_id, country_name, alpha2_code, alpha3_code, region) VALUES (?, ?, ?, ?, ?)", country_rows)

    # 3. DIM_ENGINE_SUPPLIER (Snowflake)
    engines = [
        (1, 'Ferrari', 'Italy', '1.6L V6 Turbo Hybrid / 2.4L V8'),
        (2, 'Mercedes-AMG High Performance Powertrains', 'United Kingdom', '1.6L V6 Turbo Hybrid / 2.4L V8'),
        (3, 'Honda RBPT', 'Japan', '1.6L V6 Turbo Hybrid'),
        (4, 'Renault', 'France', '1.6L V6 Turbo Hybrid / 2.4L V8'),
        (5, 'BMW', 'Germany', '2.4L V8 / 3.0L V10'),
        (6, 'Toyota', 'Japan', '2.4L V8 / 3.0L V10'),
        (7, 'Cosworth', 'United Kingdom', '2.4L V8')
    ]
    cur.executemany("INSERT INTO DIM_ENGINE_SUPPLIER (engine_supplier_id, supplier_name, headquarters_country, engine_architecture) VALUES (?, ?, ?, ?)", engines)

    # 4. DIM_TEAM_PRINCIPAL (Snowflake)
    principals = [
        (1, 'Christian Horner', 1, 2005),
        (2, 'Frédéric Vasseur', 1, 2023),
        (3, 'Andrea Stella', 1, 2023),
        (4, 'Toto Wolff', 1, 2013),
        (5, 'Mike Krack', 1, 2022),
        (6, 'Oliver Oakes', 1, 2024),
        (7, 'James Vowles', 1, 2023),
        (8, 'Franz Tost', 1, 2006),
        (9, 'Mattia Binotto', 1, 2019),
        (10, 'Ayao Komatsu', 1, 2024)
    ]
    cur.executemany("INSERT INTO DIM_TEAM_PRINCIPAL (principal_id, principal_name, nationality_id, appointment_year) VALUES (?, ?, ?, ?)", principals)

    # 5. DIM_LIVERY_SPONSOR (Snowflake)
    sponsors = [
        (1, 'Oracle', 'Technology', 2022),
        (2, 'HP', 'Technology', 2024),
        (3, 'Google Chrome', 'Technology', 2022),
        (4, 'Petronas', 'Energy', 2010),
        (5, 'Aramco', 'Energy', 2021),
        (6, 'BWT', 'Water Treatment', 2022),
        (7, 'Komatsu', 'Machinery', 2024),
        (8, 'Visa / Cash App', 'Finance', 2024),
        (9, 'Stake', 'Entertainment', 2024),
        (10, 'MoneyGram', 'Finance', 2023)
    ]
    cur.executemany("INSERT INTO DIM_LIVERY_SPONSOR (sponsor_id, sponsor_name, industry, contract_start_year) VALUES (?, ?, ?, ?)", sponsors)

    # 6. DIM_SEASON (Snowflake)
    seasons_unique = sorted(df['season'].unique())
    season_rows = []
    for yr in seasons_unique:
        era = "Ground Effect Hybrid" if yr >= 2022 else ("1.6L V6 Hybrid" if yr >= 2014 else "2.4L V8 Atmospheric")
        pts_system = "25-18-15 + FL" if yr >= 2019 else ("25-18-15" if yr >= 2010 else "10-8-6-5-4-3-2-1")
        total_rnds = int(df[df['season'] == yr]['round'].max())
        season_rows.append((int(yr), era, pts_system, "Sprint Shootout" if yr >= 2021 else "None", total_rnds))
    cur.executemany("INSERT INTO DIM_SEASON (season_year, technical_regulations_era, points_system_version, sprint_format_type, total_rounds_scheduled) VALUES (?, ?, ?, ?, ?)", season_rows)

    # 7. DIM_SESSION & DIM_TYRE_COMPOUND (Star)
    sessions = [
        (1, 'FP1', 'Free Practice 1', 'Practice'),
        (2, 'FP2', 'Free Practice 2', 'Practice'),
        (3, 'FP3', 'Free Practice 3', 'Practice'),
        (4, 'QUAL', 'Qualifying Session', 'Qualifying'),
        (5, 'SPRINT', 'Sprint Race', 'Sprint'),
        (6, 'RACE', 'Grand Prix Main Race', 'Race')
    ]
    cur.executemany("INSERT INTO DIM_SESSION (session_id, session_code, session_name, session_type) VALUES (?, ?, ?, ?)", sessions)

    compounds = [
        (1, 'SOFT', 'Soft (Red)', '#FF2D55', 'Dry'),
        (2, 'MEDIUM', 'Medium (Yellow)', '#FFD60A', 'Dry'),
        (3, 'HARD', 'Hard (White)', '#F2F2F7', 'Dry'),
        (4, 'INTER', 'Intermediate (Green)', '#30D158', 'Wet'),
        (5, 'WET', 'Full Wet (Blue)', '#0A84FF', 'Wet')
    ]
    cur.executemany("INSERT INTO DIM_TYRE_COMPOUND (compound_id, compound_code, compound_name, color_hex, compound_type) VALUES (?, ?, ?, ?, ?)", compounds)

    # 8. DIM_STATUS
    unique_statuses = sorted(df['race_status'].dropna().unique())
    status_map = {s: idx + 1 for idx, s in enumerate(unique_statuses)}
    status_rows = [(idx + 1, s, 1 if ('Finished' in s or '+' in s) else 0) for idx, s in enumerate(unique_statuses)]
    cur.executemany("INSERT INTO DIM_STATUS (status_id, status_description, is_classified) VALUES (?, ?, ?)", status_rows)

    # 9. DIM_DATE
    print(">>> [3/5] Seeding Calendar Dates & Dimensions...")
    unique_dates = sorted(df['race_date'].dropna().unique())
    date_rows_star = []
    date_rows_snow = []
    for rdate in unique_dates:
        dt = datetime.datetime.strptime(rdate, '%Y-%m-%d')
        d_id = int(rdate.replace('-', ''))
        q = (dt.month - 1) // 3 + 1
        date_rows_star.append((d_id, rdate, dt.year, q, dt.month, dt.strftime('%B'), dt.isoweekday(), dt.strftime('%A')))
        date_rows_snow.append((d_id, rdate, dt.year, q, dt.month, dt.strftime('%B'), dt.isoweekday(), dt.strftime('%A')))
    cur.executemany("INSERT INTO DIM_DATE (date_id, full_date, year, quarter, month, month_name, day_of_week, day_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", date_rows_star)
    cur.executemany("INSERT INTO DIM_DATE_SNOWFLAKE (date_id, full_date, season_year, quarter, month, month_name, day_of_week, day_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", date_rows_snow)

    # 10. DIM_CONSTRUCTOR
    df_const = df[['constructor_id', 'constructor_ref', 'constructor_name', 'constructor_nationality']].drop_duplicates('constructor_id')
    for _, row in df_const.iterrows():
        c_id = int(row['constructor_id'])
        c_ref = str(row['constructor_ref'])
        c_name = str(row['constructor_name'])
        c_nat = str(row['constructor_nationality']) if pd.notna(row['constructor_nationality']) else 'British'
        
        info = CONSTRUCTOR_COLORS.get(c_ref, ('#E10600', '#333333', 'Team Principal', 'Customer Engine'))
        color_hex = info[0]
        sec_color = info[1]
        principal = info[2]
        engine = info[3]
        
        # Star
        cur.execute(
            "INSERT INTO DIM_CONSTRUCTOR (constructor_id, constructor_ref, constructor_name, constructor_nationality, color_hex, secondary_color_hex, team_principal, power_unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (c_id, c_ref, c_name, c_nat, color_hex, sec_color, principal, engine)
        )
        # Snowflake
        nat_id = nat_map.get(c_nat, 1)
        cur.execute(
            "INSERT INTO DIM_CONSTRUCTOR_SNOWFLAKE (constructor_id, constructor_ref, constructor_name, nationality_id, engine_supplier_id, principal_id, sponsor_id, color_hex) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (c_id, c_ref, c_name, nat_id, 1, 1, 1, color_hex)
        )

    # 11. DIM_DRIVER
    df_drv = df[['driver_id', 'driver_ref', 'driver_code', 'driver_name', 'driver_dob', 'driver_nationality', 'car_number']].drop_duplicates('driver_id')
    for _, row in df_drv.iterrows():
        d_id = int(row['driver_id'])
        d_ref = str(row['driver_ref'])
        d_code = str(row['driver_code']) if pd.notna(row['driver_code']) and str(row['driver_code']) != '\\N' else d_ref[:3].upper()
        d_name = str(row['driver_name'])
        d_dob = str(row['driver_dob']) if pd.notna(row['driver_dob']) else '1990-01-01'
        d_nat = str(row['driver_nationality']) if pd.notna(row['driver_nationality']) else 'British'
        car_num = int(row['car_number']) if pd.notna(row['car_number']) and str(row['car_number']) != '\\N' else d_id
        flag_code = d_nat[:2].upper()
        headshot = f"https://media.formula1.com/d_driver_fallback_image.png"

        cur.execute(
            "INSERT INTO DIM_DRIVER (driver_id, driver_ref, driver_code, driver_name, driver_number, driver_dob, driver_nationality, driver_flag_code, headshot_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (d_id, d_ref, d_code, d_name, car_num, d_dob, d_nat, flag_code, headshot)
        )
        nat_id = nat_map.get(d_nat, 1)
        cur.execute(
            "INSERT INTO DIM_DRIVER_SNOWFLAKE (driver_id, driver_ref, driver_code, driver_name, driver_dob, nationality_id, headshot_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (d_id, d_ref, d_code, d_name, d_dob, nat_id, headshot)
        )
        cur.execute(
            "INSERT INTO DIM_DRIVER_NUMBER_HISTORY (history_id, driver_id, season_year, permanent_car_number, is_reigning_champion_override) VALUES (?, ?, ?, ?, ?)",
            (d_id, d_id, 2024, car_num, 1 if d_id in [1, 830] else 0)
        )

    # 12. DIM_CIRCUIT & DIM_RACE
    df_races = df[[
        'race_id', 'season', 'round', 'race_name', 'race_date', 'race_start_time',
        'circuit_id', 'circuit_name', 'circuit_location', 'circuit_country',
        'circuit_latitude', 'circuit_longitude', 'circuit_altitude_m'
    ]].drop_duplicates('race_id')

    # Seed Circuits
    df_circ = df[[
        'circuit_id', 'circuit_name', 'circuit_location', 'circuit_country',
        'circuit_latitude', 'circuit_longitude', 'circuit_altitude_m'
    ]].drop_duplicates('circuit_id')

    for _, row in df_circ.iterrows():
        circ_id = int(row['circuit_id'])
        c_name = str(row['circuit_name'])
        c_loc = str(row['circuit_location']) if pd.notna(row['circuit_location']) else ''
        c_ctry = str(row['circuit_country']) if pd.notna(row['circuit_country']) else 'Unknown'
        c_lat = float(row['circuit_latitude']) if pd.notna(row['circuit_latitude']) else 0.0
        c_lng = float(row['circuit_longitude']) if pd.notna(row['circuit_longitude']) else 0.0
        c_alt = int(row['circuit_altitude_m']) if pd.notna(row['circuit_altitude_m']) and str(row['circuit_altitude_m']) != '\\N' else 0
        ctry_id = country_map.get(c_ctry, 1)

        cur.execute(
            "INSERT INTO DIM_CIRCUIT_SNOWFLAKE (circuit_id, circuit_ref, circuit_name, circuit_location, country_id, circuit_latitude, circuit_longitude, circuit_altitude_m) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (circ_id, f"circuit_{circ_id}", c_name, c_loc, ctry_id, c_lat, c_lng, c_alt)
        )
        cur.execute(
            "INSERT INTO DIM_CIRCUIT_LAYOUT_HISTORY (layout_id, circuit_id, layout_version_name, length_km, number_of_corners, drs_zones_count, valid_from_year, valid_to_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (circ_id, circ_id, 'Grand Prix Layout', 5.3, 16, 2, 2004, None)
        )

    for _, row in df_races.iterrows():
        r_id = int(row['race_id'])
        yr = int(row['season'])
        rnd = int(row['round'])
        r_name = str(row['race_name'])
        r_date = str(row['race_date'])
        r_time = str(row['race_start_time']) if pd.notna(row['race_start_time']) else '13:00:00'
        circ_id = int(row['circuit_id'])
        c_name = str(row['circuit_name'])
        c_loc = str(row['circuit_location']) if pd.notna(row['circuit_location']) else ''
        c_ctry = str(row['circuit_country']) if pd.notna(row['circuit_country']) else 'Unknown'
        c_lat = float(row['circuit_latitude']) if pd.notna(row['circuit_latitude']) else 0.0
        c_lng = float(row['circuit_longitude']) if pd.notna(row['circuit_longitude']) else 0.0
        c_alt = int(row['circuit_altitude_m']) if pd.notna(row['circuit_altitude_m']) and str(row['circuit_altitude_m']) != '\\N' else 0
        svg_path = CIRCUIT_SVG_PATHS.get(circ_id, 'M120 200 C150 120 250 120 300 180 C350 240 300 320 250 300 C200 280 180 350 140 380 C100 410 80 280 120 200 Z')

        # Star
        cur.execute("""
            INSERT INTO DIM_RACE (
                race_id, season_year, round, race_name, race_date, race_start_time,
                circuit_id, circuit_name, circuit_location, circuit_country,
                circuit_latitude, circuit_longitude, circuit_altitude_m, circuit_length_km,
                total_race_laps, lap_record_time, lap_record_holder, lap_record_year, track_svg_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r_id, yr, rnd, r_name, r_date, r_time, circ_id, c_name, c_loc, c_ctry, c_lat, c_lng, c_alt, 5.4, 55, '1:27.097', 'Lewis Hamilton', 2020, svg_path))

        # Snowflake
        cur.execute("""
            INSERT INTO DIM_RACE_SNOWFLAKE (
                race_id, season_year, round, race_name, circuit_id, layout_id, race_date, race_start_time, total_race_laps
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r_id, yr, rnd, r_name, circ_id, circ_id, r_date, r_time, 55))

    conn.commit()

    # 13. FACT_RACE_RESULTS
    print(f"\n>>> [4/5] Ingesting {len(df):,} FACT_RACE_RESULTS across 2004-2024...")
    fact_results_star = []
    fact_results_snow = []

    for idx, row in df.iterrows():
        res_id = idx + 1
        r_id = int(row['race_id'])
        d_id = int(row['driver_id'])
        c_id = int(row['constructor_id'])
        d_key = int(str(row['race_date']).replace('-', ''))
        st_id = status_map.get(row['race_status'], 1)
        
        car_num = int(row['car_number']) if pd.notna(row['car_number']) and str(row['car_number']) != '\\N' else None
        grid_pos = int(row['grid_position']) if pd.notna(row['grid_position']) else 20
        qual_pos = int(row['qualifying_position']) if pd.notna(row['qualifying_position']) and str(row['qualifying_position']) != '\\N' else grid_pos
        qual_time = float(row['qualifying_best_time_sec']) if pd.notna(row['qualifying_best_time_sec']) and str(row['qualifying_best_time_sec']) != '\\N' else None
        
        fin_pos = int(row['finish_position']) if pd.notna(row['finish_position']) and str(row['finish_position']) != '\\N' else None
        fin_text = str(row['finish_position_text']) if pd.notna(row['finish_position_text']) else 'DNF'
        pts = float(row['race_points']) if pd.notna(row['race_points']) else 0.0
        laps = int(row['race_laps']) if pd.notna(row['race_laps']) else 0
        r_time = str(row['race_time']) if pd.notna(row['race_time']) and str(row['race_time']) != '\\N' else None
        r_ms = int(float(row['race_milliseconds'])) if pd.notna(row['race_milliseconds']) and str(row['race_milliseconds']) != '\\N' and float(row['race_milliseconds']) > 0 else None

        fl_num = int(row['fastest_lap_number']) if pd.notna(row['fastest_lap_number']) and str(row['fastest_lap_number']) != '\\N' else None
        fl_rank = int(row['fastest_lap_rank']) if pd.notna(row['fastest_lap_rank']) and str(row['fastest_lap_rank']) != '\\N' else None
        fl_time = str(row['fastest_lap_time']) if pd.notna(row['fastest_lap_time']) and str(row['fastest_lap_time']) != '\\N' else None
        fl_speed = float(row['fastest_lap_speed']) if pd.notna(row['fastest_lap_speed']) and str(row['fastest_lap_speed']) != '\\N' else None

        pit_cnt = int(row['pit_stop_count']) if pd.notna(row['pit_stop_count']) and str(row['pit_stop_count']) != '\\N' else 0
        pit_tot = float(row['total_pit_duration_sec']) if pd.notna(row['total_pit_duration_sec']) and str(row['total_pit_duration_sec']) != '\\N' else 0.0
        pit_avg = float(row['avg_pit_duration_sec']) if pd.notna(row['avg_pit_duration_sec']) and str(row['avg_pit_duration_sec']) != '\\N' else 0.0
        pit_fst = float(row['fastest_pit_duration_sec']) if pd.notna(row['fastest_pit_duration_sec']) and str(row['fastest_pit_duration_sec']) != '\\N' else 0.0
        last_pit = int(row['last_pit_lap']) if pd.notna(row['last_pit_lap']) and str(row['last_pit_lap']) != '\\N' else 0

        d_pts = float(row['driver_standing_points']) if pd.notna(row['driver_standing_points']) else 0.0
        d_pos = int(row['driver_championship_position']) if pd.notna(row['driver_championship_position']) and str(row['driver_championship_position']) != '\\N' else 1
        d_wins = int(row['driver_championship_wins']) if pd.notna(row['driver_championship_wins']) and str(row['driver_championship_wins']) != '\\N' else 0

        c_pts = float(row['constructor_standing_points']) if pd.notna(row['constructor_standing_points']) else 0.0
        c_pos = int(row['constructor_championship_position']) if pd.notna(row['constructor_championship_position']) and str(row['constructor_championship_position']) != '\\N' else 1
        c_wins = int(row['constructor_championship_wins']) if pd.notna(row['constructor_championship_wins']) and str(row['constructor_championship_wins']) != '\\N' else 0

        d_gap = float(row['driver_standing_gap_to_leader']) if pd.notna(row['driver_standing_gap_to_leader']) and str(row['driver_standing_gap_to_leader']) != '\\N' else 0.0
        c_gap = float(row['constructor_standing_gap_to_leader']) if pd.notna(row['constructor_standing_gap_to_leader']) and str(row['constructor_standing_gap_to_leader']) != '\\N' else 0.0

        pos_gain = int(row['position_gain']) if pd.notna(row['position_gain']) and str(row['position_gain']) != '\\N' else (grid_pos - (fin_pos if fin_pos else 20))
        q_delta = int(float(row['qualifying_to_finish_delta'])) if pd.notna(row['qualifying_to_finish_delta']) and str(row['qualifying_to_finish_delta']) != '\\N' else pos_gain

        is_pol = int(row['is_pole']) if pd.notna(row['is_pole']) else (1 if grid_pos == 1 else 0)
        is_pod = int(row['is_podium']) if pd.notna(row['is_podium']) else (1 if fin_pos and fin_pos <= 3 else 0)
        is_w = int(row['is_win']) if pd.notna(row['is_win']) else (1 if fin_pos == 1 else 0)
        is_t10 = int(row['is_top_10']) if pd.notna(row['is_top_10']) else (1 if fin_pos and fin_pos <= 10 else 0)
        is_d = int(row['is_dnf']) if pd.notna(row['is_dnf']) else (1 if fin_pos is None else 0)

        fact_results_star.append((
            res_id, r_id, d_id, c_id, d_key, st_id,
            car_num, grid_pos, qual_pos, qual_time,
            fin_pos, fin_text, pts, laps, r_time, r_ms,
            fl_num, fl_rank, fl_time, fl_speed,
            pit_cnt, pit_tot, pit_avg, pit_fst, last_pit,
            d_pts, d_pos, d_wins,
            c_pts, c_pos, c_wins,
            d_gap, c_gap,
            pos_gain, q_delta,
            is_pol, is_pod, is_w, is_t10, is_d
        ))

        fact_results_snow.append((
            res_id, r_id, d_id, c_id, d_key, st_id,
            grid_pos, fin_pos, pts, laps, fl_time,
            pit_cnt, pit_tot, d_pts, is_w, is_pod
        ))

    cur.executemany("""
        INSERT INTO FACT_RACE_RESULTS (
            result_id, race_id, driver_id, constructor_id, date_id, status_id,
            car_number, grid_position, qualifying_position, qualifying_best_time_sec,
            finish_position, finish_position_text, race_points, race_laps, race_time, race_milliseconds,
            fastest_lap_number, fastest_lap_rank, fastest_lap_time, fastest_lap_speed,
            pit_stop_count, total_pit_duration_sec, avg_pit_duration_sec, fastest_pit_duration_sec, last_pit_lap,
            driver_standing_points, driver_championship_position, driver_championship_wins,
            constructor_standing_points, constructor_championship_position, constructor_championship_wins,
            driver_standing_gap_to_leader, constructor_standing_gap_to_leader,
            position_gain, qualifying_to_finish_delta,
            is_pole, is_podium, is_win, is_top_10, is_dnf
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?,
            ?, ?, ?, ?, ?
        )
    """, fact_results_star)

    cur.executemany("""
        INSERT INTO FACT_RACE_RESULTS_SNOWFLAKE (
            result_id, race_id, driver_id, constructor_id, date_id, status_id,
            grid_position, finish_position, race_points, race_laps, fastest_lap_time,
            pit_stop_count, total_pit_duration_sec, driver_standing_points, is_win, is_podium
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, fact_results_snow)
    conn.commit()

    # 14. GENERATE HIGH-DENSITY FACT_LAP_TIMES TELEMETRY
    print("\n>>> [5/5] Generating per-lap telemetry time-series records for FACT_LAP_TIMES...")
    lap_id_counter = 1
    lap_records = []

    # Featured races across eras: 2024 British GP, 2024 Monaco, 2023 Silverstone, 2021 Abu Dhabi, 2012 Brazil, 2008 British GP, etc.
    # We generate lap telemetry for all races in recent seasons (2020-2024) + key historic races in 2008-2019
    recent_races = df[['race_id', 'season', 'round', 'race_name', 'race_date']].drop_duplicates('race_id')
    
    for _, r_meta in recent_races.iterrows():
        r_id = int(r_meta['race_id'])
        yr = int(r_meta['season'])
        d_key = int(str(r_meta['race_date']).replace('-', ''))

        # Fetch race entries
        cur.execute("""
            SELECT driver_id, constructor_id, finish_position, race_laps, fastest_lap_time, fastest_lap_speed, is_dnf
            FROM FACT_RACE_RESULTS
            WHERE race_id = ?
            ORDER BY finish_position ASC
        """, (r_id,))
        drivers_in_race = cur.fetchall()
        if not drivers_in_race:
            continue

        # Determine lap count for telemetry
        is_deep_telemetry = (yr >= 2020) or (r_meta['round'] in [1, 5, 9, 14]) or (yr in [2008, 2012, 2016, 2021])
        laps_to_sim = 52 if is_deep_telemetry else min(20, max(5, max([d[3] for d in drivers_in_race] or [50])))

        for lap_num in range(1, laps_to_sim + 1):
            for rank, d_row in enumerate(drivers_in_race, 1):
                d_id = d_row[0]
                c_id = d_row[1]
                fin_pos = d_row[2] or 20
                max_laps = d_row[3] or 55
                fl_time = d_row[4]
                fl_spd = d_row[5] or 235.0
                is_dnf = d_row[6]

                if is_dnf and lap_num > (max_laps - 3):
                    continue

                is_pit = 1 if lap_num in [18, 38] else 0
                compound_id = 3 if lap_num > 38 else (2 if lap_num > 18 else 1)
                
                # Base pace
                base_lap_ms = 88000 + (fin_pos * 180) + (lap_num * 40) + random.randint(-200, 200) + (22000 if is_pit else 0)
                s1_ms = int(base_lap_ms * 0.31)
                s2_ms = int(base_lap_ms * 0.39)
                s3_ms = base_lap_ms - (s1_ms + s2_ms)

                lap_sec = base_lap_ms / 1000.0
                lap_str = f"{int(lap_sec // 60)}:{lap_sec % 60:06.3f}"
                s1_str = f"{s1_ms / 1000.0:.3f}"
                s2_str = f"{s2_ms / 1000.0:.3f}"
                s3_str = f"{s3_ms / 1000.0:.3f}"

                gap_leader = (fin_pos - 1) * 1400 + (lap_num * 80)
                interval = 1200 if rank > 1 else 0

                lap_records.append((
                    lap_id_counter, r_id, d_id, c_id, 6, d_key, compound_id,
                    lap_num, rank, lap_str, base_lap_ms, s1_ms, s2_ms, s3_ms,
                    s1_str, s2_str, s3_str, round(fl_spd + random.uniform(-2, 3), 1),
                    220.5, lap_num % 20, min(95.0, lap_num * 2.8), (1 if lap_num <= 18 else (2 if lap_num <= 38 else 3)),
                    is_pit, 22000 if is_pit else 0, gap_leader, interval,
                    74.5, 9, 54, 1 if interval < 1000 and not is_pit else 0,
                    1 if rank == 1 and lap_num == 48 else 0,
                    1 if rank == 1 and lap_num == 48 else 0,
                    1 if rank == 1 and lap_num == 48 else 0,
                    1 if rank == 1 and lap_num == 48 else 0
                ))
                lap_id_counter += 1

                if len(lap_records) >= 20000:
                    cur.executemany("""
                        INSERT INTO FACT_LAP_TIMES (
                            lap_id, race_id, driver_id, constructor_id, session_id, date_id, compound_id,
                            lap_number, lap_position, lap_time_str, lap_time_ms, sector1_ms, sector2_ms, sector3_ms,
                            sector1_str, sector2_str, sector3_str, speed_trap_kmh, avg_speed_kmh,
                            tyre_age_laps, tyre_wear_pct, stint_number, is_pit_lap, pit_duration_ms,
                            gap_to_leader_ms, interval_to_ahead_ms, throttle_pct_full, brake_events_count, gear_shifts_count,
                            drs_activated, s1_is_purple, s2_is_purple, s3_is_purple, lap_is_fastest
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, lap_records)
                    lap_records = []

    if lap_records:
        cur.executemany("""
            INSERT INTO FACT_LAP_TIMES (
                lap_id, race_id, driver_id, constructor_id, session_id, date_id, compound_id,
                lap_number, lap_position, lap_time_str, lap_time_ms, sector1_ms, sector2_ms, sector3_ms,
                sector1_str, sector2_str, sector3_str, speed_trap_kmh, avg_speed_kmh,
                tyre_age_laps, tyre_wear_pct, stint_number, is_pit_lap, pit_duration_ms,
                gap_to_leader_ms, interval_to_ahead_ms, throttle_pct_full, brake_events_count, gear_shifts_count,
                drs_activated, s1_is_purple, s2_is_purple, s3_is_purple, lap_is_fastest
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, lap_records)

    conn.commit()
    print(">>> Master Data Warehouse seeding successfully finished!")

    # Summary Counts
    for tbl in ['DIM_DRIVER', 'DIM_CONSTRUCTOR', 'DIM_RACE', 'DIM_CIRCUIT_SNOWFLAKE', 'FACT_RACE_RESULTS', 'FACT_LAP_TIMES']:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"    - {tbl}: {cur.fetchone()[0]:,} rows")

    conn.close()

if __name__ == "__main__":
    seed_full_warehouse()
