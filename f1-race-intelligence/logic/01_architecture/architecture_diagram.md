# Architecture Diagram (System Pipeline Architecture)

```mermaid
flowchart TD
    subgraph DataIngestion [Historical Data & Preprocessing]
        D1["Historical Dataset (1994–2024 Ergast Universe)\n13,248 Driver Results | 598 Grands Prix"] --> D2["Data Validation & Sanity Audits\nMissing Values, Integrity Checks"]
        D2 --> D3["Chronological Sequencing & State Accumulation\nZero Data Leakage Sorting"]
    end

    subgraph FeatureEngineering [Pre-Race Feature Engineering]
        D3 --> F1["Feature Engineering Pipeline\n16 Pre-Race Features (Form, Experience, Grid)"]
        F1 --> F2["Rolling Driver Form (5-Race Decay)\nRolling Constructor Form (10-Entry Decay)"]
        F1 --> F3["Circuit History & Track Experience\nTeammate Grid Differential"]
    end

    subgraph TargetBranch [Class Labels & Target Generation]
        D3 --> L1["Label Generation Pipeline\nStrictly Post-Inference Targets"]
        L1 --> L2["target_is_win (P1 vs Rest - 1:19 Imbalance)\ntarget_is_podium (P1-P3) | target_is_points (P1-P10)"]
    end

    subgraph PatternMiningBranch [Pattern Matching Branch (Unsupervised)]
        F1 --> PM1["Transaction Discretizer\n(Grid Brackets, Team Tiers, Form Quintiles)"]
        PM1 --> PM2["Apriori Analysis\n(Candidate Generation)"]
        PM1 --> PM3["FP-Growth Analysis\n(FP-Tree Prefix Mining)"]
        PM2 --> PM4["Frequent Itemsets & Association Rules\n(Support, Confidence, Lift Benchmarks)"]
        PM3 --> PM4
    end

    subgraph ModelTraining [Supervised Classification Pipeline]
        F1 --> M1["Classification Engine\nXGBoost Champion + 7-Model Benchmark"]
        L2 --> M1
        M1 --> M2["Hyperparameter Tuning & Regularization\nscale_pos_weight = 19.5, Tree Pruning"]
        M1 --> M3["Chronological Validation Split\nTrain: 1994–2021 | Holdout Test: 2022–2024 (68 GPs)"]
    end

    subgraph Evaluation [Performance Evaluation]
        M3 --> E1["Performance Metrics Evaluation\nROC-AUC, PR-AUC, Confusion Matrix, Brier Score, Top-1 Hit Rate"]
        E1 --> E2["Model Artifact Serialization\nf1_race_lab_models.joblib"]
    end

    subgraph ServingLayer [Application & Serving Layer]
        E2 --> S1["FastAPI Backend Service\nrace_lab_service.py"]
        S1 --> S2["Interactive Frontend\nRace Lab UI (race_lab.html / Streamlit)"]
        S2 --> S3["User / Race Strategist\nWhat-If Scenarios & Calibrated Predictions"]
    end
```

## Data Flow Summary

1. **Historical Telemetry (1994–2024)**: Ingests 13,248 driver race classification results across 598 Grands Prix.
2. **Validation & Chronological State Accumulation**: Enforces strict chronological processing to prevent future look-ahead leakage.
3. **Pre-Race Feature Store**: Computes 16 pre-race features available strictly before green flag pit exit.
4. **Target Labels**: Generates binary targets (`target_is_win`, `target_is_podium`, `target_is_points`, `target_is_dnf`) used strictly as prediction targets.
5. **Pattern Mining Branch (Unsupervised)**: Runs Apriori and FP-Growth algorithms on discretized race transactions to identify co-occurrence rules.
6. **Classification & Validation Branch**: Trains and benchmarks 7 classifiers on 1994–2021 and evaluates on the 2022–2024 holdout test set (68 GPs).
7. **Serving & Applications**: Exposes predictions via FastAPI backend (`src/race_lab_service.py`) and browser frontend (`app/race_lab.html`).
