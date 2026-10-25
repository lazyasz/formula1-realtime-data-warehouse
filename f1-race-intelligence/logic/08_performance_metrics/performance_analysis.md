# 08. Comprehensive Performance Analysis Report

## 1. Experimental Overview & Partitioning

The production classification pipeline was evaluated across four chronologically segmented partitions to ensure zero look-ahead leakage and robust generalization across regulatory eras:

1. **Training Partition (1994–2021):** 10,999 driver-race entries (509 Grands Prix). Encompasses 28 consecutive seasons across naturally aspirated, V8, and V6 turbo-hybrid engine specifications.
2. **Validation Partition (2022):** 440 driver-race entries (22 Grands Prix). Represents the revolutionary introduction of Ground-Effect aerodynamic regulations.
3. **Test Partition (2023–2024):** 919 driver-race entries (46 Grands Prix). Strict out-of-sample holdout featuring extreme dominance (Red Bull RB19 in 2023) followed by high competitive volatility (7 distinct winners in 2024).
4. **Combined Holdout (2022–2024):** 1,359 driver-race entries (68 Grands Prix).

---

## 2. Partition-Level Metric Comparison

Below are the empirical metrics recorded from executing [calculate_metrics.py](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/08_performance_metrics/calculate_metrics.py):

| Evaluation Partition | ROC-AUC | PR-AUC | Overall Accuracy | Winner Recall | Winner F1 | Log Loss | Brier Score | Top-1 Race Hit % (GPs) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Training (1994–2021)** | 0.9733 | 0.6139 | 91.25% | 0.9371 | 0.4979 | 0.2003 | 0.0626 | 58.7% (299/509) |
| **Validation (2022)** | 0.9581 | 0.5313 | 89.55% | 0.8182 | 0.4390 | 0.2230 | 0.0702 | 50.0% (11/22) |
| **Test (2023–2024)** | 0.9659 | 0.6307 | 90.53% | 0.8043 | 0.4596 | 0.2102 | 0.0645 | 60.9% (28/46) |
| **Combined Holdout (2022–2024)** | **0.9635** | **0.6009** | **90.21%** | **0.8088** | **0.4527** | **0.2143** | **0.0663** | **57.4% (39/68)** |

---

## 3. Holdout Per-Class Performance Breakdown

From [classification_report.csv](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/08_performance_metrics/classification_report.csv), evaluated across 1,359 entries in the 2022–2024 test period:

| Class Entity | Precision | Recall | F1-Score | Support (Entries) | Class Meaning |
|---|---:|---:|---:|---:|---|
| **Non-Winner (Class 0)** | 0.9890 | 0.9071 | 0.9463 | 1,291 | Drivers finishing P2 through P20 or DNF |
| **Winner (Class 1)** | 0.3143 | **0.8088** | **0.4527** | 68 | Official race winner (exactly 1 per GP) |
| **Macro Average** | 0.6517 | 0.8579 | 0.6995 | 1,359 | Unweighted arithmetic mean across classes |
| **Weighted Average** | 0.9552 | 0.9021 | 0.9216 | 1,359 | Prevalence-weighted metrics |

### Interpretation of Trade-Off:
- **Winner Recall of 80.88% (55/68):** The cost-sensitive parameter (`scale_pos_weight=15`) successfully prioritizes capturing actual race winners. Out of 68 unseen Grands Prix, the model captured 55 true winners within its positive probability threshold.
- **Winner Precision of 31.43% (55/175):** Because the model predicts probabilities for all 20 drivers on the grid, multiple contenders in close machinery (e.g. Red Bull and Ferrari in 2022, or McLaren and Mercedes in 2024) cross the threshold. When passed to the race-level softmax layer, the single driver with the highest probability is declared the predicted winner, yielding a **57.4% Top-1 exact hit rate**.

---

## 4. Confusion Matrix Analysis

From [confusion_matrix.csv](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/08_performance_metrics/confusion_matrix.csv):

| | Predicted Non-Winner (0) | Predicted Winner (1) | Total Actual |
|---|---:|---:|---:|
| **Actual Non-Winner (0)** | **1,171 (TN)** | 120 (FP) | 1,291 |
| **Actual Winner (1)** | 13 (FN) | **55 (TP)** | 68 |
| **Total Predicted** | 1,184 | 175 | 1,359 |

- **True Negatives ($TN = 1,171$):** High specificity ($90.7\%$), cleanly eliminating backmarkers and midfield teams from contention.
- **False Positives ($FP = 120$):** Drivers running in top machinery who qualified well but did not win (e.g. pole-sitters suffering high degradation or tactical undercuts).
- **False Negatives ($FN = 13$):** Occurred primarily in chaotic wet weather or mechanical retirement scenarios (e.g., Singapore 2022, Brazil 2024).
- **True Positives ($TP = 55$):** Demonstrates that over 4 out of every 5 race winners were successfully prioritized by the model.

---

## 5. Temporal Generalization Stability

A critical observation is the absence of catastrophic model degradation between the training era (1994–2021) and the modern era (2022–2024):
- Training ROC-AUC: $0.9733 \rightarrow$ Test ROC-AUC: $0.9659$ ($\Delta = -0.0074$, less than $0.8\%$ drop).
- Training Brier Score: $0.0626 \rightarrow$ Test Brier Score: $0.0645$ ($\Delta = +0.0019$, extremely well calibrated).
- Top-1 Winner Hit Rate actually **increased** from $58.7\%$ on historical data to **$60.9\%$** on 2023–2024, demonstrating that the multi-horizon rolling features successfully adapted to the ground-effect regulatory shift without overfitting to past engine eras.
