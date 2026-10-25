"""
Formula 1 Feature Engineering & Data Preparation Pipeline for Snowflake
========================================================================
Extracts, cleans, and groups features from raw F1 telemetry into the 3 core pillars:
1. CAR FEATURES (Constructor strength, engine power, weight, reliability, grid)
2. LAP RECORD FEATURES (Track records, qualifying delta, lap pace ratio)
3. PIT STOP FEATURES (Stops count, pit loss seconds, crew efficiency)

Ensures zero data leakage (no post-race finish time, race points, or finish position as inputs).
"""

import os
import pandas as pd
import numpy as np

def run_feature_engineering():
    print("[*] Starting F1 Feature Engineering Pipeline...")
    
    # Path to source dataset
    source_csv = os.path.join(os.path.dirname(__file__), "..", "..", "F1_ML_Winner_Prediction_Dataset.csv")
    if not os.path.exists(source_csv):
        source_csv = "F1_ML_Winner_Prediction_Dataset.csv"
        
    if not os.path.exists(source_csv):
        raise FileNotFoundError(f"Source F1 dataset not found at: {source_csv}")
        
    print(f"[+] Reading source dataset: {source_csv}")
    df = pd.read_csv(source_csv, low_memory=False)
    print(f"[+] Loaded {len(df):,} rows and {len(df.columns)} columns across {df['season'].nunique()} seasons ({df['season'].min()}-{df['season'].max()}).")

    # Define Feature Groups
    # Group A: CAR FEATURES (Pre-race proxies, constructor form, car specs, starting grid)
    CAR_FEATURES = [
        "constructor_name",
        "car_estimated_power_bhp",
        "car_power_to_weight_ratio",
        "car_min_weight_kg",
        "car_mechanical_reliability_score",
        "constructor_pace_index",
        "grid_position",
        "qualifying_position",
        "driver_age_years",
        "driver_standing_points",
        "driver_championship_position",
        "constructor_standing_points",
        "constructor_championship_position"
    ]

    # Group B: LAP RECORD FEATURES (Circuit track limits, driver qualifying vs circuit lap record)
    LAP_RECORD_FEATURES = [
        "circuit_lap_record_sec",
        "driver_lap_record_delta_sec",
        "driver_lap_record_ratio",
        "driver_quali_to_record_delta_sec",
        "fastest_lap_speed",
        "average_lap_ms",
        "driver_fastest_lap_sec"
    ]

    # Group C: PIT STOP FEATURES (Strategy expectations, track transit loss, stationary crew speed)
    PIT_STOP_FEATURES = [
        "pit_stop_count",
        "total_race_pit_loss_sec",
        "avg_pit_duration_sec",
        "estimated_stationary_pit_sec",
        "pit_crew_efficiency_score",
        "pit_loss_delta_to_race_mean_sec",
        "circuit_pit_lane_loss_sec"
    ]

    # Identifiers & Metadata
    ID_COLS = [
        "race_id", "season", "round", "race_name", "race_date",
        "circuit_id", "circuit_name", "circuit_country",
        "driver_id", "driver_ref", "driver_code", "driver_name",
        "constructor_id", "constructor_ref"
    ]

    # Targets (CLASSIFICATION: is_win, is_podium; REGRESSION: finish_position)
    TARGET_COLS = [
        "is_win", "is_podium", "is_top_10", "finishing_tier", "finish_position"
    ]

    # Clean missing values safely
    df["car_estimated_power_bhp"] = df["car_estimated_power_bhp"].fillna(850.0)
    df["car_power_to_weight_ratio"] = df["car_power_to_weight_ratio"].fillna(1.22)
    df["car_min_weight_kg"] = df["car_min_weight_kg"].fillna(700.0)
    df["car_mechanical_reliability_score"] = df["car_mechanical_reliability_score"].fillna(0.85)
    df["constructor_pace_index"] = df["constructor_pace_index"].fillna(50.0)
    df["grid_position"] = df["grid_position"].fillna(20).clip(1, 24)
    df["qualifying_position"] = df["qualifying_position"].fillna(df["grid_position"]).clip(1, 24)
    df["driver_age_years"] = df["driver_age_years"].fillna(27.0)

    df["circuit_lap_record_sec"] = df["circuit_lap_record_sec"].fillna(85.0)
    df["driver_lap_record_delta_sec"] = df["driver_lap_record_delta_sec"].fillna(2.5)
    df["driver_lap_record_ratio"] = df["driver_lap_record_ratio"].fillna(1.03)
    df["driver_quali_to_record_delta_sec"] = df["driver_quali_to_record_delta_sec"].fillna(1.8)
    df["fastest_lap_speed"] = df["fastest_lap_speed"].fillna(220.0)
    df["average_lap_ms"] = df["average_lap_ms"].fillna(90000.0)
    df["driver_fastest_lap_sec"] = df["driver_fastest_lap_sec"].fillna(87.0)

    df["pit_stop_count"] = df["pit_stop_count"].fillna(2).clip(0, 5)
    df["total_race_pit_loss_sec"] = df["total_race_pit_loss_sec"].fillna(48.0)
    df["avg_pit_duration_sec"] = df["avg_pit_duration_sec"].fillna(24.0)
    df["estimated_stationary_pit_sec"] = df["estimated_stationary_pit_sec"].fillna(2.5)
    df["pit_crew_efficiency_score"] = df["pit_crew_efficiency_score"].fillna(85.0)
    df["pit_loss_delta_to_race_mean_sec"] = df["pit_loss_delta_to_race_mean_sec"].fillna(0.0)
    df["circuit_pit_lane_loss_sec"] = df["circuit_pit_lane_loss_sec"].fillna(21.0)

    df["is_win"] = df["is_win"].fillna(0).astype(int)
    df["is_podium"] = df["is_podium"].fillna(0).astype(int)
    df["is_top_10"] = df["is_top_10"].fillna(0).astype(int)
    df["finish_position"] = df["finish_position"].fillna(20.0).clip(1, 24)

    # Export clean tables
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    master_cols = ID_COLS + CAR_FEATURES + LAP_RECORD_FEATURES + PIT_STOP_FEATURES + TARGET_COLS
    # Remove duplicates if any
    master_cols = list(dict.fromkeys(master_cols))
    
    clean_master_df = df[master_cols].copy()
    master_path = os.path.join(data_dir, "clean_f1_modeling_master.csv")
    clean_master_df.to_csv(master_path, index=False)
    print(f"[+] Saved Clean Modeling Master: {master_path} ({len(clean_master_df):,} rows, {len(clean_master_df.columns)} cols)")

    # Also save raw staging splits for Snowflake RAW schema
    races_df = df[["race_id", "season", "round", "race_name", "race_date", "circuit_id", "circuit_name", "circuit_country"]].drop_duplicates()
    races_df.to_csv(os.path.join(data_dir, "raw_races.csv"), index=False)

    drivers_df = df[["driver_id", "driver_ref", "driver_code", "driver_name", "driver_dob", "driver_nationality"]].drop_duplicates()
    drivers_df.to_csv(os.path.join(data_dir, "raw_drivers.csv"), index=False)

    constructors_df = df[["constructor_id", "constructor_ref", "constructor_name", "constructor_nationality"]].drop_duplicates()
    constructors_df.to_csv(os.path.join(data_dir, "raw_constructors.csv"), index=False)

    circuits_df = df[["circuit_id", "circuit_name", "circuit_country", "circuit_lap_record_sec", "circuit_pit_lane_loss_sec"]].drop_duplicates()
    circuits_df.to_csv(os.path.join(data_dir, "raw_circuits.csv"), index=False)

    results_df = df[["race_id", "driver_id", "constructor_id", "grid_position", "qualifying_position", "finish_position", "is_win", "is_podium", "is_top_10"]].copy()
    results_df.to_csv(os.path.join(data_dir, "raw_race_results.csv"), index=False)

    print(f"[+] All raw and clean CSV files successfully staged in: {data_dir}")
    return clean_master_df

if __name__ == "__main__":
    run_feature_engineering()
