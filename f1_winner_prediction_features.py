"""
Formula 1 Race Winner Prediction Feature Enrichment Engine
==========================================================
Enriches the 2004-2024 F1 Data Warehouse dataset with high-fidelity:
1. CAR FEATURES (Engine Architecture, BHP, Minimum Weight, Aero Regulation Era, Chassis Models, Reliability Score, Pace Index)
2. LAP RECORD DATA (Official All-Time Circuit Race Lap Records, Holders, Years, Quali/Race Deltas to Track Record)
3. PIT STOP METRICS (Circuit Pit Lane Time Loss, Pit Crew Efficiency Score, Total Strategy Loss, Stationary Stop Estimates)

Outputs:
- F1_ML_Winner_Prediction_Dataset.csv
- SQLite Table: ML_WINNER_PREDICTION_FEATURES in f1_warehouse.db
"""

import sqlite3
import pandas as pd
import numpy as np
import os
import re

# -----------------------------------------------------------------------------
# 1. OFFICIAL ALL-TIME CIRCUIT RACE LAP RECORDS (Official FIA / F1 Records)
# -----------------------------------------------------------------------------
CIRCUIT_LAP_RECORDS = {
    # circuit_id: (record_sec, record_str, holder_name, record_year, pit_lane_loss_sec)
    1: (79.813, "1:19.813", "Charles Leclerc", 2024, 21.0),    # Albert Park (Melbourne)
    2: (94.080, "1:34.080", "Sebastian Vettel", 2017, 22.0),   # Sepang
    3: (91.447, "1:31.447", "Pedro de la Rosa", 2005, 22.5),   # Bahrain (Sakhir)
    4: (76.330, "1:16.330", "Max Verstappen", 2023, 22.0),    # Barcelona-Catalunya
    5: (84.770, "1:24.770", "Juan Pablo Montoya", 2005, 21.5),# Istanbul Park
    6: (72.909, "1:12.909", "Lewis Hamilton", 2021, 19.4),     # Monaco
    7: (73.078, "1:13.078", "Valtteri Bottas", 2019, 20.2),    # Gilles Villeneuve (Montreal)
    8: (75.377, "1:15.377", "Michael Schumacher", 2004, 21.0), # Magny-Cours
    9: (87.097, "1:27.097", "Max Verstappen", 2020, 20.5),    # Silverstone
    10: (73.780, "1:13.780", "Kimi Räikkönen", 2004, 20.8),   # Hockenheimring
    11: (76.627, "1:16.627", "Lewis Hamilton", 2020, 21.5),    # Hungaroring
    12: (98.683, "1:38.683", "Timo Glock", 2009, 21.0),        # Valencia Street Circuit
    13: (104.701, "1:44.701", "Sergio Perez", 2024, 23.8),     # Spa-Francorchamps
    14: (80.901, "1:20.901", "Lando Norris", 2025, 23.2),      # Monza (1:21.046 Barrichello / 1:20.901 Norris)
    15: (94.486, "1:34.486", "Daniel Ricciardo", 2024, 27.8),  # Marina Bay (Singapore)
    16: (77.287, "1:17.287", "Lewis Hamilton", 2008, 21.5),    # Fuji Speedway
    17: (92.238, "1:32.238", "Michael Schumacher", 2004, 22.8),# Shanghai
    18: (70.540, "1:10.540", "Valtteri Bottas", 2018, 21.2),   # Interlagos (São Paulo)
    19: (70.399, "1:10.399", "Rubens Barrichello", 2004, 21.0),# Indianapolis
    20: (88.352, "1:28.352", "Max Verstappen", 2020, 21.5),    # Nürburgring
    21: (75.484, "1:15.484", "Lewis Hamilton", 2020, 24.0),    # Imola
    22: (90.965, "1:30.965", "Andrea Kimi Antonelli", 2025, 22.4), # Suzuka (1:30.983 Hamilton)
    24: (86.103, "1:26.103", "Max Verstappen", 2021, 21.6),    # Yas Marina
    32: (77.774, "1:17.774", "Valtteri Bottas", 2021, 22.0),   # Hermanos Rodriguez (Mexico)
    34: (92.740, "1:32.740", "Sebastian Vettel", 2019, 21.0),  # Paul Ricard
    35: (99.605, "1:39.605", "Sebastian Vettel", 2011, 22.0),  # Korean Int Circuit
    39: (71.097, "1:11.097", "Lewis Hamilton", 2021, 20.1),    # Zandvoort
    68: (87.249, "1:27.249", "Sebastian Vettel", 2011, 21.5),  # Buddh (India)
    69: (96.169, "1:36.169", "Charles Leclerc", 2019, 21.8),   # COTA (Austin)
    70: (65.619, "1:05.619", "Carlos Sainz", 2020, 20.0),      # Red Bull Ring (Spielberg)
    71: (95.761, "1:35.761", "Lewis Hamilton", 2019, 23.0),    # Sochi Autodrom
    73: (103.009, "1:43.009", "Charles Leclerc", 2019, 21.5),  # Baku City Circuit
    75: (78.750, "1:18.750", "Lewis Hamilton", 2020, 21.0),    # Portimão (Algarve)
    76: (78.833, "1:18.833", "Lewis Hamilton", 2020, 21.5),    # Mugello
    77: (90.734, "1:30.734", "Lewis Hamilton", 2021, 20.8),    # Jeddah Corniche
    78: (84.319, "1:24.319", "Max Verstappen", 2023, 21.5),    # Losail (Qatar)
    79: (89.708, "1:29.708", "Max Verstappen", 2023, 21.4),    # Miami
    80: (95.490, "1:35.490", "Oscar Piastri", 2023, 21.0),     # Las Vegas
}

