"""
Comprehensive Performance Metrics Calculation
============================================
Calculates empirical held-out classification metrics across:
1. Training Period:       1994–2021 (10,999 entries, 509 GPs)
2. Validation Period:     2022 (440 entries, 22 GPs) - Intro of Ground Effect
3. Test Period:           2023–2024 (919 entries, 46 GPs) - Pure Out-of-Sample
4. Full Holdout Period:   2022–2024 (1,359 entries, 68 GPs)

Outputs:
- 08_performance_metrics/classification_report.csv
- 08_performance_metrics/confusion_matrix.csv
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, log_loss, brier_score_loss,
    confusion_matrix, classification_report
)
import xgboost as xgb

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "06_classification_algorithm"))
from feature_engineering import load_or_verify_features, ENGINEERED_FEATURE_COLS

def calculate_full_metric_suite():
    print("=" * 95)
    print("   PARAMETER 08: COMPREHENSIVE PERFORMANCE METRICS SUITE")
    print("=" * 95)

    df = load_or_verify_features()
    
    # Define Chronological Partitions
    train_mask = df["season"] <= 2021
    val_mask = df["season"] == 2022
    test_mask = df["season"] >= 2023
    holdout_mask = df["season"] >= 2022

    X_train = df.loc[train_mask, ENGINEERED_FEATURE_COLS].fillna(0)
    y_train = df.loc[train_mask, "target_is_win"].astype(int)

    X_val = df.loc[val_mask, ENGINEERED_FEATURE_COLS].fillna(0)
    y_val = df.loc[val_mask, "target_is_win"].astype(int)

    X_test = df.loc[test_mask, ENGINEERED_FEATURE_COLS].fillna(0)
    y_test = df.loc[test_mask, "target_is_win"].astype(int)

    X_holdout = df.loc[holdout_mask, ENGINEERED_FEATURE_COLS].fillna(0)
    y_holdout = df.loc[holdout_mask, "target_is_win"].astype(int)

    print(f"[+] Training Set:   {len(X_train):,} rows ({df.loc[train_mask, 'race_id'].nunique()} GPs, 1994–2021)")
    print(f"[+] Validation Set: {len(X_val):,} rows ({df.loc[val_mask, 'race_id'].nunique()} GPs, 2022)")
    print(f"[+] Test Set:       {len(X_test):,} rows ({df.loc[test_mask, 'race_id'].nunique()} GPs, 2023–2024)")
    print(f"[+] Total Holdout:  {len(X_holdout):,} rows ({df.loc[holdout_mask, 'race_id'].nunique()} GPs, 2022–2024)")

    # Fit Champion Classifier on Training Set
    clf = xgb.XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.05,
        scale_pos_weight=15, subsample=0.85, colsample_bytree=0.85,
        random_state=42, eval_metric="logloss"
    )
    clf.fit(X_train, y_train)

    partitions = {
        "Training (1994–2021)": (X_train, y_train, df.loc[train_mask]),
        "Validation (2022)": (X_val, y_val, df.loc[val_mask]),
        "Test (2023–2024)": (X_test, y_test, df.loc[test_mask]),
        "Combined Holdout (2022–2024)": (X_holdout, y_holdout, df.loc[holdout_mask])
    }

    summary_rows = []

    print("\n" + "=" * 110)
    print(f"{'Partition':<28} | {'ROC-AUC':<7} | {'PR-AUC':<7} | {'Accuracy':<8} | {'Recall':<7} | {'F1':<6} | {'LogLoss':<7} | {'Brier':<6} | {'Top-1 Hit %'}")
    print("=" * 110)

    for pname, (X_p, y_p, df_p) in partitions.items():
        probs = clf.predict_proba(X_p)[:, 1]
        preds = clf.predict(X_p)

        auc = roc_auc_score(y_p, probs)
        pr_auc = average_precision_score(y_p, probs)
        acc = accuracy_score(y_p, preds) * 100
        prec = precision_score(y_p, preds, zero_division=0)
        rec = recall_score(y_p, preds, zero_division=0)
        f1 = f1_score(y_p, preds, zero_division=0)
        ll = log_loss(y_p, np.clip(probs, 1e-7, 1.0 - 1e-7))
        brier = brier_score_loss(y_p, probs)

        # Race Top-1
        df_temp = df_p.copy()
        df_temp["_p"] = probs
        top1_hits = 0
        n_gps = df_temp["race_id"].nunique()
        for _, grp in df_temp.groupby("race_id"):
            top1_hits += int(grp.sort_values(by="_p", ascending=False).iloc[0]["target_is_win"] == 1)
        top1_pct = (top1_hits / n_gps) * 100

        print(f"{pname:<28} | {auc:.4f}  | {pr_auc:.4f}  | {acc:5.2f}%  | {rec:.4f}  | {f1:.4f} | {ll:.4f}  | {brier:.4f} | {top1_pct:5.1f}% ({top1_hits:02d}/{n_gps:02d})")

        summary_rows.append({
            "partition": pname,
            "roc_auc": round(auc, 4),
            "pr_auc": round(pr_auc, 4),
            "accuracy_pct": round(acc, 2),
            "precision_class_1": round(prec, 4),
            "recall_class_1": round(rec, 4),
            "f1_class_1": round(f1, 4),
            "log_loss": round(ll, 4),
            "brier_score": round(brier, 4),
            "top1_winner_hit_pct": round(top1_pct, 2),
            "top1_hits": int(top1_hits),
            "total_gps": int(n_gps)
        })

    # Detailed Per-Class Classification Report on Holdout (2022–2024)
    probs_ho = clf.predict_proba(X_holdout)[:, 1]
    preds_ho = clf.predict(X_holdout)

    report_dict = classification_report(y_holdout, preds_ho, target_names=["Non-Winner (Class 0)", "Winner (Class 1)"], output_dict=True)
    report_df = pd.DataFrame(report_dict).T.reset_index().rename(columns={"index": "class_label"})

    out_rep_csv = os.path.join(os.path.dirname(__file__), "classification_report.csv")
    report_df.to_csv(out_rep_csv, index=False)
    print(f"\n[+] Saved Per-Class Classification Report to: {out_rep_csv}")

    # Confusion Matrix on Holdout (2022–2024)
    cm = confusion_matrix(y_holdout, preds_ho)
    cm_df = pd.DataFrame(
        cm,
        index=["Actual_Non_Winner_0", "Actual_Winner_1"],
        columns=["Predicted_Non_Winner_0", "Predicted_Winner_1"]
    )
    out_cm_csv = os.path.join(os.path.dirname(__file__), "confusion_matrix.csv")
    cm_df.to_csv(out_cm_csv)
    print(f"[+] Saved Confusion Matrix to: {out_cm_csv}")

    print("\nHoldout Confusion Matrix Breakdown:")
    print(f"  True Negatives  (TN): {cm[0, 0]:,} (Non-winners correctly identified)")
    print(f"  False Positives (FP): {cm[0, 1]:,} (Non-winners flagged as potential winners)")
    print(f"  False Negatives (FN): {cm[1, 0]:,} (Winners missed by threshold)")
    print(f"  True Positives  (TP): {cm[1, 1]:,} (Winners successfully caught: {cm[1, 1]}/{cm[1, 0] + cm[1, 1]} = {cm[1, 1]/(cm[1, 0] + cm[1, 1])*100:.1f}%)")

    return summary_rows, report_df, cm_df

if __name__ == "__main__":
    calculate_full_metric_suite()
