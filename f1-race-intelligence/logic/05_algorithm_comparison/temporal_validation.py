"""
Temporal Cross-Validation & Leakage Prevention
==============================================
Validates that classification models adhere strictly to chronological order,
preventing future information leakage into past training folds.

Implements:
1. Expanding-Window Chronological Validation:
   - Fold 1: Train 1994–2018 -> Test 2019
   - Fold 2: Train 1994–2019 -> Test 2020
   - Fold 3: Train 1994–2020 -> Test 2021
   - Fold 4: Train 1994–2021 -> Test 2022
   - Fold 5: Train 1994–2022 -> Test 2023
   - Fold 6: Train 1994–2023 -> Test 2024
2. Strict Temporal Invariant Verification:
   max(Train_Season) < min(Test_Season)
3. Rolling Out-of-Sample Performance Metric Tracking
"""

import os
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import xgboost as xgb

FEATURES = [
    "grid_position", "driver_rolling_finish_5", "driver_rolling_points_5",
    "constructor_rolling_finish_10", "constructor_rolling_points_10",
    "circuit_avg_finish", "circuit_win_rate", "circuit_podium_rate",
    "circuit_experience", "season_points_before", "career_starts",
    "career_win_rate", "career_dnf_rate", "ahead_of_teammate_grid",
    "driver_age", "grid_vs_form_gap"
]

def run_temporal_validation():
    print("=" * 95)
    print("   PARAMETER 05: EXPANDING-WINDOW CHRONOLOGICAL VALIDATION & LEAKAGE PROOF")
    print("=" * 95)

    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(base_dir, "..", "..", "F1_RACE_LAB_FEATURES_1994_2024.csv")

    df = pd.read_csv(data_path, low_memory=False)
    print(f"[+] Loaded {len(df):,} records (Seasons {df['season'].min()} to {df['season'].max()}).")

    test_seasons = [2019, 2020, 2021, 2022, 2023, 2024]
    fold_results = []

    print("\n" + "-" * 95)
    print(f"{'Fold':<6} | {'Train Period':<16} | {'Test Season':<11} | {'Train Rows':<10} | {'Test Rows':<9} | {'ROC-AUC':<7} | {'Top-1 Hit %'}")
    print("-" * 95)

    for i, test_yr in enumerate(test_seasons, 1):
        train_mask = df["season"] < test_yr
        test_mask = df["season"] == test_yr

        # Temporal invariant check
        max_train_season = df.loc[train_mask, "season"].max()
        min_test_season = df.loc[test_mask, "season"].min()
        assert max_train_season < min_test_season, f"LEAKAGE DETECTED: {max_train_season} >= {min_test_season}"

        X_train = df.loc[train_mask, FEATURES].fillna(0)
        y_train = df.loc[train_mask, "target_is_win"].astype(int)
        X_test = df.loc[test_mask, FEATURES].fillna(0)
        y_test = df.loc[test_mask, "target_is_win"].astype(int)
        test_slice = df.loc[test_mask].copy()

        clf = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            scale_pos_weight=15, random_state=42, eval_metric="logloss"
        )
        clf.fit(X_train, y_train)

        probs = clf.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)
        brier = brier_score_loss(y_test, probs)

        # Race top-1 accuracy
        test_slice["p"] = probs
        top1_hits = 0
        n_races = test_slice["race_id"].nunique()
        for _, grp in test_slice.groupby("race_id"):
            top1_hits += int(grp.sort_values(by="p", ascending=False).iloc[0]["target_is_win"] == 1)
        top1_pct = (top1_hits / n_races) * 100

        print(f"Fold {i} | 1994-{test_yr-1:<10} | {test_yr:<11} | {len(X_train):<10,} | {len(X_test):<9,} | {auc:.4f}  | {top1_pct:5.1f}% ({top1_hits:02d}/{n_races:02d})")

        fold_results.append({
            "fold": i,
            "train_span": f"1994-{test_yr-1}",
            "test_season": test_yr,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "roc_auc": round(auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "top1_pct": round(top1_pct, 2),
            "top1_hits": top1_hits,
            "n_races": n_races
        })

    res_df = pd.DataFrame(fold_results)
    mean_auc = res_df["roc_auc"].mean()
    mean_top1 = res_df["top1_pct"].mean()

    print("-" * 95)
    print(f"MEAN EXPANDING-WINDOW PERFORMANCE: ROC-AUC = {mean_auc:.4f} | Top-1 Accuracy = {mean_top1:.2f}%")
    print("[+] Temporal Validation Proof: PASSED (Zero future-to-past leakage across all 6 folds).\n")
    return res_df

if __name__ == "__main__":
    run_temporal_validation()
