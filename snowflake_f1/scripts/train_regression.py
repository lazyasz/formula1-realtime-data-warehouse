"""
Formula 1 Finishing Position Prediction (Secondary Task: Regression)
=====================================================================
Predicts exact numeric finishing position (1.0 to 24.0) using pre-race features:
- CAR FEATURES (Pace index, engine BHP, reliability, starting grid)
- LAP RECORD BENCHMARKS (Track record delta, quali pace ratio)
- PIT STOP BENCHMARKS (Transit loss, pit crew efficiency, expected stops)

Kept strictly separated from the primary Winner Classification task.
Evaluates:
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Coefficient of Determination (R²)
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def train_finishing_position_regressors():
    print("=" * 80)
    print("   FORMULA 1 FINISHING POSITION REGRESSION PIPELINE (SECONDARY TASK)")
    print("=" * 80)

    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "clean_f1_modeling_master.csv")
    df = pd.read_csv(data_path, low_memory=False)

    FEATURE_COLS = [
        "car_estimated_power_bhp", "car_power_to_weight_ratio", "car_min_weight_kg",
        "car_mechanical_reliability_score", "constructor_pace_index", "grid_position",
        "qualifying_position", "driver_age_years", "driver_standing_points",
        "driver_championship_position", "constructor_standing_points", "constructor_championship_position",
        "circuit_lap_record_sec", "driver_lap_record_delta_sec", "driver_lap_record_ratio",
        "driver_quali_to_record_delta_sec", "fastest_lap_speed", "average_lap_ms", "driver_fastest_lap_sec",
        "pit_stop_count", "total_race_pit_loss_sec", "avg_pit_duration_sec",
        "estimated_stationary_pit_sec", "pit_crew_efficiency_score",
        "pit_loss_delta_to_race_mean_sec", "circuit_pit_lane_loss_sec"
    ]

    target = "finish_position"

    # Time-based train/test split (2004-2020 Train vs 2021-2024 Test)
    train_mask = df["season"] <= 2020
    test_mask = df["season"] >= 2021

    X_train = df.loc[train_mask, FEATURE_COLS]
    y_train = df.loc[train_mask, target]

    X_test = df.loc[test_mask, FEATURE_COLS]
    y_test = df.loc[test_mask, target]

    print(f"[+] Train Samples: {len(X_train):,} | Test Samples: {len(X_test):,}")

    regressors = {
        "Ridge Linear Regression": Ridge(alpha=1.0),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=120, learning_rate=0.08, max_depth=5, random_state=42)
    }

    results = []
    trained_models = {}

    for name, reg in regressors.items():
        print(f"[*] Fitting {name}...")
        reg.fit(X_train, y_train)
        trained_models[name] = reg
        
        preds = reg.predict(X_test)
        # Clip to legal F1 finishing range
        preds_clipped = np.clip(preds, 1.0, 24.0)
        
        mae = mean_absolute_error(y_test, preds_clipped)
        rmse = np.sqrt(mean_squared_error(y_test, preds_clipped))
        r2 = r2_score(y_test, preds_clipped)
        
        # Accuracy within +/- 1 position and +/- 2 positions
        within_1 = np.mean(np.abs(y_test - preds_clipped) <= 1.0) * 100
        within_2 = np.mean(np.abs(y_test - preds_clipped) <= 2.0) * 100

        print(f"    MAE: {mae:.2f} positions | RMSE: {rmse:.2f} | R²: {r2:.3f} | Within ±2 Pos: {within_2:.1f}%")

        results.append({
            "model_name": name,
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2_score": round(r2, 4),
            "within_1_position_pct": round(within_1, 2),
            "within_2_positions_pct": round(within_2, 2)
        })

    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    res_df = pd.DataFrame(results).sort_values(by="mae", ascending=True)
    res_df.to_csv(os.path.join(reports_dir, "regression_comparison.csv"), index=False)

    best_model_name = res_df.iloc[0]["model_name"]
    best_reg = trained_models[best_model_name]
    best_preds = np.clip(best_reg.predict(X_test), 1.0, 24.0)

    # Feature importance of best regressor
    if hasattr(best_reg, "feature_importances_"):
        fi_df = pd.DataFrame({
            "feature": FEATURE_COLS,
            "importance": best_reg.feature_importances_
        }).sort_values(by="importance", ascending=False)
        fi_df.to_csv(os.path.join(reports_dir, "regression_feature_importance.csv"), index=False)

    # Serialized model
    joblib.dump(best_reg, os.path.join(reports_dir, "champion_regression_model.joblib"))

    metrics_payload = {
        "best_regression_model": best_model_name,
        "mae": float(res_df.iloc[0]["mae"]),
        "rmse": float(res_df.iloc[0]["rmse"]),
        "r2_score": float(res_df.iloc[0]["r2_score"]),
        "within_1_position_pct": float(res_df.iloc[0]["within_1_position_pct"]),
        "within_2_positions_pct": float(res_df.iloc[0]["within_2_positions_pct"]),
        "error_distribution": {
            "error_mean": float(np.mean(preds_clipped - y_test)),
            "error_std": float(np.std(preds_clipped - y_test)),
            "p50_absolute_error": float(np.median(np.abs(preds_clipped - y_test))),
            "p90_absolute_error": float(np.percentile(np.abs(preds_clipped - y_test), 90))
        }
    }

    with open(os.path.join(reports_dir, "regression_metrics.json"), "w") as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"\n[+] Regression artifacts saved to {reports_dir}")
    return metrics_payload

if __name__ == "__main__":
    train_finishing_position_regressors()
