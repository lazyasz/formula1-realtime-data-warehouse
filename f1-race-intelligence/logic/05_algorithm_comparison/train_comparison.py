"""
Classification Algorithm Comparison & Validation
=================================================
Benchmarks 7 classification algorithms on the Formula 1 1994–2024 dataset.

Chronological Split:
- Training: 1994–2021 (509 Grands Prix, 10,958 entries)
- Test:     2022–2024 (68 Grands Prix, 1,400 entries) - Modern Ground Effect Era

Algorithms Evaluated:
1. Dummy Classifier (Prior Uniform Baseline)
2. Baseline Logistic Regression (Grid Position Only)
3. Decision Tree Classifier (Entropy, Max Depth 5, Balanced)
4. Random Forest Classifier (150 Trees, Balanced)
5. Gradient Boosting (GBDT, 100 Trees, LR 0.05)
6. LightGBM Classifier (100 Trees, Balanced)
7. XGBoost Classifier (Champion, Scale Pos Weight 15)

Outputs:
- 05_algorithm_comparison/comparison_results.csv
"""

import os
import time
import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score,
    balanced_accuracy_score, precision_score, recall_score,
    f1_score, brier_score_loss
)
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import lightgbm as lgb
import xgboost as xgb

FEATURES = [
    "grid_position", "driver_rolling_finish_5", "driver_rolling_points_5",
    "constructor_rolling_finish_10", "constructor_rolling_points_10",
    "circuit_avg_finish", "circuit_win_rate", "circuit_podium_rate",
    "circuit_experience", "season_points_before", "career_starts",
    "career_win_rate", "career_dnf_rate", "ahead_of_teammate_grid",
    "driver_age", "grid_vs_form_gap"
]

def load_data():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(base_dir, "..", "..", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    return pd.read_csv(data_path, low_memory=False)

def run_comparison():
    print("=" * 100)
    print("   PARAMETER 05: CLASSIFICATION ALGORITHM COMPARISON & CHRONOLOGICAL VALIDATION")
    print("=" * 100)

    df = load_data()
    print(f"[+] Loaded {len(df):,} records from 1994 to 2024.")

    train_mask = df["season"] <= 2021
    test_mask = df["season"] >= 2022

    X_train = df.loc[train_mask, FEATURES].fillna(0)
    y_train = df.loc[train_mask, "target_is_win"].astype(int)

    X_test = df.loc[test_mask, FEATURES].fillna(0)
    y_test = df.loc[test_mask, "target_is_win"].astype(int)
    test_df = df.loc[test_mask].copy()
    n_test_races = test_df["race_id"].nunique()

    print(f"[+] Chronological Partition: Train {len(X_train):,} rows ({df.loc[train_mask, 'race_id'].nunique()} GPs, 1994-2021) | Test {len(X_test):,} rows ({n_test_races} GPs, 2022-2024).")

    models = {
        "1. Dummy Classifier": DummyClassifier(strategy="uniform", random_state=42),
        "2. Baseline (Logistic Reg - Grid Only)": LogisticRegression(random_state=42, max_iter=300),
        "3. Decision Tree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=42),
        "4. Random Forest Classifier": RandomForestClassifier(n_estimators=150, max_depth=6, class_weight="balanced", random_state=42),
        "5. Gradient Boosting (GBDT)": GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42),
        "6. LightGBM Classifier": lgb.LGBMClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, is_unbalance=True, random_state=42, verbose=-1),
        "7. XGBoost Classifier (Champion)": xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15, random_state=42, eval_metric="logloss")
    }

    results = []
    print("\n" + "-" * 115)
    print(f"{'Algorithm Name':<38} | {'ROC-AUC':<7} | {'PR-AUC':<7} | {'Acc %':<6} | {'BalAcc':<6} | {'Top-1 Hit %':<12} | {'Top-3 %':<8} | {'Brier':<6}")
    print("-" * 115)

    for name, clf in models.items():
        t0 = time.perf_counter()
        if "Grid Only" in name:
            clf.fit(X_train[["grid_position"]], y_train)
            t_fit = time.perf_counter() - t0
            t_inf_start = time.perf_counter()
            probs = clf.predict_proba(X_test[["grid_position"]])[:, 1]
            preds = clf.predict(X_test[["grid_position"]])
            inf_ms = (time.perf_counter() - t_inf_start) * 1000
        else:
            clf.fit(X_train, y_train)
            t_fit = time.perf_counter() - t0
            t_inf_start = time.perf_counter()
            probs = clf.predict_proba(X_test)[:, 1]
            preds = clf.predict(X_test)
            inf_ms = (time.perf_counter() - t_inf_start) * 1000

        # Calculate metrics
        roc_auc = roc_auc_score(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)
        acc = accuracy_score(y_test, preds) * 100
        bal_acc = balanced_accuracy_score(y_test, preds) * 100
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        brier = brier_score_loss(y_test, probs)

        # Race-level Top-1 & Top-3 Hits
        test_df["_pred_prob"] = probs
        top1_hits = 0
        top3_hits = 0
        for _, grp in test_df.groupby("race_id"):
            ranked = grp.sort_values(by="_pred_prob", ascending=False)
            if ranked.iloc[0]["target_is_win"] == 1:
                top1_hits += 1
            if ranked.iloc[:3]["target_is_win"].sum() >= 1:
                top3_hits += 1

        top1_pct = (top1_hits / n_test_races) * 100
        top3_pct = (top3_hits / n_test_races) * 100

        print(f"{name:<38} | {roc_auc:.4f}  | {pr_auc:.4f}  | {acc:5.2f}% | {bal_acc:5.2f}% | {top1_pct:5.1f}% ({top1_hits:02d}/{n_test_races}) | {top3_pct:5.1f}%   | {brier:.4f}")

        results.append({
            "algorithm": name,
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "accuracy_pct": round(acc, 2),
            "balanced_acc_pct": round(bal_acc, 2),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "top1_winner_hit_pct": round(top1_pct, 2),
            "top1_hits": int(top1_hits),
            "top3_podium_hit_pct": round(top3_pct, 2),
            "brier_score": round(brier, 4),
            "inf_latency_ms": round(inf_ms, 2)
        })

    res_df = pd.DataFrame(results)
    out_csv = os.path.join(os.path.dirname(__file__), "comparison_results.csv")
    res_df.to_csv(out_csv, index=False)
    print(f"\n[+] Results successfully exported to: {out_csv}")

    return res_df

if __name__ == "__main__":
    run_comparison()