# Default fallback for unmapped circuits
DEFAULT_CIRCUIT_RECORD = (85.0, "1:25.000", "Formula 1 Record", 2020, 21.5)

# -----------------------------------------------------------------------------
# 2. CAR SPECIFICATIONS ACROSS ERAS (2004–2024)
# -----------------------------------------------------------------------------
ERA_SPECS = {
    # Era Name: (engine_arch, min_weight_kg, base_bhp, max_rpm, aero_type)
    (2004, 2005): ("3.0L Naturally Aspirated V10", 605, 930, 19000, "V10 Extreme Aero & Chimneys"),
    (2006, 2008): ("2.4L Naturally Aspirated V8", 605, 760, 19000, "V8 High Downforce & Winglets"),
    (2009, 2013): ("2.4L Naturally Aspirated V8 + KERS (60kW)", 640, 770, 18000, "V8 Blown Diffuser & Narrow Wing"),
    (2014, 2016): ("1.6L V6 Turbocharged Hybrid (120kW MGU-K)", 702, 875, 15000, "Turbo Hybrid Classic (Narrow Track)"),
    (2017, 2021): ("1.6L V6 Turbocharged Hybrid (120kW MGU-K + MGU-H)", 746, 1005, 15000, "Turbo Hybrid Wide Body & High Downforce"),
    (2022, 2024): ("1.6L V6 Turbocharged Hybrid (E10 Sustainable Fuel)", 798, 1025, 15000, "Ground Effect Venturi Tunnels (18-inch Wheels)"),
}

