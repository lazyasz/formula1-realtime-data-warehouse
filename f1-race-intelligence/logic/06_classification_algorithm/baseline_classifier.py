"""
Baseline Classifier Implementation
==================================
Implements the baseline classification model: Logistic Regression trained
exclusively on official Saturday starting grid position (`grid_position`).

Represents the naive domain heuristic: "Pole position wins the Grand Prix."
Used as the benchmark against which multi-feature improvements are measured.
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score,
    precision_score, recall_score, f1_score, brier_score_loss,
    confusion_matrix, classification_report
)

sys.path.append(os.path.dirname(__file__))
from feature_engineering import load_or_verify_features, extract_feature_matrix

def train_and_evaluate_baseline():
    print("=" * 80)
    print("   PARAMETER 06: BASELINE CLASSIFIER (GRID-ONLY LOGISTIC REGRESSION)")
    print("=" * 80)

    df = load_or_verify_features()
    X_train, y_train, X_test, y_test = extract_feature_matrix(df, split_season=2022)

    X_train_base = X_train[["grid_position"]]
    X_test_base = X_test[["grid_position"]]

    print(f"[+] Training baseline on 1994–2021 ({len(X_train_base):,} rows)...")
    clf = LogisticRegression(random_state=42, max_iter=300)
    clf.fit(X_train_base, y_train)

    print(f"[+] Model Intercept: {clf.intercept_[0]:.4f} | Grid Weight: {clf.coef_[0][0]:.4f}")

    # Predictions
    probs = clf.predict_proba(X_test_base)[:, 1]
    preds = clf.predict(X_test_base)

    # Metrics
    auc = roc_auc_score(y_test, probs)
    pr_auc = average_precision_score(y_test, probs)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    brier = brier_score_loss(y_test, probs)

    test_slice = df.loc[df["season"] >= 2022].copy()
    test_slice["pred_prob"] = probs

    # Top-1 Winner Hit Rate across 68 test races
    top1_hits = 0
    n_races = test_slice["race_id"].nunique()
    for _, grp in test_slice.groupby("race_id"):
        top1_hits += int(grp.sort_values(by="pred_prob", ascending=False).iloc[0]["target_is_win"] == 1)

    top1_pct = (top1_hits / n_races) * 100

    print("\n" + "-" * 50)
    print("BASELINE OUT-OF-SAMPLE EVALUATION (2022–2024)")
    print("-" * 50)
    print(f"ROC-AUC:                {auc:.4f}")
    print(f"PR-AUC:                 {pr_auc:.4f}")
    print(f"Accuracy:               {acc*100:.2f}%")
    print(f"Precision (Class 1):    {prec:.4f}")
    print(f"Recall (Class 1):       {rec:.4f}")
    print(f"F1-Score (Class 1):     {f1:.4f}")
    print(f"Brier Score:            {brier:.4f}")
    print(f"Top-1 Race Hit Rate:    {top1_pct:.2f}% ({top1_hits}/{n_races} GPs)")
    print("-" * 50)

    # Sample Race Prediction Demonstration (2024 British GP)
    silverstone_2024 = test_slice[test_slice["race_id"] == 1132].sort_values(by="grid_position")
    if not silverstone_2024.empty:
        print("\n--- SAMPLE PREDICTIONS: 2024 BRITISH GP (RACE ID 1132) ---")
        for _, r in silverstone_2024.head(5).iterrows():
            print(f"  P{int(r['grid_position']):02d} {r['driver_name']:<20} | Baseline Win Prob: {r['pred_prob']*100:5.2f}% | Actual Winner: {bool(r['target_is_win'])}")

    return {
        "model": "Baseline Logistic Regression",
        "roc_auc": round(auc, 4),
        "pr_auc": round(pr_auc, 4),
        "f1": round(f1, 4),
        "top1_pct": round(top1_pct, 2)
    }

if __name__ == "__main__":
    train_and_evaluate_baseline()
