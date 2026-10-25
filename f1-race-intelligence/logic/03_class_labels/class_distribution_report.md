# Class Distribution & Imbalance Report

## 1. Quantitative Class Distribution Across 1994–2024 Universe

The historical dataset encompasses **12,358 driver classification records** across **577 Formula 1 Grands Prix** (1994 to 2024):

| Target Label | Positive Class (1) | Negative Class (0) | Total Records | Positive Prevalence (%) | Imbalance Ratio (Neg : Pos) | Missing Values |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`target_is_win`** | **577** | **11,781** | **12,358** | **4.67%** | **20.42 : 1** | **0 (0.0%)** |
| **`target_is_podium`** | **1,731** | **10,627** | **12,358** | **14.01%** | **6.14 : 1** | **0 (0.0%)** |
| **`target_is_points`** | **5,770** | **6,588** | **12,358** | **46.69%** | **1.14 : 1** | **0 (0.0%)** |
| **`target_is_dnf`** | **3,467** | **8,891** | **12,358** | **28.05%** | **2.56 : 1** | **0 (0.0%)** |

## 2. Winner Exclusivity Verification

* Every single Grand Prix out of 577 races contains **exactly 1 winner** ($\sum_{i=1}^{M_j} \text{target\_is\_win}_i = 1$).
* No races contain 0 winners or dual winners.

## 3. Analysis of Class Imbalance Challenge

1. **The 20:1 Winner Imbalance:**
   * In a 20-car grid, only 1 driver wins, making winning a rare event (4.67%).
   * A trivial, uninformative "all negative" dummy classifier achieves **95.33% raw accuracy** while having **0% precision, 0% recall, and F1-score of 0.00**.
   * Consequently, accuracy alone is a misleading metric for F1 winner classification.

2. **Engineering Solutions Implemented:**
   * **Asymmetric Hessian Scaling:** In XGBoost, we set `scale_pos_weight = 19.5` to invert the empirical imbalance odds ratio, penalizing false negatives proportionally.
   * **Stratified Chronological Splitting:** Training partitions preserve exact race-by-race balance.
   * **Precision-Recall Optimization:** Models are evaluated using PR-AUC and Brier Score, which explicitly penalize poorly calibrated probability distributions.
   * **Race-Level Softmax Normalization:** Re-normalizes predictions across the starting grid so that exactly one winner is picked per Grand Prix.
