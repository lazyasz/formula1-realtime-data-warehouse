"""
Multi-Task & Multi-Class Classification Evaluation Engine
=========================================================
Evaluates 4 distinct classification tasks across the Formula 1 Dataset:
1. Task 1: Binary Winner Classification (is_win: 4.76% positive rate)
2. Task 2: Binary Podium Classification (is_podium: 14.29% positive rate)
3. Task 3: Binary Points Scorer Classification (is_top_10: 47.63% positive rate)
4. Task 4: Multi-Class 5-Tier Classification (finishing_tier: P1 Winner, P2-P3 Podium, P4-P10 Points, P11+ Backmarker, DNF)

Outputs:
- Classification metrics (ROC-AUC, PR-AUC, Accuracy, Balanced Accuracy, Precision, Recall, Macro-F1)
- Confusion Matrices
- Imbalance mitigation evaluation (scale_pos_weight, class_weight='balanced')
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, recall_score, f1_score,
    balanced_accuracy_score, classification_report, confusion_matrix, average_precision_score
)

def run_class_labels_evaluation():
    print("================================================================================")
    print("   FORMULA 1 TARGET CLASSES & LABELING SCHEME EVALUATION ENGINE")
    print("================================================================================")

    csv_path = "F1_ML_Winner_Prediction_Dataset.csv"
    df = pd.read_csv(csv_path, low_memory=False)

    # 1. Add multi-class target: finishing_tier
    def get_tier(row):
        if row["is_win"] == 1:
            return 0 # Winner (P1)
        elif row["is_podium"] == 1:
            return 1 # Podium (P2, P3)
        elif row["is_top_10"] == 1:
            return 2 # Points (P4-P10)
        elif row["is_dnf"] == 1:
            return 4 # DNF
        else:
            return 3 # Backmarker (P11+)

    df["finishing_tier"] = df.apply(get_tier, axis=1)

    # Save back to CSV & DB
    df.to_csv(csv_path, index=False)
    conn = sqlite3.connect("f1_warehouse.db")
    df.to_sql("ML_WINNER_PREDICTION_FEATURES", conn, if_exists="replace", index=False)
    conn.close()

    # Feature List
    FEATURES = [
        "car_estimated_power_bhp", "car_power_to_weight_ratio", "car_min_weight_kg",
        "car_mechanical_reliability_score", "constructor_pace_index",
        "circuit_lap_record_sec", "driver_lap_record_delta_sec", "driver_lap_record_ratio",
        "driver_quali_to_record_delta_sec", "fastest_lap_speed",
        "pit_stop_count", "total_race_pit_loss_sec", "pit_crew_efficiency_score",
        "estimated_stationary_pit_sec", "pit_loss_delta_to_race_mean_sec",
        "grid_position", "qualifying_position", "driver_standing_points",
        "driver_championship_position", "driver_championship_wins",
        "driver_standing_gap_to_leader", "constructor_standing_points",
        "constructor_championship_position"
    ]

    X = df[FEATURES].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    # Chronological Split: Train (2004-2021: 7,291 rows), Test (2022-2024: 1,359 rows)
    train_mask = df["season"] <= 2021
    test_mask = df["season"] >= 2022

    X_train, X_test = X[train_mask], X[test_mask]

    # Task Configurations
    tasks = [
        ("Task 1: Grand Prix Winner (is_win)", "is_win", "binary", 20.0),
        ("Task 2: Podium Finisher (is_podium)", "is_podium", "binary", 6.0),
        ("Task 3: Points Scorer (is_top_10)", "is_top_10", "binary", 1.0),
        ("Task 4: 5-Tier Finishing Rank (finishing_tier)", "finishing_tier", "multiclass", None)
    ]

    all_task_results = []

    for task_title, target_col, task_type, pos_weight in tasks:
        print(f"\n================================================================================")
        print(f"  {task_title}")
        print(f"================================================================================")
        
        y_train = df.loc[train_mask, target_col].astype(int)
        y_test = df.loc[test_mask, target_col].astype(int)

        print(f"[*] Target Column: '{target_col}' | Type: {task_type}")
        print(f"[*] Class Distribution in Train (2004-2021):")
        for cls_val, cnt in y_train.value_counts().items():
            print(f"    - Class {cls_val}: {cnt:>5} ({cnt/len(y_train)*100:.2f}%)")
        print(f"[*] Class Distribution in Test (2022-2024):")
        for cls_val, cnt in y_test.value_counts().items():
            print(f"    - Class {cls_val}: {cnt:>5} ({cnt/len(y_test)*100:.2f}%)")

        if task_type == "binary":
            # Train XGBoost Binary Classifier with class weight
            clf = xgb.XGBClassifier(
                n_estimators=130, max_depth=4, learning_rate=0.05,
                scale_pos_weight=pos_weight if pos_weight > 1.0 else 1.0,
                random_state=42, eval_metric="logloss"
            )
            clf.fit(X_train, y_train)
            probs = clf.predict_proba(X_test)[:, 1]
            preds = clf.predict(X_test)

            roc_auc = roc_auc_score(y_test, probs)
            pr_auc = average_precision_score(y_test, probs)
            acc = accuracy_score(y_test, preds)
            bal_acc = balanced_accuracy_score(y_test, preds)
            prec = precision_score(y_test, preds, zero_division=0)
            rec = recall_score(y_test, preds, zero_division=0)
            f1 = f1_score(y_test, preds, zero_division=0)

            print(f"\n[+] Performance Metrics:")
            print(f"    - ROC-AUC           : {roc_auc:.4f}")
            print(f"    - PR-AUC            : {pr_auc:.4f}")
            print(f"    - Accuracy          : {acc*100:.2f}%")
            print(f"    - Balanced Accuracy : {bal_acc*100:.2f}%")
            print(f"    - Precision         : {prec:.4f}")
            print(f"    - Recall            : {rec:.4f}")
            print(f"    - F1-Score          : {f1:.4f}")

            cm = confusion_matrix(y_test, preds)
            print(f"\n[+] Confusion Matrix (TN, FP / FN, TP):")
            print(f"    [[TN: {cm[0,0]:>4},  FP: {cm[0,1]:>4}]")
            print(f"     [FN: {cm[1,0]:>4},  TP: {cm[1,1]:>4}]]")

            all_task_results.append({
                "task": task_title,
                "target": target_col,
                "roc_auc": round(roc_auc, 4),
                "pr_auc": round(pr_auc, 4),
                "accuracy_pct": round(acc * 100, 2),
                "balanced_acc_pct": round(bal_acc * 100, 2),
                "f1_score": round(f1, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4)
            })

        else:
            # Multi-Class XGBoost Classifier
            clf = xgb.XGBClassifier(
                n_estimators=130, max_depth=4, learning_rate=0.05,
                objective="multi:softprob", num_class=5,
                random_state=42, eval_metric="mlogloss"
            )
            clf.fit(X_train, y_train)
            probs = clf.predict_proba(X_test)
            preds = clf.predict(X_test)

            acc = accuracy_score(y_test, preds)
            bal_acc = balanced_accuracy_score(y_test, preds)
            f1_macro = f1_score(y_test, preds, average="macro")
            f1_weighted = f1_score(y_test, preds, average="weighted")

            print(f"\n[+] Multi-Class Performance Metrics:")
            print(f"    - Overall Accuracy       : {acc*100:.2f}%")
            print(f"    - Balanced Accuracy      : {bal_acc*100:.2f}%")
            print(f"    - Macro F1-Score         : {f1_macro:.4f}")
            print(f"    - Weighted F1-Score      : {f1_weighted:.4f}")

            print(f"\n[+] Detailed Classification Report:")
            target_names = ["Tier 0 (Winner)", "Tier 1 (Podium)", "Tier 2 (Points)", "Tier 3 (Backmarker)", "Tier 4 (DNF)"]
            print(classification_report(y_test, preds, target_names=target_names, zero_division=0))

            all_task_results.append({
                "task": task_title,
                "target": target_col,
                "roc_auc": "N/A (Multi)",
                "pr_auc": "N/A (Multi)",
                "accuracy_pct": round(acc * 100, 2),
                "balanced_acc_pct": round(bal_acc * 100, 2),
                "f1_score": round(f1_macro, 4),
                "precision": "Macro",
                "recall": "Macro"
            })

    return all_task_results

if __name__ == "__main__":
    run_class_labels_evaluation()