# Team Power Unit Supplier Mapping (by era/season)
def get_engine_supplier_for_constructor(constructor_ref: str, season: int) -> str:
    ref = str(constructor_ref).lower().strip()
    if "ferrari" in ref:
        return "Ferrari"
    if "mercedes" in ref or "brawn" in ref:
        return "Mercedes"
    if "red_bull" in ref or "red bull" in ref:
        if season == 2005:
            return "Cosworth"
        elif season == 2006:
            return "Ferrari"
        elif season <= 2018:
            return "Renault"
        elif season <= 2021:
            return "Honda"
        else:
            return "Red Bull Powertrains / Honda"
    if "mclaren" in ref:
        if season <= 2014:
            return "Mercedes"
        elif season <= 2017:
            return "Honda"
        elif season <= 2020:
            return "Renault"
        else:
            return "Mercedes"
    if "renault" in ref or "alpine" in ref or "lotus_f1" in ref:
        return "Renault"
    if "aston_martin" in ref or "racing_point" in ref or "force_india" in ref:
        if season == 2008:
            return "Ferrari"
        return "Mercedes"
    if "williams" in ref:
        if season <= 2005:
            return "BMW"
        elif season == 2006:
            return "Cosworth"
        elif season <= 2009:
            return "Toyota"
        elif season <= 2011:
            return "Cosworth"
        elif season <= 2013:
            return "Renault"
        else:
            return "Mercedes"
    if "sauber" in ref or "alfa" in ref or "rb" in ref or "toro_rosso" in ref or "alphatauri" in ref or "haas" in ref:
        if "toro_rosso" in ref or "alphatauri" in ref or ref == "rb":
            if season == 2006:
                return "Cosworth"
            elif season <= 2013:
                return "Ferrari"
            elif season <= 2015:
                return "Renault"
            elif season == 2016:
                return "Ferrari"
            elif season == 2017:
                return "Renault"
            elif season <= 2021:
                return "Honda"
            else:
                return "Red Bull Powertrains / Honda"
        if "bmw_sauber" in ref or (ref == "sauber" and 2006 <= season <= 2009):
            return "BMW"
        return "Ferrari"
    if "toyota" in ref:
        return "Toyota"
    if "bar" in ref or "honda" in ref or "super_aguri" in ref:
        return "Honda"
    if "jordan" in ref or "minardi" in ref or "spyker" in ref or "midland" in ref:
        return "Cosworth" if season <= 2005 else "Ferrari"
    return "Independent Supplier"

# Team Pit Crew Benchmark Base Rating (0–100 score)
PIT_CREW_BENCHMARKS = {
    "red_bull": 98.0,
    "ferrari": 91.5,
    "mclaren": 94.0,
    "mercedes": 93.0,
    "aston_martin": 88.0,
    "racing_point": 87.0,
    "force_india": 86.0,
    "alpine": 86.5,
    "renault": 85.0,
    "williams": 89.0,     # Williams had world-record pit stop runs (DHL award 2016)
    "alphatauri": 85.0,
    "toro_rosso": 84.0,
    "rb": 85.5,
    "haas": 82.0,
    "sauber": 78.0,
    "alfa": 80.0,
    "toyota": 84.0,
    "bmw_sauber": 86.0,
    "brawn": 92.0,
}

def parse_time_str_to_sec(time_val) -> float:
    """Converts strings like '1:27.452' or '87.452' or milliseconds into seconds."""
    if pd.isna(time_val) or time_val is None or time_val == "" or time_val == r"\N":
        return 0.0
    s = str(time_val).strip()
    if not s or s == "0":
        return 0.0
    try:
        if ":" in s:
            parts = s.split(":")
            mins = float(parts[0])
            secs = float(parts[1])
            return mins * 60.0 + secs
        val = float(s)
        if val > 1000: # milliseconds
            return val / 1000.0
        return val
    except Exception:
        return 0.0

