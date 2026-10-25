"""
Formula 1 Race Lab - Data Ingestion, Pre-Race Feature Engineering & Modeling Engine
==================================================================================
Processes the complete 1994-2024 Ergast dataset without data leakage.
Constructs strict pre-race features available BEFORE each Grand Prix.
Trains both Classification (Winner, Podium, Points, DNF) and Regression (Finishing Position) models.
Performs chronological out-of-time validation on the 2022-2024 Ground Effect Era.
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    brier_score_loss, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb
import lightgbm as lgb

ERGAST_DIR = r"C:\Users\dhruv\Downloads\archive (1)"
DB_PATH = "f1_warehouse.db"
OUTPUT_CSV = "F1_RACE_LAB_FEATURES_1994_2024.csv"
MODEL_PKL = "f1_race_lab_models.joblib"
METRICS_JSON = "race_lab_metrics.json"

def ingest_and_engineer_features():
    print("=" * 80)
    print(" [1] INGESTING HISTORICAL ERGAST DATASET (1994-2024)")
    print("=" * 80)

    # 1. Load CSVs
    races = pd.read_csv(os.path.join(ERGAST_DIR, "races.csv"))
    results = pd.read_csv(os.path.join(ERGAST_DIR, "results.csv"))
    drivers = pd.read_csv(os.path.join(ERGAST_DIR, "drivers.csv"))
    constructors = pd.read_csv(os.path.join(ERGAST_DIR, "constructors.csv"))
    circuits = pd.read_csv(os.path.join(ERGAST_DIR, "circuits.csv"))
    status = pd.read_csv(os.path.join(ERGAST_DIR, "status.csv"))

    # Optional qualifying
    qualifying = pd.read_csv(os.path.join(ERGAST_DIR, "qualifying.csv"))

    print(f"[*] Loaded raw tables:")
    print(f"    - races: {len(races):,} rows")
    print(f"    - results: {len(results):,} rows")
    print(f"    - drivers: {len(drivers):,} rows")
    print(f"    - constructors: {len(constructors):,} rows")
    print(f"    - circuits: {len(circuits):,} rows")

    # Filter races: 1994 to 2024
    races_subset = races[(races["year"] >= 1994) & (races["year"] <= 2024)].copy()
    races_subset.sort_values(by=["year", "round"], inplace=True)
    race_ids = set(races_subset["raceId"])

    results_subset = results[results["raceId"].isin(race_ids)].copy()
    print(f"[+] 1994-2024 Universe: {len(races_subset)} Races | {len(results_subset):,} Driver Entries")

    # Merge race metadata
    df = results_subset.merge(
        races_subset[["raceId", "year", "round", "circuitId", "name", "date"]],
        on="raceId", how="left"
    )

    # Merge circuit metadata
    df = df.merge(
        circuits[["circuitId", "circuitRef", "name", "country", "alt"]].rename(
            columns={"name": "circuit_name", "alt": "circuit_alt"}
        ),
        on="circuitId", how="left"
    )

    # Merge driver metadata
    df = df.merge(
        drivers[["driverId", "driverRef", "code", "forename", "surname", "dob", "nationality"]],
        on="driverId", how="left"
    )
    df["driver_name"] = df["forename"] + " " + df["surname"]

    # Merge constructor metadata
    df = df.merge(
        constructors[["constructorId", "constructorRef", "name", "nationality"]].rename(
            columns={"name": "constructor_name", "nationality": "constructor_nat"}
        ),
        on="constructorId", how="left"
    )

    # Merge status
    df = df.merge(status, on="statusId", how="left")

    # Chronological sort
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["date", "raceId", "grid"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # -------------------------------------------------------------------------
    # Parse Targets
    # -------------------------------------------------------------------------
    df["finish_pos"] = pd.to_numeric(df["positionOrder"], errors="coerce").fillna(20).astype(int)
    df["target_is_win"] = (df["finish_pos"] == 1).astype(int)
    df["target_is_podium"] = (df["finish_pos"] <= 3).astype(int)
    df["target_is_points"] = (df["finish_pos"] <= 10).astype(int)

    # DNF target: statusId 1 is 'Finished', statusId in (+1 Lap, etc. is also classified)
    # Statuses like 1 (Finished), 11 (+1 Lap), 12 (+2 Laps), 13 (+3 Laps) are classified finishes.
    classified_status_ids = {1, 11, 12, 13, 14, 15, 16, 17, 18, 19, 45, 53, 88}
    df["target_is_dnf"] = (~df["statusId"].isin(classified_status_ids)).astype(int)
    df["target_finish_position"] = df["finish_pos"].clip(1, 20)

    # Clean grid position (grid 0 means pit lane start or unclassified grid, treat as 20)
    df["grid_position"] = pd.to_numeric(df["grid"], errors="coerce").fillna(20).astype(int)
    df["grid_position"] = df["grid_position"].apply(lambda g: 20 if g <= 0 else min(g, 20))

    # Driver Age in years
    df["dob_dt"] = pd.to_datetime(df["dob"], errors="coerce")
    df["driver_age"] = (df["date"] - df["dob_dt"]).dt.days / 365.25
    df["driver_age"] = df["driver_age"].fillna(26.0).clip(17, 55)

    print("\n" + "=" * 80)
    print(" [2] LEAK-FREE PRE-RACE FEATURE ENGINEERING")
    print("=" * 80)
    print("[*] Computing historical rolling statistics strictly prior to each event...")

    # We iterate chronologically to ensure zero future leakage
    records = []
    
    # Historical accumulators
    driver_history = {}       # driverId -> list of {finish_pos, points, dnf, date}
    constructor_history = {}  # constructorId -> list of {finish_pos, points, date}
    circuit_driver_hist = {}  # (circuitId, driverId) -> list of finish_pos
    driver_season_pts = {}    # (year, driverId) -> total points before race
    driver_career_stats = {}  # driverId -> {starts, wins, podiums, dnfs}

    # Qualifying teammate battle lookup
    # Find qualifying position if available
    quali_lookup = {}
    if len(qualifying) > 0:
        for _, qrow in qualifying.iterrows():
            quali_lookup[(qrow["raceId"], qrow["driverId"])] = qrow["position"]

    # Process race-by-race in chronological order
    for (year, race_id), race_group in df.groupby(["year", "raceId"], sort=False):
        # Determine teammate qualifying positions for this race
        constructor_drivers = {}
        for _, row in race_group.iterrows():
            cid = row["constructorId"]
            did = row["driverId"]
            grid_p = row["grid_position"]
            constructor_drivers.setdefault(cid, []).append((did, grid_p))

        # Check teammate quali lead
        teammate_advantage = {}
        for cid, dlist in constructor_drivers.items():
            if len(dlist) == 2:
                d1, g1 = dlist[0]
                d2, g2 = dlist[1]
                teammate_advantage[d1] = 1 if g1 < g2 else 0
                teammate_advantage[d2] = 1 if g2 < g1 else 0
            else:
                for did, _ in dlist:
                    teammate_advantage[did] = 0

        # Compute pre-race features for every driver in this race
        for _, row in race_group.iterrows():
            did = row["driverId"]
            cid = row["constructorId"]
            cir_id = row["circuitId"]
            points_scored = float(row["points"]) if pd.notna(row["points"]) else 0.0

            # 1. Driver recent form (last 5 races prior to this)
            dh = driver_history.get(did, [])
            if len(dh) > 0:
                recent_5 = dh[-5:]
                d_roll_finish_5 = np.mean([x["finish_pos"] for x in recent_5])
                d_roll_points_5 = np.mean([x["points"] for x in recent_5])
                d_dnf_rate_career = np.mean([x["dnf"] for x in dh])
            else:
                d_roll_finish_5 = 14.0
                d_roll_points_5 = 0.5
                d_dnf_rate_career = 0.20

            # 2. Constructor recent form (last 10 entries prior to this)
            ch = constructor_history.get(cid, [])
            if len(ch) > 0:
                c_roll_finish_10 = np.mean([x["finish_pos"] for x in ch[-10:]])
                c_roll_points_10 = np.mean([x["points"] for x in ch[-10:]])
            else:
                c_roll_finish_10 = 12.0
                c_roll_points_10 = 1.0

            # 3. Circuit historical performance
            cdh = circuit_driver_hist.get((cir_id, did), [])
            if len(cdh) > 0:
                circuit_avg_finish = np.mean(cdh)
                circuit_win_rate = np.mean([1 if pos == 1 else 0 for pos in cdh])
                circuit_podium_rate = np.mean([1 if pos <= 3 else 0 for pos in cdh])
                circuit_experience = len(cdh)
            else:
                circuit_avg_finish = 13.0
                circuit_win_rate = 0.0
                circuit_podium_rate = 0.0
                circuit_experience = 0

            # 4. Season-to-date points before race
            season_pts_before = driver_season_pts.get((year, did), 0.0)

            # 5. Career starts, wins, podiums before race
            dc = driver_career_stats.get(did, {"starts": 0, "wins": 0, "podiums": 0, "dnfs": 0})
            career_starts = dc["starts"]
            career_wins = dc["wins"]
            career_podiums = dc["podiums"]
            career_win_rate = (career_wins / career_starts) if career_starts > 0 else 0.0

            # 6. Teammate beat in qualifying
            ahead_teammate = teammate_advantage.get(did, 0)

            # Grid to rolling finish expected conversion gap
            grid_vs_form_gap = row["grid_position"] - d_roll_finish_5

            rec = {
                "result_id": int(row["resultId"]),
                "race_id": int(row["raceId"]),
                "season": int(row["year"]),
                "round": int(row["round"]),
                "circuit_id": int(row["circuitId"]),
                "circuit_name": str(row["circuit_name"]),
                "circuit_country": str(row["country"]),
                "race_name": str(row["name"]),
                "race_date": str(row["date"].strftime("%Y-%m-%d")),
                "driver_id": int(row["driverId"]),
                "driver_code": str(row["code"]) if pd.notna(row["code"]) else str(row["surname"][:3].upper()),
                "driver_name": str(row["driver_name"]),
                "constructor_id": int(row["constructorId"]),
                "constructor_name": str(row["constructor_name"]),
                # PRE-RACE MODEL FEATURES
                "grid_position": int(row["grid_position"]),
                "driver_rolling_finish_5": round(float(d_roll_finish_5), 2),
                "driver_rolling_points_5": round(float(d_roll_points_5), 2),
                "constructor_rolling_finish_10": round(float(c_roll_finish_10), 2),
                "constructor_rolling_points_10": round(float(c_roll_points_10), 2),
                "circuit_avg_finish": round(float(circuit_avg_finish), 2),
                "circuit_win_rate": round(float(circuit_win_rate), 4),
                "circuit_podium_rate": round(float(circuit_podium_rate), 4),
                "circuit_experience": int(circuit_experience),
                "season_points_before": round(float(season_pts_before), 1),
                "career_starts": int(career_starts),
                "career_win_rate": round(float(career_win_rate), 4),
                "career_dnf_rate": round(float(d_dnf_rate_career), 4),
                "ahead_of_teammate_grid": int(ahead_teammate),
                "driver_age": round(float(row["driver_age"]), 1),
                "grid_vs_form_gap": round(float(grid_vs_form_gap), 2),
                # TARGET VARIABLES
                "target_is_win": int(row["target_is_win"]),
                "target_is_podium": int(row["target_is_podium"]),
                "target_is_points": int(row["target_is_points"]),
                "target_is_dnf": int(row["target_is_dnf"]),
                "target_finish_position": int(row["target_finish_position"])
            }
            records.append(rec)

        # AFTER the race is completed: Update historical accumulators for future races!
        for _, row in race_group.iterrows():
            did = row["driverId"]
            cid = row["constructorId"]
            cir_id = row["circuitId"]
            fpos = int(row["finish_pos"])
            pts = float(row["points"]) if pd.notna(row["points"]) else 0.0
            is_dnf = int(row["target_is_dnf"])
            is_win = int(row["target_is_win"])
            is_pod = int(row["target_is_podium"])

            # Driver history
            driver_history.setdefault(did, []).append({"finish_pos": fpos, "points": pts, "dnf": is_dnf})
            # Constructor history
            constructor_history.setdefault(cid, []).append({"finish_pos": fpos, "points": pts})
            # Circuit history
            circuit_driver_hist.setdefault((cir_id, did), []).append(fpos)
            # Season points
            driver_season_pts[(year, did)] = driver_season_pts.get((year, did), 0.0) + pts
            # Career stats
            dc = driver_career_stats.setdefault(did, {"starts": 0, "wins": 0, "podiums": 0, "dnfs": 0})
            dc["starts"] += 1
            dc["wins"] += is_win
            dc["podiums"] += is_pod
            dc["dnfs"] += is_dnf

    df_feat = pd.DataFrame(records)
    print(f"[+] Feature store constructed: {len(df_feat):,} records across {df_feat['race_id'].nunique()} races.")
    df_feat.to_csv(OUTPUT_CSV, index=False)
    print(f"[OK] Saved pre-race features to '{OUTPUT_CSV}'")

    # Sync into SQLite
    conn = sqlite3.connect(DB_PATH)
    df_feat.to_sql("F1_RACE_LAB_FEATURES", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"[OK] Registered table 'F1_RACE_LAB_FEATURES' in SQLite database.")

    return df_feat

def train_and_validate_models(df_feat):
    print("\n" + "=" * 80)
    print(" [3] CHRONOLOGICAL OUT-OF-TIME VALIDATION & MODEL TRAINING")
    print("=" * 80)

    # Pre-race feature list
    FEATURE_COLS = [
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

    print(f"[*] Features Utilized ({len(FEATURE_COLS)}):")
    for f in FEATURE_COLS:
        print(f"    - {f}")

    # Chronological Split:
    # Train: 1994 - 2021 (Earlier eras)
    # Out-of-Time Test: 2022 - 2024 (Ground Effect Era)
    train_mask = df_feat["season"] <= 2021
    test_mask = df_feat["season"] >= 2022

    X_train = df_feat.loc[train_mask, FEATURE_COLS].copy()
    X_test = df_feat.loc[test_mask, FEATURE_COLS].copy()

    test_races = df_feat.loc[test_mask, "race_id"].nunique()
    print(f"\n[*] Train Set (1994-2021): {len(X_train):,} rows")
    print(f"[*] Out-of-Time Test Set (2022-2024): {len(X_test):,} rows ({test_races} Grands Prix)")

    metrics_suite = {}

    # =========================================================================
    # TARGET 1: RACE WINNER CLASSIFICATION (is_win)
    # =========================================================================
    print("\n--- [Target 1: Race Winner Classification] ---")
    y_win_train = df_feat.loc[train_mask, "target_is_win"]
    y_win_test = df_feat.loc[test_mask, "target_is_win"]

    win_models = {
        "Baseline (Logistic Regression on Grid)": LogisticRegression(max_iter=500),
        "Random Forest Classifier": RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42),
        "LightGBM Classifier": lgb.LGBMClassifier(n_estimators=100, max_depth=4, learning_rate=0.06, random_state=42, verbose=-1),
        "XGBoost Classifier": xgb.XGBClassifier(n_estimators=120, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")
    }

    win_eval = {}
    best_win_model = None
    best_win_auc = 0.0

    for name, clf in win_models.items():
        if "Baseline" in name:
            clf.fit(X_train[["grid_position"]], y_win_train)
            probs = clf.predict_proba(X_test[["grid_position"]])[:, 1]
            preds = clf.predict(X_test[["grid_position"]])
        else:
            clf.fit(X_train, y_win_train)
            probs = clf.predict_proba(X_test)[:, 1]
            preds = clf.predict(X_test)

        auc = roc_auc_score(y_win_test, probs)
        brier = brier_score_loss(y_win_test, probs)
        acc = accuracy_score(y_win_test, preds)
        prec = precision_score(y_win_test, preds, zero_division=0)
        rec = recall_score(y_win_test, preds, zero_division=0)
        f1 = f1_score(y_win_test, preds, zero_division=0)

        # Evaluate Top-1 Race Winner Hit Rate
        df_test_eval = df_feat[test_mask].copy()
        df_test_eval["prob"] = probs
        top1_hits = 0
        top3_hits = 0
        total_gps = 0

        for r_id, grp in df_test_eval.groupby("race_id"):
            total_gps += 1
            ranked = grp.sort_values(by="prob", ascending=False)
            actual_w = grp[grp["target_is_win"] == 1]
            if len(actual_w) > 0:
                act_w_did = actual_w.iloc[0]["driver_id"]
                pred_p1 = ranked.iloc[0]["driver_id"]
                pred_p3 = ranked.iloc[:3]["driver_id"].values
                if pred_p1 == act_w_did:
                    top1_hits += 1
                if act_w_did in pred_p3:
                    top3_hits += 1

        top1_pct = round(top1_hits / total_gps * 100, 2)
        top3_pct = round(top3_hits / total_gps * 100, 2)

        win_eval[name] = {
            "roc_auc": round(auc, 4),
            "top1_winner_accuracy": f"{top1_pct}% ({top1_hits}/{total_gps})",
            "top3_podium_hit": f"{top3_pct}% ({top3_hits}/{total_gps})",
            "brier_score": round(brier, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4)
        }
        print(f"  {name:<38} | ROC-AUC: {auc:.4f} | Top-1 Win: {top1_pct}% | Brier: {brier:.4f}")

        if auc > best_win_auc:
            best_win_auc = auc
            best_win_model = clf

    metrics_suite["winner_models"] = win_eval

    # =========================================================================
    # TARGET 2: PODIUM CLASSIFICATION (is_podium)
    # =========================================================================
    print("\n--- [Target 2: Podium Finish Classification] ---")
    y_pod_train = df_feat.loc[train_mask, "target_is_podium"]
    y_pod_test = df_feat.loc[test_mask, "target_is_podium"]

    clf_podium = xgb.XGBClassifier(n_estimators=120, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")
    clf_podium.fit(X_train, y_pod_train)
    pod_probs = clf_podium.predict_proba(X_test)[:, 1]
    pod_preds = clf_podium.predict(X_test)
    pod_auc = roc_auc_score(y_pod_test, pod_probs)
    pod_acc = accuracy_score(y_pod_test, pod_preds)
    pod_prec = precision_score(y_pod_test, pod_preds, zero_division=0)
    pod_rec = recall_score(y_pod_test, pod_preds, zero_division=0)
    pod_f1 = f1_score(y_pod_test, pod_preds, zero_division=0)
    metrics_suite["podium_model"] = {
        "roc_auc": round(pod_auc, 4),
        "accuracy": round(pod_acc * 100, 2),
        "precision": round(pod_prec, 4),
        "recall": round(pod_rec, 4),
        "f1_score": round(pod_f1, 4)
    }
    print(f"  XGBoost Podium Classifier: ROC-AUC {pod_auc:.4f} | F1-Score {pod_f1:.4f} | Accuracy {pod_acc*100:.1f}%")

    # =========================================================================
    # TARGET 3: POINTS FINISH CLASSIFICATION (is_points)
    # =========================================================================
    print("\n--- [Target 3: Points Finish Classification (Top 10)] ---")
    y_pts_train = df_feat.loc[train_mask, "target_is_points"]
    y_pts_test = df_feat.loc[test_mask, "target_is_points"]

    clf_points = lgb.LGBMClassifier(n_estimators=120, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
    clf_points.fit(X_train, y_pts_train)
    pts_probs = clf_points.predict_proba(X_test)[:, 1]
    pts_preds = clf_points.predict(X_test)
    pts_auc = roc_auc_score(y_pts_test, pts_probs)
    pts_acc = accuracy_score(y_pts_test, pts_preds)
    pts_f1 = f1_score(y_pts_test, pts_preds, zero_division=0)
    metrics_suite["points_model"] = {
        "roc_auc": round(pts_auc, 4),
        "accuracy": round(pts_acc * 100, 2),
        "f1_score": round(pts_f1, 4)
    }
    print(f"  LightGBM Points Classifier: ROC-AUC {pts_auc:.4f} | Accuracy {pts_acc*100:.1f}% | F1 {pts_f1:.4f}")

    # =========================================================================
    # TARGET 4: DNF CLASSIFICATION (is_dnf)
    # =========================================================================
    print("\n--- [Target 4: DNF / Retirement Classification] ---")
    y_dnf_train = df_feat.loc[train_mask, "target_is_dnf"]
    y_dnf_test = df_feat.loc[test_mask, "target_is_dnf"]

    clf_dnf = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
    clf_dnf.fit(X_train, y_dnf_train)
    dnf_probs = clf_dnf.predict_proba(X_test)[:, 1]
    dnf_preds = clf_dnf.predict(X_test)
    dnf_auc = roc_auc_score(y_dnf_test, dnf_probs)
    metrics_suite["dnf_model"] = {
        "roc_auc": round(dnf_auc, 4),
        "dnf_prevalence_pct": round(float(y_dnf_test.mean() * 100), 2)
    }
    print(f"  GBDT DNF Classifier: ROC-AUC {dnf_auc:.4f} | Test DNF Prevalence {y_dnf_test.mean()*100:.1f}%")

    # =========================================================================
    # TARGET 5: FINISHING POSITION REGRESSION / RANKING (finish_position)
    # =========================================================================
    print("\n--- [Target 5: Finishing Position Prediction (Regression)] ---")
    y_pos_train = df_feat.loc[train_mask, "target_finish_position"]
    y_pos_test = df_feat.loc[test_mask, "target_finish_position"]

    # Benchmark Ridge vs Random Forest vs GBDT Regressor
    reg_models = {
        "Baseline (Grid Position Only)": Ridge(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=150, max_depth=6, random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=120, max_depth=4, learning_rate=0.06, random_state=42)
    }

    pos_eval = {}
    best_reg_model = None
    best_mae = 999.0

    for rname, reg in reg_models.items():
        if "Baseline" in rname:
            reg.fit(X_train[["grid_position"]], y_pos_train)
            pred_pos = reg.predict(X_test[["grid_position"]])
        else:
            reg.fit(X_train, y_pos_train)
            pred_pos = reg.predict(X_test)

        mae = mean_absolute_error(y_pos_test, pred_pos)
        rmse = np.sqrt(mean_squared_error(y_pos_test, pred_pos))
        r2 = r2_score(y_pos_test, pred_pos)

        pos_eval[rname] = {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2_score": round(r2, 4)
        }
        print(f"  {rname:<38} | MAE: {mae:.2f} positions | RMSE: {rmse:.2f} | R²: {r2:.4f}")

        if mae < best_mae:
            best_mae = mae
            best_reg_model = reg

    metrics_suite["position_regression"] = pos_eval

    # -------------------------------------------------------------------------
    # Feature Importance for Winner XGBoost
    # -------------------------------------------------------------------------
    feat_imps = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": best_win_model.feature_importances_
    }).sort_values(by="importance", ascending=False)
    feat_imps["importance_pct"] = (feat_imps["importance"] / feat_imps["importance"].sum() * 100).round(2)
    metrics_suite["feature_importances"] = feat_imps.to_dict(orient="records")

    print("\n[*] Top 8 Feature Importances (XGBoost Winner Model):")
    for _, r in feat_imps.head(8).iterrows():
        print(f"    - {r['feature']:<30}: {r['importance_pct']:.2f}%")

    # -------------------------------------------------------------------------
    # Save Model Artifacts
    # -------------------------------------------------------------------------
    artifacts = {
        "features": FEATURE_COLS,
        "win_model": best_win_model,
        "podium_model": clf_podium,
        "points_model": clf_points,
        "dnf_model": clf_dnf,
        "position_regressor": best_reg_model,
        "all_win_models": win_models,
        "metrics": metrics_suite
    }
    joblib.dump(artifacts, MODEL_PKL)
    print(f"\n[OK] Saved all trained models to '{MODEL_PKL}'")

    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics_suite, f, indent=2)
    print(f"[OK] Saved validation metrics to '{METRICS_JSON}'")

    return artifacts

if __name__ == "__main__":
    df_feat = ingest_and_engineer_features()
    artifacts = train_and_validate_models(df_feat)
    print("\n[SUCCESS] Race Lab Data & ML Engine fully built and calibrated!")
