# 🏎️ Formula 1 Race Intelligence — Power BI Dashboard Blueprint & Implementation Guide

This guide accompanies the **Power BI Master Package** generated directly from the Formula 1 Data Warehouse and Machine Learning engine. It enables you or your colleague to build an enterprise-grade, high-octane Microsoft Power BI dashboard in minutes.

---

## 📦 What Is In The Shareable Package

1. **`F1_Race_Intelligence_PowerBI_Dataset.xlsx`** (2.37 MB)
   * A consolidated, multi-sheet workbook designed for instant 1-click import into Power BI Desktop.
   * Contains **12 pre-structured, clean tables**:
     * `Fact_Grand_Prix_Predictions` — 8,650 driver starts (2004–2024) with all 3 engineering pillars, actual outcomes, predicted win probabilities, predicted finish slots, and hit flags.
     * `Dim_Drivers` — 108 drivers with career stats, win rates, and podium percentages.
     * `Dim_Circuits` — 38 global circuits with track records and pit loss penalties.
     * `Dim_Constructors` — 35 teams with historical entries, wins, and pace ratings.
     * `Dim_Races` — 412 distinct Formula 1 Grands Prix calendar records.
     * `ML_Model_Benchmark` — 9 evaluated classification algorithms with ROC-AUC, PR-AUC, F1, Accuracy, and Top-1/Top-3 hit rates.
     * `ML_ROC_Curves` — Exact False Positive Rate (FPR) vs True Positive Rate (TPR) coordinates for plotting overlaid ROC curves.
     * `ML_Association_Rules` — Top association rules with Support, Confidence, Lift factor, and classified Target Outcomes.
     * `ML_Frequent_Itemsets` — Discovered frequent itemsets and lengths.
     * `ML_Feature_Importance` — 31 features grouped by the 3 Engineering Pillars.
     * `Executive_KPI_Summary` — High-level platform scorecards.
     * `DAX_Measures_Reference` — Pre-written DAX formulas.

2. **`F1_PowerBI_Theme.json`**
   * Custom dark racing theme with official Formula 1 color tokens:
     * **F1 Red:** `#E10600`
     * **Telemetry Cyan / Teal:** `#00BDAE`
     * **Podium Gold:** `#F2C811`
     * **Sector Green:** `#00E676`
     * **Speed Blue:** `#118DFF`
     * **Dark Carbon Background:** `#0B0D10` / `#1C1C1C` / `#242424`

---

## 🚀 3-Minute Quickstart in Power BI Desktop

### Step 1: Import the Data
1. Open **Power BI Desktop**.
2. Click **`Home`** $\rightarrow$ **`Get Data`** $\rightarrow$ **`Excel workbook`**.
3. Select **`F1_Race_Intelligence_PowerBI_Dataset.xlsx`**.
4. Check all 12 tables and click **`Load`**.

### Step 2: Apply the Racing Dark Theme
1. In the top ribbon, click **`View`** $\rightarrow$ click the **`Themes`** dropdown $\rightarrow$ **`Browse for themes`**.
2. Select **`F1_PowerBI_Theme.json`**.
   > *Instantly, all charts, cards, backgrounds, fonts, and palettes will convert into an authentic dark racing aesthetic!*

### Step 3: Verify Data Model Relationships (Star Schema)
In the **Model View** (left sidebar, 3rd icon), ensure these 1-to-many relationships exist (Power BI auto-detects most of them):
* `Dim_Drivers[driver_name]` $\rightarrow$ `Fact_Grand_Prix_Predictions[driver_name]`
* `Dim_Circuits[circuit_name]` $\rightarrow$ `Fact_Grand_Prix_Predictions[circuit_name]`
* `Dim_Constructors[constructor_name]` $\rightarrow$ `Fact_Grand_Prix_Predictions[constructor_name]`
* `Dim_Races[race_id]` $\rightarrow$ `Fact_Grand_Prix_Predictions[race_id]`

---

## 🖥️ 3-Page Dashboard Blueprint & Visual Layout

---

