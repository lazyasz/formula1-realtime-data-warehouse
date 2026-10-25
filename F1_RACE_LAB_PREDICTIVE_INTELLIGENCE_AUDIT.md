# 🏎️ Formula 1 Predictive Intelligence — The Race Lab
## Comprehensive Engineering Audit, Data Pipeline & Machine Learning Report

---

### Executive Summary

This report documents the architectural audit, dataset ingestion, pre-race feature engineering, model training, chronological out-of-time validation, and interactive product implementation for **F1 Predictive Intelligence: The Race Lab**.

The platform is designed as an industrial motorsport decision-support system and machine learning laboratory. It strictly separates pre-race observables from post-race outcomes, eliminates data leakage, trains both classification and regression models on the **1994–2024 Ergast universe (577 Grands Prix, 12,358 driver race entries)**, and provides an interactive **Scenario Studio** where race strategists can test hypothetical scenarios and forecast the remaining races of the **2026 championship season**.

---

## 1. Dataset Audit & Schema Discovery (1994–2024)

### 1.1 Ingested Tables & Entity Relationships

The platform ingests the complete historical Formula 1 relational dataset from the Ergast archive located at `C:\Users\dhruv\Downloads\archive (1)`:

| Entity / Table | Raw Total Rows | Columns | Filtered 1994–2024 Rows | Role in Prediction Pipeline |
| :--- | :---: | :---: | :---: | :--- |
| **`races.csv`** | 1,125 | 18 | **577** | Event dimension: Season, round, circuit, date, official event name. |
| **`results.csv`** | 26,759 | 18 | **12,358** | Fact table: Grid, finishing position, points, laps, time, status. |
| **`drivers.csv`** | 861 | 9 | **174 active** | Driver dimension: Driver reference, permanent code, DOB, nationality. |
| **`constructors.csv`** | 212 | 5 | **48 active** | Constructor dimension: Team reference, name, nationality. |
| **`circuits.csv`** | 77 | 9 | **38 active** | Circuit dimension: Country, location, coordinates, altitude. |
| **`qualifying.csv`** | 10,494 | 9 | **10,494** | Session qualifying times: Q1, Q2, Q3 and grid rank. |
| **`status.csv`** | 139 | 2 | **139** | Finish classification and mechanical/collision retirement codes. |
| **`pit_stops.csv`** | 11,371 | 7 | **11,371** | In-race pit stop transit times and stop counts (2011–2024). |

### 1.2 Pre-Race Observables vs. Post-Race Target Separation (Leakage Audit)

To guarantee mathematical validity, the pipeline strictly classifies every attribute before engineering features:

- **Pre-Race Inputs:** Starting Grid Position (`grid`), Qualifying Teammate Advantage, Driver Rolling Finish Average (last 5 races), Driver Rolling Points (last 5 races), Constructor Rolling Finish (last 10 entries), Circuit Historical Average Finish, Circuit Historical Win/Podium Rate, Driver Season Points before event, Career Starts, Career Win Rate, Career DNF Rate, Driver Age, Grid-vs-Form Expected Conversion Gap.
- **Post-Race Outcomes (Targets Only):** `target_is_win` (finish == 1), `target_is_podium` (finish <= 3), `target_is_points` (finish <= 10), `target_is_dnf` (unclassified retirement), `target_finish_position` (P1–P20).
- **Leakage Prevention:** Laps completed, in-race elapsed time, fastest lap speed, and race pit stop occurrences are completely excluded from pre-race feature calculation.

---

## 2. Feature Engineering & Pre-Race Feature Store

Features are computed using strict rolling origin accumulators sorted chronologically by race date (`date ASC, raceId ASC`). No future information from race $N$ is available when predicting race $N$:

```python
FEATURE_COLS = [
    "grid_position",                 # Official starting grid (1 to 20)
    "driver_rolling_finish_5",       # Driver mean finish in prior 5 races
    "driver_rolling_points_5",       # Driver mean points in prior 5 races
    "constructor_rolling_finish_10", # Team mean finish in prior 10 entries
    "constructor_rolling_points_10", # Team mean points in prior 10 entries
    "circuit_avg_finish",            # Driver's historical avg finish at this circuit
    "circuit_win_rate",              # Historical win rate at this circuit
    "circuit_podium_rate",           # Historical podium rate at this circuit
    "circuit_experience",            # Number of previous starts at this circuit
    "season_points_before",          # Championship points accumulated prior to race
    "career_starts",                 # Career Grand Prix starts prior to race
    "career_win_rate",               # Career win percentage prior to race
    "career_dnf_rate",               # Career retirement rate prior to race
    "ahead_of_teammate_grid",        # 1 if qualified ahead of teammate, else 0
    "driver_age",                    # Driver age in years at date of race
    "grid_vs_form_gap"               # Grid position minus rolling finish expectation
]
```

The feature store is saved as `F1_RACE_LAB_FEATURES_1994_2024.csv` and synchronized into the relational warehouse table `F1_RACE_LAB_FEATURES` (12,358 rows).

---

## 3. Model Training & Chronological Out-of-Time Validation

### 3.1 Validation Methodology

- **Training Era (1994–2021):** 10,999 driver entries across 509 Grands Prix. Spans V10, V8, and V6 Hybrid eras.
- **Out-of-Time Test Era (2022–2024):** 1,359 driver entries across 68 Grands Prix. Represents the contemporary Ground Effect aerodynamic regulations.

### 3.2 Target 1: Race Winner Classification (`is_win`)

Evaluated on 68 out-of-time test Grands Prix:

| Model | ROC-AUC | Top-1 Winner Hit Rate | Top-3 Podium Hit | Brier Score | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost Classifier (Champion)** | **0.9605** | **57.35% (39/68)** | **94.12% (64/68)** | **0.0289** | 0.4444 | 0.4706 | **0.4571** |
| **LightGBM Classifier** | 0.9600 | 52.94% (36/68) | 92.65% (63/68) | 0.0298 | 0.4286 | 0.4412 | 0.4348 |
| **Random Forest Classifier** | 0.9573 | 55.88% (38/68) | 91.18% (62/68) | 0.0303 | 0.4516 | 0.4118 | 0.4308 |
| **Logistic Regression (Grid Baseline)** | 0.9198 | 51.47% (35/68) | 88.24% (60/68) | 0.0345 | 0.3871 | 0.3529 | 0.3692 |

### 3.3 Target 2: Podium Finish Classification (`is_podium`)

- **Model:** XGBoost Classifier (`n_estimators=120, max_depth=4, lr=0.05`)
- **ROC-AUC:** `0.9379`
- **Accuracy:** `90.4%`
- **Precision:** `0.7226`
- **Recall:** `0.5980`
- **F1-Score:** `0.6544`

### 3.4 Target 3: Points Finish Classification (`is_points`, Top 10)

- **Model:** LightGBM Classifier (`n_estimators=120, max_depth=5, lr=0.05`)
- **ROC-AUC:** `0.8636`
- **Accuracy:** `79.0%`
- **F1-Score:** `0.7969`

### 3.5 Target 4: DNF / Retirement Risk Classification (`is_dnf`)

- **Model:** Gradient Boosting Classifier (`n_estimators=100, max_depth=3`)
- **ROC-AUC:** `0.5600`
- **Test DNF Prevalence:** `14.3%`

### 3.6 Target 5: Finishing Position Regression (`finish_position`, P1–P20)

| Regressor Model | MAE (Positions) | RMSE | $R^2$ Score | Rank Correlation |
| :--- | :---: | :---: | :---: | :---: |
| **Random Forest Regressor (Champion)** | **&plusmn;3.30** | **4.26** | **0.4548** | **0.762** |
| **Gradient Boosting Regressor** | &plusmn;3.48 | 4.45 | 0.4043 | 0.741 |
| **Ridge Baseline (Grid Position Only)** | &plusmn;3.62 | 4.55 | 0.3773 | 0.710 |

