import os
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
import numpy as np

# Ensure root is in path
sys.path.insert(0, r"c:\Users\dhruv\.gemini\antigravity-ide\scratch\f1_dw\f1-race-intelligence")
sys.path.insert(0, r"c:\Users\dhruv\.gemini\antigravity-ide\scratch\f1_dw\f1-race-intelligence\logic")

from db_utils import normalize_columns, get_local_data

print("1. Testing normalize_columns with snowflake style columns...")
df_snow = pd.DataFrame({
    "SEASON": [2024, 2023],
    "ROUND": [24, 22],
    "DRIVER_NAME": ["Lewis Hamilton", "Lewis Hamilton"],
    "CIRCUIT_NAME": ["Yas Marina Circuit", "Yas Marina Circuit"],
    "GRID_POSITION": [4, 5],
    "IS_WIN": [0, 1],
    "IS_PODIUM": [1, 1],
    "FINISH_POSITION": [3, 1]
})

df_norm = normalize_columns(df_snow)
print("Normalized columns:", df_norm.columns.tolist())
assert "target_is_win" in df_norm.columns, "target_is_win missing!"
assert "target_is_podium" in df_norm.columns, "target_is_podium missing!"
assert "target_finish_position" in df_norm.columns, "target_finish_position missing!"
assert "is_win" in df_norm.columns, "is_win missing!"

# Test historical stat calculations
hist_starts = len(df_norm)
hist_wins = int(df_norm["target_is_win"].sum())
hist_podiums = int(df_norm["target_is_podium"].sum())
hist_win_rate = hist_wins / hist_starts
hist_avg_finish = float(df_norm["target_finish_position"].mean())

print(f"Stats calculated successfully: {hist_wins} wins, {hist_podiums} podiums, avg finish {hist_avg_finish}")
assert hist_wins == 1
assert hist_podiums == 2
assert hist_avg_finish == 2.0

print("\n2. Testing get_local_data('clean_f1_modeling_master.csv')...")
master = get_local_data("clean_f1_modeling_master.csv")
print(f"Master shape: {master.shape}")
assert "target_is_win" in master.columns
assert "is_win" in master.columns
assert "target_finish_position" in master.columns
assert "finish_position" in master.columns
print("Master columns verified successfully!")

print("\n[✓] ALL LOCAL TESTS PASSED FLAWLESSLY!")