### Page 1: 🏆 Champion Race Predictor & Telemetry Studio
* **Objective:** Explain **Single Model Classification** and live race outcome forecasting.
* **Top Slicers Panel:**
  * **Season Slicer:** Slider (`2004` to `2024`, default `2024`).
  * **Driver Slicer:** Dropdown (`Lewis Hamilton`, `Max Verstappen`, `Lando Norris`, etc.).
  * **Circuit Slicer:** Dropdown (`Silverstone`, `Monaco`, `Spa`, `Yas Marina`, etc.).
  * **Grid Position Slicer:** Number slider (`1` to `20`).
* **KPI Scorecards (Row 1):**
  * `🏆 Predicted Win Probability` $\rightarrow$ `[Avg Win Probability] * 100` (e.g. `68.5%`).
  * `🥉 Podium Likelihood` $\rightarrow$ `AVERAGE(Fact[predicted_podium_prob]) * 100` (e.g. `92.4%`).
  * `🏁 Expected Finish Position` $\rightarrow$ `ROUND(AVERAGE(Fact[predicted_finish_slot]), 0)` (e.g. `P1`).
  * `📜 Track Record Win Rate` $\rightarrow$ `Dim_Drivers[win_rate_pct]` (e.g. `31.2%`).
* **Core Visuals (Row 2 & 3):**
  * **Win Probability Gauge:** Value: `[Avg Win Probability]`, Target: `0.05` (5% uniform field baseline).
  * **Feature Impact Waterfall / Bar Chart:** 
    * Y-axis: Factors (Starting Grid, Constructor Pace, Lap Record Delta, Pit Crew Efficiency).
    * X-axis: Impact Value (Positive in Green `#00E676`, Negative in Red `#E10600`).
  * **Full 20-Car Grid Simulated Leaderboard (Table visual):**
    * Columns: `driver_name`, `constructor_name`, `grid_position`, `predicted_win_prob` (Data Bar), `predicted_finish_slot`, `confidence_tier`.

---

### Page 2: 📊 Classification Comparison of Models & Validation
* **Objective:** Benchmark **all 9 machine learning algorithms** and show statistical validation proofs.
* **Top Slicers Panel:**
  * **Category Slicer:** Multiselect (`Proposed Innovation`, `Gradient Boosted Trees`, `Bagging Ensemble`, `Linear Baseline`, `Neural Network`).
  * **Sort Metric Slicer:** Radio button (`Test ROC-AUC`, `PR-AUC`, `Top-1 Hit Rate`).
* **KPI Scorecards (Row 1):**
  * `Top Benchmark ROC-AUC` $\rightarrow$ `0.9635` (*Champion XGBoost*).
  * `Peak PR-AUC (19:1 Imbalance)` $\rightarrow$ `0.6009` (*+50.4% vs Baseline*).
  * `Top-1 Winner Hit Rate` $\rightarrow$ `57.35%` (*39 / 68 Test GPs*).
  * `Hypothesis Significance` $\rightarrow$ `p = 0.0012` (*Paired t-test t = -8.20, Reject H0*).
* **Core Visuals:**
  * **Overlaid Receiver Operating Characteristic (ROC) Curves (Line Chart):**
    * Data Source: `ML_ROC_Curves` table.
    * X-axis: `False_Positive_Rate`.
    * Y-axis: `True_Positive_Rate`.
    * Legend: `Model_Name`.
    * *Shows champion XGBoost bowing highest toward top-left corner compared to baselines.*
  * **Model Comparison Benchmark Matrix (Matrix visual):**
    * Rows: `model_name`.
    * Values: `test_roc_auc`, `test_pr_auc`, `test_f1`, `test_accuracy_pct`, `top1_winner_hit_pct`, `top3_podium_hit_pct`.
    * Conditional formatting: Data bars or heatmaps on ROC-AUC and Top-1 Hit %.
  * **Grouped Bar Chart (Precision vs Recall vs F1 vs PR-AUC):**
    * X-axis: `model_name`.
    * Y-axis: `test_precision`, `test_recall`, `test_f1`, `test_pr_auc`.

---

