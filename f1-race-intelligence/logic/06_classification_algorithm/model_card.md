# Model Card: Formula 1 Race Winner Classifier (Champion XGBoost)

## Model Details
- **Model Name:** F1 Champion Race Winner Classifier (`champion_xgboost_classifier`)
- **Version:** 2.4.0 (2026 Release)
- **Architecture:** Extreme Gradient Boosted Trees (`xgboost.XGBClassifier`)
- **Trained By:** F1 Race Intelligence Engineering
- **Release Date:** October 2026
- **Artifact Path:** `models/champion_xgboost_classifier.joblib`
- **License:** Open Research / Motorsport Analytics

## Intended Use
- **Primary Intended Use:** Predict the probability of each entrant winning a Formula 1 Grand Prix prior to lights-out, using exclusively pre-race qualifying, historical form, and constructor indicators.
- **Primary Users:** Motorsport race engineers, telemetry analysts, predictive modeling researchers.
- **Out-of-Scope Use Cases:** In-race live betting with real-time telemetry inputs (e.g., pit stop lap triggers, safety car flags, crash telemetry), which represent in-race leakage if used pre-race.

## Training Data
- **Corpus:** 10,999 driver-race observations across 509 FIA Formula 1 Grands Prix spanning seasons 1994 to 2021.
- **Target Distribution:** 509 positive winner instances (4.63%), 10,490 negative instances (95.37%).
- **Regulatory Eras Covered:** 3.5L/3.0L Naturally Aspirated V10 (1994–2005), 2.4L V8 (2006–2013), 1.6L V6 Turbo-Hybrid (2014–2021).

## Out-of-Sample Evaluation Data
- **Corpus:** 1,359 driver-race entries across 68 Grands Prix spanning seasons 2022 to 2024.
- **Condition:** Ground-Effect Aerodynamic Regulations era (completely unseen during model training).
- **Temporal Invariant:** Strictly verified $\max(T_{\text{train}}) = 2021 < \min(T_{\text{test}}) = 2022$.

## Quantitative Performance Metrics (Test Set 2022–2024)

| Metric | Measured Value | Standard Error / Notes |
|---|---|---|
| **ROC-AUC** | **0.9635** | Evaluated on out-of-sample holdout |
| **PR-AUC (Avg Precision)** | **0.6009** | Baseline random guess PR-AUC = 0.0500 |
| **Overall Accuracy** | **90.21%** | Binary classification at default threshold |
| **Winner Class Recall** | **80.88%** | 55 of 68 actual race winners identified |
| **Top-1 Winner Hit Rate** | **57.35% (39/68)** | True winner had highest probability on grid |
| **Top-3 Podium Hit Rate** | **88.24% (60/68)** | True winner in top-3 highest probabilities |
| **Brier Calibration Score** | **0.0663** | Well-calibrated probabilistic output |
| **Inference Latency** | **5.64 ms** | Per full 20-car grid evaluation |

## Factors & Feature Importance
The top five influential features driving model decisions:
1. `grid_position` (38.14% relative gain)
2. `driver_rolling_finish_5` (10.60% relative gain)
3. `constructor_rolling_finish_10` (7.23% relative gain)
4. `career_win_rate` (6.12% relative gain)
5. `driver_rolling_points_5` (5.60% relative gain)

## Caveats and Recommendations
1. **Grid Position Dominance:** Grid position remains the single strongest feature. If qualifying is held in extreme rain or anomalous weather, qualitative review should be exercised.
2. **Team Reliability Shocks:** First-lap collisions or unforeseen power unit electrical failures cannot be anticipated prior to race start.
