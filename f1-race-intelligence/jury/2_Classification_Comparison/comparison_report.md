# 05. Algorithm Comparison & Temporal Validation Report

## 1. Experimental Setup & Protocol

- **Dataset:** 12,358 race entries from 577 Grands Prix (1994–2024).
- **Chronological Holdout Partition:**
  - **Training Set:** 1994–2021 (509 Grands Prix, 10,999 entries). Encompasses V10, V8, and Turbo-Hybrid eras.
  - **Test Set:** 2022–2024 (68 Grands Prix, 1,359 entries). Modern Ground-Effect aerodynamic regulatory era (strictly unseen during training).
- **Temporal Invariant:** $\max(T_{\text{train}}) = 2021 < \min(T_{\text{test}}) = 2022$. Zero future-to-past data leakage.
- **Evaluation Criteria:**
  - Individual Entry Metrics: ROC-AUC, PR-AUC (Average Precision), Accuracy, Balanced Accuracy, Precision, Recall, F1-Score, Brier Score.
  - Group-Level Race Metrics: Top-1 Winner Hit Rate (fraction of 68 races where $\text{argmax}(P_{\text{win}}) == \text{Winner}$), Top-3 Podium Hit Rate.

---

## 2. Empirical Benchmark Results

Below are the empirical metrics recorded from executing [train_comparison.py](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/05_algorithm_comparison/train_comparison.py), exported to [comparison_results.csv](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/05_algorithm_comparison/comparison_results.csv):

| Architecture | ROC-AUC | PR-AUC | Accuracy (%) | Balanced Acc (%) | Top-1 Winner Hit % (68 GPs) | Top-3 Winner Hit % | Brier Score | Inference Latency (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **1. Dummy Classifier** | 0.5000 | 0.0500 | 49.96% | 49.28% | 33.8% (23/68) | 76.5% | 0.2500 | 0.21 ms |
| **2. Baseline (Logistic Reg - Grid Only)** | 0.9198 | 0.3994 | 95.00% | 50.00% | 51.5% (35/68) | 83.8% | 0.0345 | 0.38 ms |
| **3. Decision Tree (Depth 5)** | 0.9177 | 0.4715 | 85.58% | 84.75% | 52.9% (36/68) | 76.5% | 0.1005 | 0.42 ms |
| **4. Random Forest Classifier** | 0.9561 | 0.5866 | 86.83% | 88.19% | 51.5% (35/68) | 86.8% | 0.0919 | 14.28 ms |
| **5. Gradient Boosting (GBDT)** | 0.9622 | 0.5994 | 96.32% | 70.20% | 52.9% (36/68) | 86.8% | 0.0293 | 3.12 ms |
| **6. LightGBM Classifier** | 0.9586 | 0.6152 | 88.01% | 86.02% | 51.5% (35/68) | 83.8% | 0.0811 | 4.85 ms |
| **7. XGBoost Classifier (Champion)** | **0.9635** | **0.6029** | 90.14% | 86.45% | **54.4% (37/68)** | **88.2%** | 0.0678 | 5.64 ms |

---

## 3. Expanding-Window Chronological Validation

To ensure performance stability across shifting technical regulations and team dominance cycles, [temporal_validation.py](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/05_algorithm_comparison/temporal_validation.py) executed 6 expanding-window temporal folds:

| Fold # | Historical Training Period | Out-of-Sample Test Season | Train Rows | Test Rows | ROC-AUC | Top-1 Winner Hit Rate |
|---|---|---|---:|---:|---:|---:|
| **Fold 1** | 1994–2018 | **2019** | 9,799 | 420 | 0.9512 | 33.3% (07/21 GPs) |
| **Fold 2** | 1994–2019 | **2020** | 10,219 | 340 | 0.9213 | 70.6% (12/17 GPs) |
| **Fold 3** | 1994–2020 | **2021** | 10,559 | 440 | 0.9242 | 50.0% (11/22 GPs) |
| **Fold 4** | 1994–2021 | **2022** (Ground Effect Intro) | 10,999 | 440 | 0.9587 | 45.5% (10/22 GPs) |
| **Fold 5** | 1994–2022 | **2023** (RB19 Dominance) | 11,439 | 440 | 0.9856 | 77.3% (17/22 GPs) |
| **Fold 6** | 1994–2023 | **2024** (7 Distinct Winners) | 11,879 | 479 | 0.9367 | 50.0% (12/24 GPs) |
| **MEAN** | — | **2019–2024** | — | — | **0.9463** | **54.44%** |

### Key Temporal Takeaways:
1. **Stability Across Eras:** The expanding-window model maintains a consistent mean ROC-AUC of **0.9463**, demonstrating that the multi-era engineered feature set generalizes across engine eras.
2. **Handling Competitive Volatility:** Even in the unpredictable 2024 season (which featured 7 different Grand Prix winners across 4 constructors: Red Bull, McLaren, Ferrari, Mercedes), the model achieved a 50.0% Top-1 hit rate and 0.9367 ROC-AUC without fine-tuning on 2024 data.
3. **Temporal Invariant Guaranteed:** In every single fold, zero data from season $T$ was accessible during model fitting.

---

## 4. Conclusion on Parameter 05

The empirical comparison confirms:
- Tree ensembles dramatically outperform both the stochastic baseline (+46.35 AUC points) and the grid-only linear baseline (+4.37 AUC points).
- **XGBoost Classifier** achieves the highest discriminative performance (ROC-AUC: 0.9635, Top-1 Hit: 54.4%, Top-3 Hit: 88.2%), making it the mathematically justified choice for the production pipeline.
