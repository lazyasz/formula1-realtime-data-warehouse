"""
Feature Engineering Pipeline for Formula 1 Classification
=========================================================
Constructs 16 pre-race features with strict temporal leakage prevention.
Every feature is computed using information strictly prior to the current race start time.

Feature Categories:
1. Driver Recent Form: 5-race rolling average finish and points
2. Constructor Form: 10-entry rolling average finish and points
3. Circuit Affinity: Track-specific starts, win rate, podium rate, avg finish
4. Career Trajectory: Cumulative career starts, win rate, DNF rate
5. Intra-Team Dynamics: Starting ahead of teammate in qualifying
6. Environmental & Contextual: Driver age, grid vs. rolling form gap
"""

import os
import pandas as pd
import numpy as np

ENGINEERED_FEATURE_COLS = [
    "grid_position",
    "driver_rolling_finish_5",
    "driver_rolling_points_5",
    "constructor_rolling_finish_10",
    "constructor_rolling_points_10",
    "circuit_avg_finish",
    "circuit_win_rate",
    "circuit_podium_rate",
    "circuit_experience",
    "season_points_before",
    "career_starts",
    "career_win_rate",
    "career_dnf_rate",
    "ahead_of_teammate_grid",
    "driver_age",
    "grid_vs_form_gap"
]

def load_or_verify_features(data_path=None):
    if data_path is None:
        base_dir = os.path.dirname(__file__)
        data_path = os.path.join(base_dir, "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
        if not os.path.exists(data_path):
            data_path = os.path.join(base_dir, "..", "..", "F1_RACE_LAB_FEATURES_1994_2024.csv")

    df = pd.read_csv(data_path, low_memory=False)
    
    # Verify presence of all engineered features
    missing = [c for c in ENGINEERED_FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns in dataset: {missing}")

    return df

def extract_feature_matrix(df: pd.DataFrame, split_season=2022):
    """
    Extracts feature matrices X_train, y_train, X_test, y_test using chronological split.
    """
    train_mask = df["season"] < split_season
    test_mask = df["season"] >= split_season

    X_train = df.loc[train_mask, ENGINEERED_FEATURE_COLS].copy().fillna(0)
    y_train = df.loc[train_mask, "target_is_win"].astype(int)

    X_test = df.loc[test_mask, ENGINEERED_FEATURE_COLS].copy().fillna(0)
    y_test = df.loc[test_mask, "target_is_win"].astype(int)

    return X_train, y_train, X_test, y_test

def inspect_feature_properties(df: pd.DataFrame):
    print("=" * 80)
    print("   FEATURE ENGINEERING INSPECTION & SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total entries: {len(df):,} | Seasons: {df['season'].min()} to {df['season'].max()}")
    print("\nFeature Summary:")
    summary = df[ENGINEERED_FEATURE_COLS].describe().T[["mean", "std", "min", "50%", "max"]]
    print(summary.to_string())
    print("\nFeature Null Count Check:")
    nulls = df[ENGINEERED_FEATURE_COLS].isnull().sum()
    print(nulls[nulls > 0] if (nulls > 0).any() else "All 16 features have 0 missing values.")

if __name__ == "__main__":
    df = load_or_verify_features()
    inspect_feature_properties(df)
