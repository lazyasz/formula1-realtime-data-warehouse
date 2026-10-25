"""
Champion Classification Pipeline: XGBoost Classifier
======================================================
Implements the production-grade Formula 1 Winner Classifier utilizing:
1. Complete 16-feature multidimensional vector
2. Cost-sensitive gradient boosting (`scale_pos_weight=15`)
3. Chronological out-of-sample holdout validation (2022–2024)
4. Race-level temperature-scaled Softmax Probability Normalization
5. Artifact persistence to `models/champion_xgboost_classifier.joblib`
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score,
    precision_score, recall_score, f1_score, brier_score_loss,
    confusion_matrix, classification_report
)

sys.path.append(os.path.dirname(__file__))
from feature_engineering import load_or_verify_features, extract_feature_matrix, ENGINEERED_FEATURE_COLS

def softmax_race_probabilities(probs, race_ids, temperature=0.8):
    """
    Applies temperature-scaled softmax across entrants within each race
    so that probabilities for each Grand Prix sum exactly to 1.0 (100%).
    """
    df_temp = pd.DataFrame({"prob": probs, "race_id": list(race_ids)})
    norm_probs = np.zeros(len(probs))
    
    for rid, grp in df_temp.groupby("race_id"):
        logits = np.log(np.clip(grp["prob"].values, 1e-7, 1.0 - 1e-7))
        scaled_logits = logits / temperature
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits))
        softmax_p = exp_logits / np.sum(exp_logits)
        norm_probs[grp.index.to_numpy()] = softmax_p
        
    return norm_probs

def train_and_evaluate_champion():
    print("=" * 80)
    print("   PARAMETER 06: CHAMPION XGBOOST CLASSIFIER PIPELINE")
    print("=" * 80)

    df = load_or_verify_features()
    X_train, y_train, X_test, y_test = extract_feature_matrix(df, split_season=2022)

    print(f"[+] Fitting XGBoost on 1994–2021 ({len(X_train):,} samples, 16 features)...")
    clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=15,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="logloss"
    )
    clf.fit(X_train, y_train)
    print("[+] Model fitting complete.")

    # Model Artifact Persistence
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    model_artifact_path = os.path.join(models_dir, "champion_xgboost_classifier.joblib")
    joblib.dump(clf, model_artifact_path)
    print(f"[+] Model artifact persisted to: {model_artifact_path}")

    # Raw Probabilities & Normalization
    raw_probs = clf.predict_proba(X_test)[:, 1]
    preds = clf.predict(X_test)
    
    test_slice = df.loc[df["season"] >= 2022].copy()
    test_slice["raw_prob"] = raw_probs
    test_slice["norm_prob"] = softmax_race_probabilities(raw_probs, test_slice["race_id"])

    # Classification Metrics
    auc = roc_auc_score(y_test, raw_probs)
    pr_auc = average_precision_score(y_test, raw_probs)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    brier = brier_score_loss(y_test, raw_probs)
    cm = confusion_matrix(y_test, preds)

    # Race-Level Hit Evaluation across 68 Out-of-Sample Grands Prix
    top1_hits = 0
    top3_hits = 0
    n_races = test_slice["race_id"].nunique()

    for _, grp in test_slice.groupby("race_id"):
        ranked = grp.sort_values(by="norm_prob", ascending=False)
        if ranked.iloc[0]["target_is_win"] == 1:
            top1_hits += 1
        if ranked.iloc[:3]["target_is_win"].sum() >= 1:
            top3_hits += 1

    top1_pct = (top1_hits / n_races) * 100
    top3_pct = (top3_hits / n_races) * 100

    print("\n" + "-" * 55)
    print("CHAMPION CLASSIFIER EVALUATION REPORT (2022–2024)")
    print("-" * 55)
    print(f"ROC-AUC:                     {auc:.4f}")
    print(f"PR-AUC:                      {pr_auc:.4f}")
    print(f"Accuracy:                    {acc*100:.2f}%")
    print(f"Precision (Class 1):         {prec:.4f}")
    print(f"Recall (Class 1):            {rec:.4f}")
    print(f"F1-Score (Class 1):          {f1:.4f}")
    print(f"Brier Score:                 {brier:.4f}")
    print(f"Top-1 Winner Hit Rate:       {top1_pct:.2f}% ({top1_hits}/{n_races} GPs)")
    print(f"Top-3 Winner Presence:       {top3_pct:.2f}% ({top3_hits}/{n_races} GPs)")
    print(f"\nConfusion Matrix:\n{cm}")
    print("-" * 55)

    # Feature Importance
    importance_df = pd.DataFrame({
        "feature": ENGINEERED_FEATURE_COLS,
        "importance": clf.feature_importances_
    }).sort_values(by="importance", ascending=False)
    print("\nTop 5 Most Influential Features:")
    for _, r in importance_df.head(5).iterrows():
        print(f"  - {r['feature']:<30}: {r['importance']*100:5.2f}%")

    # Sample Race Demonstration: 2024 British Grand Prix (Race ID 1132)
    sample_gp = test_slice[test_slice["race_id"] == 1132].sort_values(by="norm_prob", ascending=False)
    if not sample_gp.empty:
        print("\n--- SAMPLE SERVING OUTPUT: 2024 BRITISH GRAND PRIX ---")
        for i, (_, r) in enumerate(sample_gp.head(6).iterrows(), 1):
            is_win = " [ACTUAL WINNER]" if r["target_is_win"] == 1 else ""
            print(f"  {i}. {r['driver_name']:<20} ({r['constructor_name']:<12}) | Grid: P{int(r['grid_position']):02d} | Calibrated Win Odds: {r['norm_prob']*100:5.2f}%{is_win}")

    return clf, importance_df

if __name__ == "__main__":
    train_and_evaluate_champion()
