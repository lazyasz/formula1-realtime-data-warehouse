import os
import time
import random
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "f1_warehouse")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
SIM_INTERVAL_SEC = float(os.getenv("SIM_INTERVAL_SEC", "1.5"))

# Top F1 Contenders for Live Simulation (2024 British GP Silverstone race_id = 9)
LIVE_DRIVERS = [
    {"driver_id": 830, "driver_code": "VER", "team_id": 9, "base_lap": 87200, "pos": 1},  # Verstappen (Red Bull)
    {"driver_id": 846, "driver_code": "NOR", "team_id": 1, "base_lap": 87350, "pos": 2},  # Norris (McLaren)
    {"driver_id": 844, "driver_code": "LEC", "team_id": 6, "base_lap": 87500, "pos": 3},  # Leclerc (Ferrari)
    {"driver_id": 1,   "driver_code": "HAM", "team_id": 131, "base_lap": 87400, "pos": 4}, # Hamilton (Mercedes)
    {"driver_id": 847, "driver_code": "RUS", "team_id": 131, "base_lap": 87550, "pos": 5}, # Russell (Mercedes)
    {"driver_id": 857, "driver_code": "PIA", "team_id": 1, "base_lap": 87600, "pos": 6},  # Piastri (McLaren)
    {"driver_id": 832, "driver_code": "SAI", "team_id": 6, "base_lap": 87700, "pos": 7},  # Sainz (Ferrari)
    {"driver_id": 4,   "driver_code": "ALO", "team_id": 117, "base_lap": 87900, "pos": 8}, # Alonso (Aston Martin)
]

def run_live_simulation_feed():
    print("=" * 80)
    print("  FORMULA 1 LIVE RACE TELEMETRY SIMULATION FEEDER")
    print(f"  Streaming interval: {SIM_INTERVAL_SEC}s per live batch to fact_lap_times")
    print("=" * 80)

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Target live race
    race_id = 9
    date_id = 20240707
    cur_lap = 1
    max_laps = 52

    while True:
        now_ts = datetime.now()
        batch_records = []

        # Generate telemetry for all live contenders for the current lap
        for d in LIVE_DRIVERS:
            driver_id = d["driver_id"]
            team_id = d["team_id"]
            pos = d["pos"]

            # Realistic lap jitter
            jitter = random.randint(-400, 450)
            total_lap_ms = d["base_lap"] + jitter
            s1 = int(total_lap_ms * 0.32) + random.randint(-100, 100)
            s2 = int(total_lap_ms * 0.38) + random.randint(-150, 150)
            s3 = total_lap_ms - s1 - s2
            speed = round(320.0 + random.uniform(0.5, 24.5), 2)
            is_pit = 1 if cur_lap in [18, 38] and random.random() > 0.5 else 0
            tyre_age = (cur_lap % 20) + 1
            compound_id = 1 if cur_lap < 18 else (3 if cur_lap < 38 else 2)

            batch_records.append((
                race_id,
                driver_id,
                team_id,
                6, # session_id = RACE
                cur_lap,
                date_id,
                compound_id,
                total_lap_ms,
                pos,
                s1,
                s2,
                s3,
                speed,
                tyre_age,
                is_pit,
                now_ts
            ))

        # Insert new live telemetry lap
        execute_values(cur, """
            INSERT INTO fact_lap_times (
                race_id, driver_id, team_id, session_id, lap_number, date_id,
                tyre_compound_id, lap_time_ms, lap_position, sector1_ms, sector2_ms,
                sector3_ms, speed_trap_kmh, tyre_age_laps, is_pit_lap, recorded_at
            ) VALUES %s
            ON CONFLICT (race_id, driver_id, session_id, lap_number) 
            DO UPDATE SET recorded_at = EXCLUDED.recorded_at, lap_time_ms = EXCLUDED.lap_time_ms;
        """, batch_records)

        print(f"[{now_ts.strftime('%H:%M:%S')}] 🟢 Ingested LAP {cur_lap}/{max_laps} telemetry for {len(batch_records)} active drivers (Top speed: {max(b[12] for b in batch_records)} km/h)")

        cur_lap += 1
        if cur_lap > max_laps:
            cur_lap = 1 # Loop simulation

        time.sleep(SIM_INTERVAL_SEC)

if __name__ == "__main__":
    run_live_simulation_feed()
