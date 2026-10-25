# Architecture Explanation & System Walkthrough

## 1. End-to-End Pipeline Architecture

The system implements a production-grade machine learning and pattern mining architecture designed specifically for sports analytics where temporal ordering and informational boundaries are critical.

```
Historical Dataset (1994–2024)
   │
   ├──> Data Ingestion & Validation (Missing values, referential integrity)
   │       │
   │       └──> Chronological Sorting (Zero-leakage temporal state)
   │               │
   │               ├──> Pre-Race Feature Engineering (16 signals available before start)
   │               │       │
   │               │       ├──> Supervised Classification Pipeline
   │               │       │       ├── Training (1994–2021)
   │               │       │       ├── Chronological Validation Split
   │               │       │       └── Out-of-Time Holdout Evaluation (2022–2024: 68 GPs)
   │               │       │
   │               │       └──> Pattern Mining Branch (Unsupervised)
   │               │               ├── Transaction Discretization
   │               │               ├── Apriori Candidate Generation
   │               │               └── FP-Growth Prefix Tree Mining
   │               │
   │               └──> Target Label Generation (is_win, is_podium, is_points, is_dnf)
   │
   └──> Serving & Inference Layer
           ├── Model Serialization (f1_race_lab_models.joblib)
           ├── REST & Scenario API (race_lab_service.py)
           └── User Interface (Race Lab UI / Streamlit)
```

## 2. Detailed Pipeline Stages

### Stage 1: Historical Dataset & Validation
* **Raw Universe:** 1994 to 2024 FIA Formula 1 World Championship (31 seasons, 598 Championship Grands Prix, 13,248 driver entries).
* **Validation Layer:** Enforces integrity checks ensuring zero missing values in primary key identifiers (`race_id`, `driver_id`, `constructor_id`, `circuit_id`).
* **Chronological Sequencing:** Processes every race strictly in historical order $(t_1 < t_2 < \dots < t_N)$.

### Stage 2: Leakage-Safe Feature Engineering
* All features are computed strictly using information available **prior to the green flag** of that specific race:
  * Rolling 5-race driver performance metrics only incorporate races $t-1, t-2, \dots, t-5$.
  * Season points before race are set to exactly `0.0` for Round 1 of every season.
  * Circuit experience and track win rates strictly count starts prior to the current event.
* Feature sets never touch post-race duration, lap count, points scored in the current race, or race status.

### Stage 3: Class Label Formulation
* Targets are computed post-race for supervised training:
  * `target_is_win`: 1 if final classified position is P1, 0 otherwise (5.0% prevalence).
  * `target_is_podium`: 1 if finished P1–P3, 0 otherwise (15.0% prevalence).
  * `target_is_points`: 1 if finished in top 10 scoring positions, 0 otherwise.
  * `target_is_dnf`: 1 if retired due to collision or mechanical failure, 0 otherwise.

### Stage 4: Unsupervised Pattern Mining Branch
* Completely decoupled from supervised model training to prevent methodological confusion:
  * Discretizes starting grid, team tier, driver form, and pit speed into categorical transaction tokens.
  * Runs both Apriori (level-wise candidate generation) and FP-Growth (compact FP-Tree structure).
  * Generates association rules evaluated by Support, Confidence, and Lift.

### Stage 5: Chronological Model Validation & Serving
* **Out-of-Time Testing:** Prevents temporal look-ahead bias by training strictly on 1994–2021 (earlier regulation eras) and evaluating on the 2022–2024 Ground Effect Era (68 unseen Grands Prix).
* **Champion Model:** Extreme Gradient Boosting (XGBoost) with asymmetric cost scaling (`scale_pos_weight = 19.5`) to counter the 1:19 class imbalance.
* **Serving:** Serialized as `models/f1_race_lab_models.joblib`, queried via `src/race_lab_service.py` to deliver real-time What-If scenario simulations.
