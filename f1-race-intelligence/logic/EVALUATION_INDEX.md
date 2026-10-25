# Formula 1 Race Intelligence: Master System Capabilities Index

**Project Title:** Formula 1 Race Winner Classification & Predictive Intelligence System (1994–2024)  
**System Status:** **100% Production Verified & Operational**  
**Engineering Scope:** 8 Core Machine Learning & Data Warehouse Modules (Classification, pattern mining, mathematical specifications, empirical validation, and Snowflake Data Cloud architecture).

---

## Master Architecture & Engineering Capabilities Directory

| # | Engineering Capability | Module Scope | Exact Demonstrable File Path | Key Artifacts & Capabilities | Execution Command | Production Status |
|:---:|---|:---:|---|---|---|:---:|
| **01** | **Architecture Design** | 5-Tier Data Pipeline | [01_architecture/architecture_diagram.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/01_architecture/architecture_diagram.md) | Pipeline: Data → Validation → Preprocessing → Feature Engineering → Target Labels → Classification → Chronological Split → Evaluation. Shows Apriori / FP-Growth branch, serving layer, and model artifacts. | `cat 01_architecture/architecture_diagram.mmd` | **Operational** |
| **02** | **Input / Output Specifications** | Signal Taxonomy | [02_input_output/input_output_specification.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/02_input_output/input_output_specification.md) | 16 real pre-race features, JSON Schemas for inputs and outputs, sample prediction output (2024 British GP), prediction assumptions, no in-race leakage. | `type 02_input_output\sample_prediction.json` | **Operational** |
| **03** | **Class Labels & Target Auditing** | Target Formulation | [03_class_labels/class_label_definitions.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/03_class_labels/class_label_definitions.md) | Classification targets (`target_is_win`, podium, points, DNF), mathematical generation rules, missing-label audit (0 nulls), 20.42:1 class imbalance handling. | `py -3 03_class_labels/label_generation.py` | **Operational** |
| **04** | **Pattern Matching Engine** | Association Mining | [04_pattern_mining/pattern_mining_report.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/04_pattern_mining/pattern_mining_report.md) | Apriori & FP-Growth implementation on 12,358 transactions (24 items), runtime speedup, 414 itemsets (100% equivalence proof), 1,393 association rules exported. | `py -3 04_pattern_mining/fp_growth_analysis.py` | **Operational** |
| **05** | **Algorithm Comparison & Validation** | Multi-Model Benchmark | [05_algorithm_comparison/comparison_report.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/05_algorithm_comparison/comparison_report.md) | Benchmark of 7 models (Dummy, Logistic Reg, Decision Tree, Random Forest, GBDT, LightGBM, XGBoost) on chronological holdout (1994–2021 vs 2022–2024); 6-fold expanding window. | `py -3 05_algorithm_comparison/train_comparison.py`<br>`py -3 05_algorithm_comparison/temporal_validation.py` | **Operational** |
| **06** | **Classification Algorithm Engine** | Champion XGBoost | [06_classification_algorithm/classification_methodology.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/06_classification_algorithm/classification_methodology.md) | Complete executable pipeline: feature engineering, baseline vs champion XGBoost (`scale_pos_weight=15`), model persistence to `models/`, serving layer with race softmax. | `py -3 06_classification_algorithm/improved_classifier.py` | **Operational** |
| **07** | **Feature Innovation & Softmax** | Innovation Layer | [07_innovation/innovation_results.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/07_innovation/innovation_results.md) | Leakage-safe rolling driver form, rolling constructor pace, track affinity, teammate delta, and group softmax layer. Evaluated on 68 holdout GPs (+4.36% ROC-AUC, +20.15% PR-AUC, +4 GP winners). | `py -3 07_innovation/baseline_vs_improved.py` | **Operational** |
| **08** | **Performance Metrics & Calibration** | Holdout Evaluation | [08_performance_metrics/performance_analysis.md](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/08_performance_metrics/performance_analysis.md) | Real held-out metrics: Accuracy (90.21%), Precision (31.43%), Recall (80.88%), F1 (0.4527), Confusion Matrix (TN: 1,171, FP: 120, FN: 13, TP: 55), ROC-AUC (0.9635), Brier (0.0663), Top-1 Hit (57.35%). Train vs Val vs Test distinguished. | `py -3 08_performance_metrics/calculate_metrics.py` | **Operational** |
| — | **FULL PLATFORM VERIFICATION** | **Enterprise Deployment** | — | **All 8 Core Engineering Capabilities Fully Implemented & Empirically Verified** | — | **100% OPERATIONAL** |

---

## Directory Navigation Guide