### Page 3: 🧩 Pattern Mining Engine & Association Rules
* **Objective:** Explain **Unsupervised Association Rule Mining** (FP-Growth vs Apriori).
* **Top Slicers Panel:**
  * **Target Outcome Slicer:** `target_outcome` (`Race Winner (P1)`, `Podium Finish (P1-P3)`, `Points Finisher`, `DNF / Out`).
  * **Minimum Lift Slider:** `lift` slider (`1.0` to `20.0`, default `3.0`).
  * **Minimum Confidence Slider:** `confidence` slider (`0.20` to `0.90`).
* **KPI Scorecards (Row 1):**
  * `Total Discovered Itemsets` $\rightarrow$ `7,940 Sets` (*100% Identical in both algos*).
  * `Total Discovered Rules` $\rightarrow$ `1,393 Rules` (*Confidence >= 0.50*).
  * `FP-Growth Speedup` $\rightarrow$ `1.32x Faster` (*No candidate generation*).
  * `Peak Rule Lift` $\rightarrow$ `19.47x Lift` (*Pole + Elite Pit Stop $\rightarrow$ Winner*).
* **Core Visuals:**
  * **Top Association Rules by Lift (Clustered Bar Chart):**
    * Y-axis: `antecedents`.
    * X-axis: `lift`.
    * Color: `confidence`.
  * **Rule Distribution Scatter Plot (Scatter chart):**
    * X-axis: `support`.
    * Y-axis: `confidence`.
    * Size: `lift`.
    * Legend / Color: `target_outcome`.
  * **Algorithm Execution Benchmark (Bar chart):**
    * Category: `Algorithm` (`Apriori` vs `FP-Growth`).
    * Value: Execution time in seconds (`0.70s` vs `0.53s`).
    * Callout note: *"FP-Tree compression reduces database scans to exactly 2 passes."*

---

## 🧮 Ready-To-Copy DAX Measures

Create a new table called `_Measures` in Power BI Desktop and paste these formulas:

```dax
// 1. Total Evaluated Driver Starts
Total Driver Starts = COUNTROWS('Fact_Grand_Prix_Predictions')

// 2. Total Formula 1 Grands Prix Evaluated
Total Grands Prix = DISTINCTCOUNT('Fact_Grand_Prix_Predictions'[race_id])

// 3. Ground-Truth Winners
Total Race Winners = 
CALCULATE(
    COUNTROWS('Fact_Grand_Prix_Predictions'), 
    'Fact_Grand_Prix_Predictions'[is_win] = 1
)

// 4. Model Top-1 Winner Accuracy %
Top 1 Winner Hit Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS('Fact_Grand_Prix_Predictions'), 'Fact_Grand_Prix_Predictions'[is_winner_hit] = 1), 
    [Total Grands Prix], 
    0
) * 100

// 5. Model Top-3 Podium Hit Rate %
Top 3 Podium Hit Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS('Fact_Grand_Prix_Predictions'), 'Fact_Grand_Prix_Predictions'[is_podium_hit] = 1), 
    [Total Grands Prix] * 3, 
    0
) * 100

// 6. Starting Pole-to-Win Conversion Rate %
Pole to Win % = 
DIVIDE(
    CALCULATE(COUNTROWS('Fact_Grand_Prix_Predictions'), 'Fact_Grand_Prix_Predictions'[grid_position] = 1, 'Fact_Grand_Prix_Predictions'[is_win] = 1), 
    CALCULATE(COUNTROWS('Fact_Grand_Prix_Predictions'), 'Fact_Grand_Prix_Predictions'[grid_position] = 1), 
    0
) * 100

// 7. Slicer-Responsive Calculated Win Probability
Avg Win Probability = AVERAGE('Fact_Grand_Prix_Predictions'[predicted_win_prob])

// 8. Expected vs Actual Finish Position Gap (MAE)
Finishing Position MAE = AVERAGEA(ABS('Fact_Grand_Prix_Predictions'[finish_position_gap]))
```

---

## 🏁 How to Share with Your Friend

Simply share these two files with your colleague:
1. **`F1_Race_Intelligence_PowerBI_Dataset.xlsx`**
2. **`F1_PowerBI_Theme.json`**

They can open Power BI Desktop, import the Excel workbook, apply the theme JSON file, and have the exact visual dashboards live in under 5 minutes!