---

## 4. Feature Importance & Model Explainability

Top feature importance breakdown from the champion XGBoost Classifier:
1. **Starting Grid Position:** `61.17%`
2. **Career Win Rate:** `6.35%`
3. **Driver Rolling Finish Avg (Last 5):** `4.21%`
4. **Driver Rolling Points Avg (Last 5):** `2.61%`
5. **Career Grand Prix Starts:** `2.61%`
6. **Ahead of Teammate in Quali:** `2.59%`
7. **Constructor Rolling Points (Last 10):** `2.55%`
8. **Circuit Historical Podium Rate:** `2.47%`

---

## 5. The Interactive Race Lab (Implementation Details)

The interactive laboratory is live at **[http://localhost:8000/race-lab](http://localhost:8000/race-lab)** and provides five dedicated modules:

1. **Scenario Studio:** Counterfactual "What If" simulator. Modifies starting grid position, teammate battle, and recent form without altering historical records.
2. **Full Grid Predictions:** Ranks all 20 drivers with calibrated win probabilities summing to 100%.
3. **Driver & Team Comparison:** Head-to-head career and circuit statistics.
4. **2026 Remaining Season Forecaster:** Current date October 13, 2026. Pre-weekend provisional forecasts for Rounds 19–24 (USA, Mexico, Brazil, Las Vegas, Qatar, Abu Dhabi).
5. **Model Validation Suite:** Displays out-of-time chronological validation metrics.

---

## 6. Automated QA Test Suite Results

The automated test suite in [`test_race_lab_engine_qa.py`](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/test_race_lab_engine_qa.py) executed 8 tests:

```
test_01_dataset_row_counts_and_columns ... ok (12,358 entries, 577 races, 1994-2024)
test_02_zero_data_leakage .............. ok (Round 1 points == 0, strictly pre-race)
test_03_classification_models_trained .. ok (XGBoost Winner ROC-AUC > 0.90)
test_04_position_regressor_trained ..... ok (Random Forest MAE: 3.30 < Baseline 3.62)
test_05_prediction_pipeline_execution .. ok (20 drivers, calibrated sum == 100%)
test_06_scenario_simulation_functionality ok (P1 pole increases win prob over P4)
test_07_driver_comparison_logic ........ ok (Real head-to-head career stats)
test_08_2026_remaining_calendar ........ ok (6 upcoming 2026 championship rounds)
----------------------------------------------------------------------
Ran 8 tests in 2.602s

OK
```

---

## 7. Service Endpoints Reference

The FastAPI service exposes the following endpoints on port `8000`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/race-lab` | Serves the interactive Race Lab application interface. |
| `GET` | `/api/racelab/seasons-races` | Returns all 583 historical (1994–2024) and forecast (2026) events. |
| `GET` | `/api/racelab/race-grid?race_id={id}` | Returns 20 driver pre-race feature vectors for selected event. |
| `GET/POST`| `/api/racelab/predict` | Evaluates all 20 drivers using the specified model and target. |
| `GET/POST`| `/api/racelab/simulate` | Evaluates counterfactual scenario vectors and re-ranks the full 20-car simulated leaderboard in real time. |
| `GET` | `/api/racelab/explain` | Computes exact mathematical TreeSHAP feature attribution values for the target driver. |
| `GET` | `/api/racelab/compare-drivers` | Head-to-head comparison of two drivers at a circuit. |
| `GET` | `/api/racelab/compare-constructors` | Head-to-head comparison of team entries, wins, podiums, and reliability. |
| `GET` | `/api/racelab/constructors` | Returns all unique constructors for interactive filtering. |
| `GET` | `/api/racelab/historical-evidence` | Historical winners and podiums at a specific circuit. |
| `GET` | `/api/racelab/metrics` | Returns chronological out-of-time validation metrics. |

