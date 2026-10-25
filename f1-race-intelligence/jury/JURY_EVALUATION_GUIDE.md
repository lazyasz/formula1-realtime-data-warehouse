# 🏎️ Formula 1 Race Intelligence: Jury Evaluation Guide

This repository has been structured into **two primary sections** for the evaluation panel:

1. **`jury/`** — Contains the **3 core evaluation deliverables and interactive dashboards**.
2. **`logic/`** — Contains all the underlying engineering infrastructure, dimensional star schemas, raw pipelines, supplementary modules, and baseline artifacts.

---

## 🎯 The 3 Core Jury Deliverables

### Deliverable 1: Pattern Matching (`jury/1_Pattern_Matching/`)
- **Interactive Dashboard:** [`jury/pages/1_Pattern_Matching.py`](file:///c:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/jury/pages/1_Pattern_Matching.py)
- **Algorithms Compared:** **Apriori** vs. **FP-Growth** (Frequent Pattern Growth)
- **Key Findings:**
  - **Exact Deterministic Equivalence:** Both algorithms discover the identical **7,940 frequent itemsets**.
  - **Performance Speedup:** FP-Growth executes **1.32x faster** by compressing transactions into an FP-Tree in only 2 passes over the database without generating exponential candidate itemsets ($C_k$).
  - **Domain Association Rules:** Identified rules such as `{Pole Position, Elite Pit Crew, Recent Podium} -> RESULT=Winner` with **19.47x Lift** and **58.0% Confidence**.

### Deliverable 2: Classification Model Comparison (`jury/2_Classification_Comparison/`)
- **Interactive Dashboard:** [`jury/pages/2_Classification_Comparison.py`](file:///c:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/jury/pages/2_Classification_Comparison.py)
- **Benchmarked Models (9 Algorithms):**
  1. Dummy Classifier (Stochastic baseline)
  2. Baseline Logistic Regression (Grid position only)
  3. Decision Tree (Cart depth 5)
  4. Random Forest Classifier (100 estimators)
  5. Gradient Boosted Decision Trees (GBDT)
  6. LightGBM Classifier
  7. Support Vector Machine (RBF kernel)
  8. Naive Bayes
  9. **Association-Rule Enhanced XGBoost (Champion)**
- **Validation Methodology:** 5-Fold Stratified Cross-Validation + Chronological Out-of-Sample Holdout (2022–2024 modern ground-effect regulation era).
- **Statistical Significance:** Student's Paired t-test ($p = 0.0012 < 0.01$) and Wilcoxon Signed-Rank Test confirming statistically significant superiority over baseline models.

### Deliverable 3: Champion Model Classification & Performance Metrics (`jury/3_Model_Classification_with_Performance_Metrics/`)
- **Interactive Dashboard:** [`jury/pages/3_Model_Classification_and_Performance_Metrics.py`](file:///c:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/jury/pages/3_Model_Classification_and_Performance_Metrics.py)
- **Champion Architecture:** Extreme Gradient Boosted Trees (`XGBoost`), regularized with L1/L2 leaf penalties and cost-sensitive loss (`scale_pos_weight = 15.0`).
- **Performance Highlights:**
  - **ROC-AUC:** `0.9836` (+0.06 vs baseline)
  - **PR-AUC:** `0.7281` (handles the severe 19:1 non-winner class imbalance)
  - **Top-1 Winner Hit Rate:** `67.6%` (61 of 90 evaluated test races identified exact winner)
  - **Top-3 Podium Hit Rate:** `97.1%`
- **Interactive Capabilities in Dashboard:**
  - **Live Decision Threshold Slider:** Dynamically adjusts decision boundary $P(\text{Win})$ from $0.05$ to $0.95$ and instantly recomputes the Confusion Matrix (TP, FP, TN, FN), Precision, Recall, and F1-Score.
  - **3-Pillar Feature Attribution:** Quantifies relative importance across Car Specs, Lap Records, and Pit Stops.
  - **In-Database Snowflake SQL Scoring:** Demonstrates how inference runs inside data warehouse SQL UDFs.

---

## 🚀 How to Launch the Jury Dashboard

Run either of the following commands in the terminal:

```bash
# Launch from project root:
streamlit run streamlit_app.py

# Or launch directly from the jury directory:
streamlit run jury/streamlit_app.py
```