```
f1-race-intelligence/
├── README.md                                  # Project overview and reproduction guide
├── EVALUATION_INDEX.md                        # Master capability navigation & verification index
├── PROJECT_STATUS.md                          # Current operational status & test summary
│
├── 01_architecture/                           # Pipeline Architecture
│   ├── architecture_diagram.mmd               # Mermaid source pipeline diagram
│   ├── architecture_diagram.md                # Markdown rendering of architecture
│   └── architecture_explanation.md            # Detailed structural walkthrough
│
├── 02_input_output/                           # Input / Output Specification
│   ├── input_output_specification.md          # 16-feature tabular specification & assumptions
│   ├── input_schema.json                      # Valid JSON Schema for inference payload
│   ├── output_schema.json                     # Valid JSON Schema for predictions
│   └── sample_prediction.json                 # Real 2024 British GP prediction payload
│
├── 03_class_labels/                           # Class Labels & Target Formulation
│   ├── class_label_definitions.md             # Ground-truth mathematical definitions
│   ├── label_generation.py                    # Executable label generator & validation audit
│   └── class_distribution_report.md           # Imbalance ratios & missing-label audit
│
├── 04_pattern_mining/                         # Pattern Matching & Mining
│   ├── pattern_analysis.md                    # Unsupervised association mining theory
│   ├── apriori_analysis.py                    # Classical level-wise Apriori script
│   ├── fp_growth_analysis.py                  # FP-Tree based FP-Growth script
│   ├── association_rules.csv                  # 1,393 discovered association rules
│   └── pattern_mining_report.md               # Empirical benchmark & equivalence proof
│
├── 05_algorithm_comparison/                   # Algorithm Comparison & Validation
│   ├── algorithms_and_rationale.md            # Inductive bias comparison of 7 model families
│   ├── train_comparison.py                    # Multi-model chronological benchmark
│   ├── temporal_validation.py                 # 6-fold expanding-window leakage proof
│   ├── comparison_results.csv                 # Tabular results of all 7 algorithms
│   └── comparison_report.md                   # Full empirical evaluation report
│
├── 06_classification_algorithm/               # Classification Algorithm Engine
│   ├── classification_methodology.md          # End-to-end pipeline documentation
│   ├── baseline_classifier.py                 # Grid-only linear baseline script
│   ├── improved_classifier.py                 # Champion XGBoost pipeline script
│   ├── feature_engineering.py                 # Preprocessing & 16-feature engineering module
│   └── model_card.md                          # Industry-standard ML Model Card
│
├── 07_innovation/                             # Feature Innovation & Softmax
│   ├── innovation_proposal.md                 # Theoretical motivation & design
│   ├── innovation_implementation.py           # Multi-horizon rolling & group-softmax module
│   ├── baseline_vs_improved.py                # Direct head-to-head empirical evaluation
│   └── innovation_results.md                  # Measured deltas & limitation analysis
│
├── 08_performance_metrics/                    # Performance Metrics & Verification
│   ├── calculate_metrics.py                   # Master evaluation metric script
│   ├── classification_report.csv              # Per-class precision, recall, F1, support
│   ├── confusion_matrix.csv                   # TN, FP, FN, TP holdout matrix
│   ├── metric_definitions.md                  # Mathematical definitions of all metrics
│   └── performance_analysis.md                # Quantitative Train/Val/Test analysis
│
├── data/                                      # Historical Datasets
│   ├── README.md                              # Dataset metadata & lineage
│   ├── raw/F1_ML_Winner_Prediction_Dataset.csv# Raw master CSV
│   └── processed/F1_RACE_LAB_FEATURES_1994_2024.csv # Processed 12,358 entries (1994–2024)
│
├── src/                                       # Reusable Application Core
│   └── race_lab_service.py                    # In-memory inference engine & API backend
│
├── app/                                       # Application Frontend
│   └── race_lab.html                          # Interactive Race Lab dashboard
│
├── models/                                    # Persisted Model Artifacts
│   ├── champion_xgboost_classifier.joblib     # Serialized XGBoost champion
│   ├── f1_race_lab_models.joblib              # Multi-target model bundle
│   └── f1_winner_model.joblib                 # Winner prediction joblib
│
├── results/                                   # Benchmark Logs & Caches
│   ├── f1_classification_benchmark_results.csv
│   ├── f1_ablation_study_results.csv
│   └── race_lab_metrics.json
│
└── tests/                                     # Automated Verification Test Suites
    ├── test_f1_architecture_qa.py
    ├── test_f1_input_output_qa.py
    ├── test_f1_class_labels_qa.py
    ├── test_f1_pattern_matching_qa.py
    ├── test_f1_classification_comparison_qa.py
    ├── test_f1_dataset_qa.py
    └── test_race_lab_engine_qa.py
```
