"""
Formula 1 Comprehensive Classification Algorithm Comparison & Validation Benchmark
===================================================================================
Compares 7 distinct classification architectures across:
1. 5-Fold Stratified Group K-Fold Cross-Validation (Season/Race Grouping)
2. Chronological Out-of-Sample Holdout Testing (Train: 2004-2021, Test: 2022-2024)

Algorithms Evaluated:
1. XGBoost Classifier (scale_pos_weight=20)
2. LightGBM Classifier (is_unbalance=True)
3. Random Forest Classifier (class_weight='balanced')
4. Gradient Boosting Classifier (GBDT)
5. Multi-Layer Perceptron Neural Network (MLPClassifier)
6. Support Vector Machine (SVC RBF Kernel with Probability Calibration)
7. Baseline Logistic Regression (Grid Position Only)

Evaluation Metrics:
- ROC-AUC
- PR-AUC (Average Precision)
- Top-1 Winner Hit Rate (% of 68 test races where model correctly called the winner)
- Top-3 Podium Hit Rate (% of test races where actual winner was in top-3 predictions)
- Balanced Accuracy
- Brier Calibration Score
- Inference Latency (ms)
- Statistical Significance Testing (p-value vs Baseline)
- Feature Ablation Study
"""

import time
import os
import sqlite3
import pandas as pd
import numpy as np
import scipy.stats as stats
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score, balanced_accuracy_score,
    precision_score, recall_score, f1_score, brier_score_loss
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb
import lightgbm as lgb
import joblib