def enrich_f1_dataset():
    print("================================================================================")
    print("   STARTING F1 WINNER PREDICTION FEATURE ENRICHMENT (CAR, LAP, PIT)")
    print("================================================================================")

    csv_path = "F1_Warehouse_Master_65_Columns_2004_2024.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Master CSV not found at {csv_path}")

    print(f"[*] Reading master dataset: {csv_path} ...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"[+] Loaded {len(df):,} race entries with {len(df.columns)} base columns.")

    # -------------------------------------------------------------------------
    # 1. CAR FEATURES ENRICHMENT
    # -------------------------------------------------------------------------
    print("\n[*] Computing 1. CAR FEATURES...")
    
    def get_era_tuple(year):
        for (y_start, y_end), specs in ERA_SPECS.items():
            if y_start <= year <= y_end:
                return specs
        return ("1.6L V6 Turbocharged Hybrid", 798, 1000, 15000, "Modern Regulation")

    era_data = [get_era_tuple(int(y)) for y in df["season"]]
    df["car_engine_architecture"] = [e[0] for e in era_data]
    df["car_min_weight_kg"] = [e[1] for e in era_data]
    df["car_base_power_bhp"] = [e[2] for e in era_data]
    df["car_max_rpm"] = [e[3] for e in era_data]
    df["car_aero_regulation_era"] = [e[4] for e in era_data]

    # Power Unit Supplier
    df["car_power_unit_supplier"] = [
        get_engine_supplier_for_constructor(c_ref, int(s))
        for c_ref, s in zip(df["constructor_ref"], df["season"])
    ]

    # Supplier Tier BHP Modifier
    # Tier 1 works factory teams get +15-25 BHP over customer baselines
    def calc_estimated_bhp(supplier, constructor_ref, base_bhp):
        sup = str(supplier).lower()
        c_ref = str(constructor_ref).lower()
        bonus = 0
        if "ferrari" in sup and "ferrari" in c_ref:
            bonus = 20
        elif "mercedes" in sup and "mercedes" in c_ref:
            bonus = 25
        elif "red bull" in sup or "honda" in sup and "red_bull" in c_ref:
            bonus = 25
        elif "renault" in sup and ("renault" in c_ref or "alpine" in c_ref):
            bonus = 10
        return base_bhp + bonus

    df["car_estimated_power_bhp"] = [
        calc_estimated_bhp(sup, c_ref, base)
        for sup, c_ref, base in zip(df["car_power_unit_supplier"], df["constructor_ref"], df["car_base_power_bhp"])
    ]

    # Power to Weight Ratio (BHP / kg)
    df["car_power_to_weight_ratio"] = (df["car_estimated_power_bhp"] / df["car_min_weight_kg"]).round(4)

    # Constructor Chassis Generation Name
    def get_chassis_code(constructor_ref, season):
        c = str(constructor_ref).lower()
        if "red_bull" in c:
            num = season - 2004
            return f"RB{num}"
        elif "ferrari" in c:
            if season == 2024: return "SF-24"
            if season == 2023: return "SF-23"
            if season == 2022: return "F1-75"
            return f"Ferrari-{season}"
        elif "mercedes" in c:
            num = season - 2009
            return f"W{num:02d}"
        elif "mclaren" in c:
            if season >= 2017:
                return f"MCL{season - 1986}"
            return f"MP4-{season - 1984}"
        elif "williams" in c:
            return f"FW{season - 1977}"
        return f"{str(constructor_ref).title()}-{season}"

    df["car_chassis_model"] = [get_chassis_code(c, int(s)) for c, s in zip(df["constructor_ref"], df["season"])]

    # Historical Constructor Mechanical Reliability Score (% completed without mechanical DNF in season)
    df["is_mechanical_dnf"] = df["race_status"].str.lower().str.contains(
        "engine|gearbox|transmission|hydraulics|electrical|suspension|brakes|clutch|exhaust|radiator|oil|fuel", na=False
    ).astype(int)

    team_rel = df.groupby(["season", "constructor_id"])["is_mechanical_dnf"].transform(lambda x: 1.0 - x.mean()).round(4)
    df["car_mechanical_reliability_score"] = team_rel

    # Constructor Rolling Pace Index (Average qualifying rank of constructor in season)
    df["constructor_season_avg_grid"] = df.groupby(["season", "constructor_id"])["grid_position"].transform("mean").round(2)
    df["constructor_pace_index"] = (21.0 - df["constructor_season_avg_grid"]).clip(lower=1.0).round(2)

    print(f"[+] Added 10 Car Features: car_engine_architecture, car_min_weight_kg, car_estimated_power_bhp, car_power_to_weight_ratio, car_aero_regulation_era, car_power_unit_supplier, car_chassis_model, car_mechanical_reliability_score, constructor_pace_index.")

    # -------------------------------------------------------------------------
    # 2. LAP RECORD & TRACK SPEED ENRICHMENT
    # -------------------------------------------------------------------------
    print("\n[*] Computing 2. LAP RECORD METRICS (Cross-referencing FACT_LAP_TIMES telemetry)...")

    # Connect to SQLite to retrieve lap-level telemetry aggregates
    db_conn = sqlite3.connect("f1_warehouse.db")
    cur_lap_query = """
        SELECT 
            race_id, driver_id,
            COUNT(CASE WHEN is_pit_lap = 1 THEN 1 END) as lap_pit_stops,
            MIN(lap_time_ms) as min_lap_ms,
            AVG(lap_time_ms) as avg_lap_ms
        FROM FACT_LAP_TIMES
        GROUP BY race_id, driver_id
    """
    df_laps = pd.read_sql_query(cur_lap_query, db_conn)
    db_conn.close()

    # Merge lap aggregates
    df = df.merge(df_laps, on=["race_id", "driver_id"], how="left")

    circuit_records = []
    record_strs = []
    record_holders = []
    record_years = []
    pit_losses = []

    for cid in df["circuit_id"]:
        rec = CIRCUIT_LAP_RECORDS.get(int(cid), DEFAULT_CIRCUIT_RECORD)
        circuit_records.append(rec[0])
        record_strs.append(rec[1])
        record_holders.append(rec[2])
        record_years.append(rec[3])
        pit_losses.append(rec[4])

    df["circuit_lap_record_sec"] = circuit_records
    df["circuit_lap_record_str"] = record_strs
    df["circuit_lap_record_holder"] = record_holders
    df["circuit_lap_record_year"] = record_years
    df["circuit_pit_lane_loss_sec"] = pit_losses

    # Convert driver fastest lap string to seconds and fallback to min_lap_ms
    driver_fl_sec = []
    for fl_time, fl_ms, lap_min_ms in zip(df["fastest_lap_time"], df["fastest_recorded_lap_ms"], df["min_lap_ms"]):
        sec = parse_time_str_to_sec(fl_time)
        if sec <= 0 and pd.notna(fl_ms) and fl_ms > 0:
            sec = fl_ms / 1000.0
        if sec <= 0 and pd.notna(lap_min_ms) and lap_min_ms > 0:
            sec = lap_min_ms / 1000.0
        driver_fl_sec.append(round(sec, 3))
    df["driver_fastest_lap_sec"] = driver_fl_sec

    # Parse qualifying best time to seconds, fallback to pole-delta estimation
    quali_sec_list = []
    for q_time, fl_sec, grid_pos in zip(df["qualifying_best_time_sec"], df["driver_fastest_lap_sec"], df["grid_position"]):
        q_val = parse_time_str_to_sec(q_time)
        if q_val <= 0 and fl_sec > 0:
            # Qualifying is typically ~1.2% faster than race fastest lap due to lower fuel
            grid_penalty = max(0, (grid_pos - 1) * 0.08)
            q_val = round(fl_sec * 0.988 + grid_penalty, 3)
        quali_sec_list.append(q_val)
    df["driver_qualifying_sec"] = quali_sec_list

    # Calculate Lap Record Gap (seconds delta to all-time circuit record)
    df["driver_lap_record_delta_sec"] = np.where(
        df["driver_fastest_lap_sec"] > 0,
        (df["driver_fastest_lap_sec"] - df["circuit_lap_record_sec"]).round(3),
        15.0
    )

    # Lap Record Pace Ratio (1.0 = equal to track record, 1.05 = 5% slower)
    df["driver_lap_record_ratio"] = np.where(
        (df["driver_fastest_lap_sec"] > 0) & (df["circuit_lap_record_sec"] > 0),
        (df["driver_fastest_lap_sec"] / df["circuit_lap_record_sec"]).round(4),
        1.15
    )

    # Driver Qualifying Delta to Circuit Lap Record
    df["driver_quali_to_record_delta_sec"] = np.where(
        df["driver_qualifying_sec"] > 0,
        (df["driver_qualifying_sec"] - df["circuit_lap_record_sec"]).round(3),
        12.0
    )

    print(f"[+] Added 8 Lap Record Features: circuit_lap_record_sec, circuit_lap_record_str, circuit_lap_record_holder, circuit_lap_record_year, driver_fastest_lap_sec, driver_lap_record_delta_sec, driver_lap_record_ratio, driver_quali_to_record_delta_sec.")

    # -------------------------------------------------------------------------
    # 3. PIT STOP TIME & STRATEGY ENRICHMENT
    # -------------------------------------------------------------------------
    print("\n[*] Computing 3. PIT STOP TIME & EFFICIENCY METRICS...")

    # Backfill pit stop counts from FACT_LAP_TIMES if pit_stop_count is 0 or NaN
    df["pit_stop_count"] = np.where(
        df["pit_stop_count"] > 0,
        df["pit_stop_count"],
        df["lap_pit_stops"].fillna(0).astype(int)
    )

    # In eras without recorded pit durations (2004-2010), estimate pit duration based on pit stops * stationary time + transit loss
    df["total_pit_duration_sec"] = np.where(
        df["total_pit_duration_sec"] > 0,
        df["total_pit_duration_sec"],
        (df["pit_stop_count"] * (df["circuit_pit_lane_loss_sec"] + 3.2)).round(2)
    )

    df["avg_pit_duration_sec"] = np.where(
        df["pit_stop_count"] > 0,
        (df["total_pit_duration_sec"] / df["pit_stop_count"]).round(2),
        0.0
    )

    df["fastest_pit_duration_sec"] = np.where(
        df["fastest_pit_duration_sec"] > 0,
        df["fastest_pit_duration_sec"],
        np.where(df["pit_stop_count"] > 0, (df["circuit_pit_lane_loss_sec"] + 2.4).round(2), 0.0)
    )

    # Team Pit Crew Benchmark Score
    df["pit_crew_efficiency_score"] = [
        PIT_CREW_BENCHMARKS.get(str(c_ref).lower(), 80.0)
        for c_ref in df["constructor_ref"]
    ]

    # Stationary Pit Stop Estimate (Wheel gun time ~2.2-3.5s)
    def estimate_stationary_time(avg_duration, pit_loss, pit_count):
        if pit_count > 0:
            if avg_duration > 15.0: # includes pit lane transit
                stat = avg_duration - pit_loss
                return max(1.8, min(8.0, round(stat, 3)))
            elif avg_duration > 0:
                return round(avg_duration, 3)
            return 2.8
        return 0.0

    df["estimated_stationary_pit_sec"] = [
        estimate_stationary_time(d, loss, count)
        for d, loss, count in zip(df["avg_pit_duration_sec"], df["circuit_pit_lane_loss_sec"], df["pit_stop_count"])
    ]

    # Total Race Pit Strategy Loss = (pit_stop_count * circuit_pit_lane_loss_sec) + (pit_stop_count * estimated_stationary_pit_sec)
    df["total_race_pit_loss_sec"] = (
        (df["pit_stop_count"] * df["circuit_pit_lane_loss_sec"]) + 
        (df["pit_stop_count"] * df["estimated_stationary_pit_sec"])
    ).round(2)

    # Pit Strategy Delta to Race Field Mean
    race_mean_pit_loss = df.groupby("race_id")["total_race_pit_loss_sec"].transform("mean").round(2)
    df["pit_loss_delta_to_race_mean_sec"] = (df["total_race_pit_loss_sec"] - race_mean_pit_loss).round(2)

    # Optimal Stop Count Flag (1-stop vs 2-stop)
    race_winner_stops = df[df["is_win"] == 1].groupby("race_id")["pit_stop_count"].first()
    df["winning_strategy_stop_count"] = df["race_id"].map(race_winner_stops).fillna(df["pit_stop_count"]).astype(int)
    df["pit_stop_delta_to_winning_strategy"] = (df["pit_stop_count"] - df["winning_strategy_stop_count"]).astype(int)

    print(f"[+] Added 6 Pit Stop Features: circuit_pit_lane_loss_sec, pit_crew_efficiency_score, estimated_stationary_pit_sec, total_race_pit_loss_sec, pit_loss_delta_to_race_mean_sec, pit_stop_delta_to_winning_strategy.")

    # -------------------------------------------------------------------------
    # 4. SAVE ENRICHED MASTER CSV
    # -------------------------------------------------------------------------
    output_csv = "F1_ML_Winner_Prediction_Dataset.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n[OK] Saved enriched machine learning dataset: '{output_csv}' ({len(df):,} rows x {len(df.columns)} cols)")

    # -------------------------------------------------------------------------
    # 5. SYNC TO SQLITE DATABASE (f1_warehouse.db)
    # -------------------------------------------------------------------------
    db_path = "f1_warehouse.db"
    print(f"[*] Syncing enriched features to SQLite database: {db_path} ...")
    conn = sqlite3.connect(db_path)
    
    # Store complete ML dataset table
    df.to_sql("ML_WINNER_PREDICTION_FEATURES", conn, if_exists="replace", index=False)

    # Create optimized indexing for low-latency queries
    cur = conn.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ml_race_driver ON ML_WINNER_PREDICTION_FEATURES (race_id, driver_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ml_season_constructor ON ML_WINNER_PREDICTION_FEATURES (season, constructor_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ml_is_win ON ML_WINNER_PREDICTION_FEATURES (is_win)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ml_grid ON ML_WINNER_PREDICTION_FEATURES (grid_position)")

    # Also update/add columns in DIM_CIRCUIT_LAP_RECORDS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS DIM_CIRCUIT_LAP_RECORDS (
            circuit_id INTEGER PRIMARY KEY,
            circuit_lap_record_sec REAL,
            circuit_lap_record_str TEXT,
            circuit_lap_record_holder TEXT,
            circuit_lap_record_year INTEGER,
            circuit_pit_lane_loss_sec REAL
        )
    """)
    cur.executemany("""
        INSERT OR REPLACE INTO DIM_CIRCUIT_LAP_RECORDS 
        (circuit_id, circuit_lap_record_sec, circuit_lap_record_str, circuit_lap_record_holder, circuit_lap_record_year, circuit_pit_lane_loss_sec)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [(cid, rec[0], rec[1], rec[2], rec[3], rec[4]) for cid, rec in CIRCUIT_LAP_RECORDS.items()])

    # Create analytical view for Winner Prediction ML
    cur.execute("""
        CREATE VIEW IF NOT EXISTS V_RACE_WINNER_ML_DATASET AS
        SELECT 
            race_id, season, round, race_name, circuit_name, circuit_country,
            driver_id, driver_code, driver_name, driver_nationality, driver_age_years,
            constructor_id, constructor_name,
            car_chassis_model, car_power_unit_supplier, car_engine_architecture,
            car_estimated_power_bhp, car_min_weight_kg, car_power_to_weight_ratio,
            car_mechanical_reliability_score, constructor_pace_index,
            circuit_lap_record_sec, circuit_lap_record_str, circuit_lap_record_holder,
            driver_fastest_lap_sec, driver_lap_record_delta_sec, driver_lap_record_ratio,
            grid_position, qualifying_position, driver_qualifying_sec, driver_quali_to_record_delta_sec,
            pit_stop_count, total_pit_duration_sec, avg_pit_duration_sec, fastest_pit_duration_sec,
            circuit_pit_lane_loss_sec, pit_crew_efficiency_score, estimated_stationary_pit_sec, total_race_pit_loss_sec,
            driver_standing_points, driver_championship_position, driver_championship_wins, driver_standing_gap_to_leader,
            constructor_standing_points, constructor_championship_position, constructor_standing_gap_to_leader,
            finish_position, is_win, is_podium, is_top_10, is_dnf
        FROM ML_WINNER_PREDICTION_FEATURES
    """)

    conn.commit()
    conn.close()
    print("[OK] SQLite database updated with 'ML_WINNER_PREDICTION_FEATURES' and 'DIM_CIRCUIT_LAP_RECORDS'!")

    return df

if __name__ == "__main__":
    enrich_f1_dataset()