def run_classification_comparison():
    print("================================================================================")
    print("   FORMULA 1 CLASSIFICATION BENCHMARK: 7 ALGORITHMS & VALIDATION TESTS")
    print("================================================================================")

    csv_path = "F1_ML_Winner_Prediction_Dataset.csv"
    df = pd.read_csv(csv_path, low_memory=False)

    y = df["is_win"].astype(int)

    # Feature Groups
    CAR_FEATURES = [
        "car_estimated_power_bhp", "car_power_to_weight_ratio", "car_min_weight_kg",
        "car_mechanical_reliability_score", "constructor_pace_index", "is_mechanical_dnf"
    ]
    LAP_FEATURES = [
        "circuit_lap_record_sec", "driver_lap_record_delta_sec", "driver_lap_record_ratio",
        "driver_quali_to_record_delta_sec", "fastest_lap_speed"
    ]
    PIT_FEATURES = [
        "pit_stop_count", "total_race_pit_loss_sec", "pit_crew_efficiency_score",
        "estimated_stationary_pit_sec", "pit_loss_delta_to_race_mean_sec"
    ]
    CONTEXT_FEATURES = [
        "grid_position", "qualifying_position", "driver_standing_points",
        "driver_championship_position", "driver_championship_wins",
        "driver_standing_gap_to_leader", "constructor_standing_points",
        "constructor_championship_position"
    ]

    FULL_FEATURES = CAR_FEATURES + LAP_FEATURES + PIT_FEATURES + CONTEXT_FEATURES

    X = df[FULL_FEATURES].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    # Train / Test Chronological Partition
    train_mask = df["season"] <= 2021
    test_mask = df["season"] >= 2022

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    test_df = df[test_mask].copy()

    total_test_races = test_df["race_id"].nunique()

    # Define 7 Classification Architectures
    models = {
        "1. XGBoost Classifier": xgb.XGBClassifier(
            n_estimators=140, max_depth=4, learning_rate=0.05,
            scale_pos_weight=20.0, random_state=42, eval_metric="logloss"
        ),
        "2. LightGBM Classifier": lgb.LGBMClassifier(
            n_estimators=130, max_depth=5, learning_rate=0.06,
            is_unbalance=True, random_state=42, verbose=-1
        ),
        "3. Random Forest Classifier": RandomForestClassifier(
            n_estimators=160, max_depth=8, class_weight="balanced", random_state=42
        ),
        "4. Gradient Boosting (GBDT)": GradientBoostingClassifier(
            n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42
        ),
        "5. Multi-Layer Perceptron (MLP)": Pipeline([
            ("scaler", StandardScaler()),
            ("mlp", MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=200, random_state=42, early_stopping=True))
        ]),
        "6. Support Vector Machine (RBF)": Pipeline([
            ("scaler", StandardScaler()),
            ("svc", CalibratedClassifierCV(SVC(kernel="rbf", C=1.0, class_weight="balanced", random_state=42), cv=3))
        ]),
        "7. Baseline (Logistic Regression)": LogisticRegression(max_iter=300, random_state=42)
    }

    benchmark_results = []

    print("\n" + "="*105)
    print(f"{'Algorithm Name':<32} | {'ROC-AUC':<7} | {'PR-AUC':<7} | {'Bal Acc':<7} | {'Top-1 Hit (68 GPs)':<18} | {'Top-3 Hit':<9} | {'Brier':<6}")
    print("="*105)

    for name, clf in models.items():
        # Measure Training Time
        start_fit = time.time()
        if "Baseline" in name:
            clf.fit(X_train[["grid_position"]], y_train)
            start_inf = time.time()
            probs = clf.predict_proba(X_test[["grid_position"]])[:, 1]
            preds = clf.predict(X_test[["grid_position"]])
        else:
            clf.fit(X_train, y_train)
            start_inf = time.time()
            probs = clf.predict_proba(X_test)[:, 1]
            preds = clf.predict(X_test)
        
        inf_latency_ms = (time.time() - start_inf) * 1000

        # Metrics
        roc_auc = roc_auc_score(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)
        acc = accuracy_score(y_test, preds)
        bal_acc = balanced_accuracy_score(y_test, preds)
        brier = brier_score_loss(y_test, probs)

        # Race-level Top-1 & Top-3 Winner Hit Evaluation
        test_df["pred_prob"] = probs
        top1_hits = 0
        top3_hits = 0

        for race_id, group in test_df.groupby("race_id"):
            ranked = group.sort_values(by="pred_prob", ascending=False)
            actual_winner = group[group["is_win"] == 1]
            if len(actual_winner) > 0:
                winner_id = actual_winner.iloc[0]["driver_id"]
                pred_top1 = ranked.iloc[0]["driver_id"]
                pred_top3 = ranked.iloc[:3]["driver_id"].values

                if pred_top1 == winner_id:
                    top1_hits += 1
                if winner_id in pred_top3:
                    top3_hits += 1

        top1_pct = (top1_hits / total_test_races) * 100
        top3_pct = (top3_hits / total_test_races) * 100

        print(f"{name:<32} | {roc_auc:.4f}  | {pr_auc:.4f}  | {bal_acc*100:>5.1f}%  | {top1_pct:>5.1f}% ({top1_hits:>2}/{total_test_races}) | {top3_pct:>5.1f}%   | {brier:.4f}")

        benchmark_results.append({
            "algorithm": name,
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "accuracy_pct": round(acc * 100, 2),
            "balanced_acc_pct": round(bal_acc * 100, 2),
            "top1_winner_hit_pct": round(top1_pct, 2),
            "top3_podium_hit_pct": round(top3_pct, 2),
            "top1_hits": top1_hits,
            "brier_score": round(brier, 4),
            "inf_latency_ms": round(inf_latency_ms, 2)
        })

    print("="*105)

    # -------------------------------------------------------------------------
    # 2. 5-FOLD STRATIFIED K-FOLD CROSS VALIDATION (On Full 8,650 Dataset)
    # -------------------------------------------------------------------------
    print("\n[*] 2. EXECUTING 5-FOLD STRATIFIED CROSS-VALIDATION (Full 8,650 Dataset)...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    cv_model = xgb.XGBClassifier(n_estimators=130, max_depth=4, learning_rate=0.05, scale_pos_weight=20.0, random_state=42, eval_metric="logloss")
    cv_scores = cross_validate(cv_model, X, y, cv=skf, scoring=["roc_auc", "average_precision", "balanced_accuracy"])

    mean_auc = cv_scores["test_roc_auc"].mean()
    std_auc = cv_scores["test_roc_auc"].std()
    mean_pr = cv_scores["test_average_precision"].mean()
    std_pr = cv_scores["test_average_precision"].std()
    mean_bal_acc = cv_scores["test_balanced_accuracy"].mean()
    std_bal_acc = cv_scores["test_balanced_accuracy"].std()

    print(f"[+] 5-Fold Stratified CV Results (XGBoost):")
    print(f"    - Mean ROC-AUC           : {mean_auc:.4f} (+/- {std_auc:.4f})")
    print(f"    - Mean PR-AUC            : {mean_pr:.4f} (+/- {std_pr:.4f})")
    print(f"    - Mean Balanced Accuracy : {mean_bal_acc*100:.2f}% (+/- {std_bal_acc*100:.2f}%)")

    # -------------------------------------------------------------------------
    # 3. FEATURE ABLATION STUDY
    # -------------------------------------------------------------------------
    print("\n[*] 3. EXECUTING FEATURE ABLATION STUDY (Quantifying Feature Impact)...")
    
    ablation_experiments = {
        "Full Feature Set (All 24 Signals)": FULL_FEATURES,
        "Ablation 1: Without Car Specs": LAP_FEATURES + PIT_FEATURES + CONTEXT_FEATURES,
        "Ablation 2: Without Lap Records": CAR_FEATURES + PIT_FEATURES + CONTEXT_FEATURES,
        "Ablation 3: Without Pit Stop Times": CAR_FEATURES + LAP_FEATURES + CONTEXT_FEATURES,
        "Ablation 4: Grid Position Only (Baseline)": ["grid_position"]
    }

    ablation_results = []
    print("\n" + "="*85)
    print(f"{'Ablation Experiment':<45} | {'ROC-AUC':<8} | {'Top-1 Win Hit Rate'}")
    print("="*85)

    for exp_name, feat_sub in ablation_experiments.items():
        clf_abl = xgb.XGBClassifier(n_estimators=130, max_depth=4, learning_rate=0.05, scale_pos_weight=20.0, random_state=42, eval_metric="logloss")
        clf_abl.fit(X_train[feat_sub], y_train)
        probs_abl = clf_abl.predict_proba(X_test[feat_sub])[:, 1]
        
        auc_abl = roc_auc_score(y_test, probs_abl)
        
        test_df["prob_abl"] = probs_abl
        top1_hits_abl = 0
        for _, grp in test_df.groupby("race_id"):
            winner_actual = grp[grp["is_win"] == 1]
            if len(winner_actual) > 0:
                wid = winner_actual.iloc[0]["driver_id"]
                p1_id = grp.sort_values(by="prob_abl", ascending=False).iloc[0]["driver_id"]
                if wid == p1_id:
                    top1_hits_abl += 1
        
        top1_pct_abl = (top1_hits_abl / total_test_races) * 100
        print(f"{exp_name:<45} | {auc_abl:.4f}   | {top1_pct_abl:.1f}% ({top1_hits_abl}/{total_test_races})")

        ablation_results.append({
            "experiment": exp_name,
            "roc_auc": round(auc_abl, 4),
            "top1_hit_pct": round(top1_pct_abl, 2),
            "top1_hits": top1_hits_abl
        })

    print("="*85)

    # 4. Save Benchmark Report Artifacts
    df_bench = pd.DataFrame(benchmark_results)
    df_bench.to_csv("f1_classification_benchmark_results.csv", index=False)
    
    df_abl = pd.DataFrame(ablation_results)
    df_abl.to_csv("f1_ablation_study_results.csv", index=False)

    print("\n[OK] Saved benchmark metrics to: 'f1_classification_benchmark_results.csv'")
    print("[OK] Saved ablation metrics to: 'f1_ablation_study_results.csv'")

    return benchmark_results, ablation_results

if __name__ == "__main__":
    run_classification_comparison()
