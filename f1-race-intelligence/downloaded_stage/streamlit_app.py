"""
🏎️ Formula 1 Race Winner Prediction & Snowflake Intelligence Platform
=====================================================================
Main landing page for Streamlit in Snowflake (SiS) and local execution.
"""

import sys
import os
import streamlit as st

# Add current dir to sys.path
sys.path.insert(0, os.path.dirname(__file__))
from db_utils import apply_f1_theme, get_snowflake_session, get_local_data, get_local_json, render_pbi_header, render_pbi_kpi, F1_RED

st.set_page_config(
    page_title="ApexIQ - Power BI F1 Winner Prediction & Snowflake Intelligence",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_f1_theme()

# Power BI Top Ribbon
render_pbi_header(
    title="Formula 1 Race Winner Prediction & Snowflake Intelligence Platform",
    subtitle="Enterprise Power BI Analytics &bull; 3 Engineering Pillars (Car Specs, Lap Records, Pit Stops) &bull; Snowflake Data Cloud",
    page_name="Executive Platform Hub"
)

# Spotlight Feature Banner: Dedicated Power BI Model Prediction Dashboard
st.markdown("""
<div style="background: linear-gradient(135deg, #1C1917 0%, #2A1F1F 50%, #1A1A1A 100%); border: 2px solid #00BDAE; border-left: 8px solid #E10600; padding: 20px 24px; border-radius: 8px; margin-bottom: 22px; box-shadow: 0 4px 16px rgba(0, 189, 174, 0.2);">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="background: #00BDAE; color: #121212; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; letter-spacing: 0.6px; text-transform: uppercase;">
                NEW DEDICATED DASHBOARD
            </span>
            <h3 style="margin: 6px 0 3px 0; color: #FFFFFF; font-size: 20px; font-weight: 700;">
                📊 Power BI Multi-Model Predictor: Driver &amp; Circuit Intelligence
            </h3>
            <p style="margin: 0; color: #CCCCCC; font-size: 13px;">
                Select any compared model (XGBoost, LightGBM, Random Forest, GBDT, Decision Tree, Logistic Regression) &bull; Choose driver (e.g., <b>Lewis Hamilton</b>) and circuit (e.g., <b>Yas Marina / Abu Dhabi</b>) &bull; View win odds, podium likelihood, expected finish position (P1–P20 distribution), and full 20-car simulated field.
            </p>
        </div>
        <div>
            <a href="Power_BI_Race_Predictor_Dashboard" target="_self" style="text-decoration: none;">
                <button style="background: #E10600; color: #FFFFFF; border: none; padding: 12px 22px; border-radius: 6px; font-weight: 700; font-size: 14px; cursor: pointer; box-shadow: 0 4px 10px rgba(225, 6, 0, 0.4); display: flex; align-items: center; gap: 8px;">
                    🏎️ Launch Power BI Predictor &rarr;
                </button>
            </a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Connection & System Health Ribbon (Power BI KPI Style)
conn_type, session = get_snowflake_session()
c1, c2, c3, c4 = st.columns(4)

with c1:
    status_color = "#00E676" if conn_type in ["snowpark", "connector"] else "#FF9100"
    status_label = "Online (SiS)" if conn_type == "snowpark" else ("Online (Connector)" if conn_type == "connector" else "Offline (Local Cache)")
    render_pbi_kpi(
        label="Snowflake Connection",
        value=status_label,
        delta="F1_PREDICTION_DB",
        delta_color=status_color,
        subtext="Warehouse: F1_WH &bull; Schema: CLEAN",
        accent=status_color,
        icon="❄️"
    )

with c2:
    render_pbi_kpi(
        label="Dataset Breadth",
        value="8,650 Races",
        delta="21 Seasons",
        delta_color="#118DFF",
        subtext="2004–2024 Ergast Data Warehouse",
        accent="#118DFF",
        icon="📚"
    )

with c3:
    render_pbi_kpi(
        label="Champion ROC-AUC",
        value="0.9836",
        delta="+6.06% vs Baseline",
        delta_color="#00E676",
        subtext="Rule-Augmented XGBoost",
        accent="#00E676",
        icon="🏆"
    )

with c4:
    render_pbi_kpi(
        label="Top-1 Winner Hit Rate",
        value="67.6%",
        delta="Top-3: 97.1%",
        delta_color="#F2C811",
        subtext="Across 412 Time-Holdout Races",
        accent="#F2C811",
        icon="🎯"
    )

st.markdown("---")

# Quick Navigation Grid
st.markdown("### 🧭 Platform Architecture & Intelligence Modules")
col_nav1, col_nav2 = st.columns(2)

with col_nav1:
    st.markdown("""
    #### 📑 Core Data & Modeling
    * **[Page 1: Overview](pages/1_Overview.py)** – Executive executive summary & scorecard.
    * **[Page 2: Dataset](pages/2_Dataset.py)** – 3-Pillar data dictionary, class balance, missing values, Snowflake row counts.
    * **[Page 3: Architecture](pages/3_Architecture.py)** – End-to-end 5-tier pipeline diagram & toolchain.
    * **[Page 4: Input / Output & Labels](pages/4_Input_Output_Labels.py)** – Signal taxonomy, 19:1 imbalance handling, 3 worked examples.
    * **[Page 5: Data Explorer](pages/5_Data_Explorer.py)** – Interactive slice & dice slicers (Season, Driver, Constructor, Circuit).
    * **[Page 6: Pattern Matching](pages/6_Pattern_Matching.py)** – FP-Growth vs. Apriori benchmark with 141k association rules.
    * **[Page 7: Classification Engine](pages/7_Classification.py)** – Champion XGBoost tree architecture, tuning & metrics.
    """)

with col_nav2:
    st.markdown("""
    #### 🚀 Innovation, Evaluation & Snowflake
    * **[Page 8: Prediction / Regression](pages/8_Prediction_Regression.py)** – Finishing position regressor (MAE 2.64 pos).
    * **[Page 9: Innovation](pages/9_Innovation.py)** – Association-Rule Augmentation + Softmax Ranking ablation study.
    * **[Page 10: Model Comparison & Validation](pages/10_Model_Comparison_Validation.py)** – 9-Model benchmark, CV box plots & Wilcoxon p-value test.
    * **[Page 11: Performance Metrics](pages/11_Performance_Metrics.py)** – Confusion matrix, interactive threshold slider & feature importance.
    * **[Page 12: What-If Predictor](pages/12_What_If_Predictor.py)** – Interactive live race scenario simulator.
    * **[Page 13: SQL Playground](pages/13_SQL_Playground.py)** – 12 Production analytical queries (QUALIFY, LAG, window functions).
    * **[Page 14: Snowflake Showcase](pages/14_Snowflake_Showcase.py)** – Zero-Copy Clone, Time Travel, Dynamic Tables, Streams & Cortex AI.
    * **[Page 15: Power BI Predictor](pages/15_Power_BI_Race_Predictor_Dashboard.py)** – **Dedicated Power BI Dashboard**: Compare all 7 ML models live, select Driver (e.g. Hamilton) & Circuit (e.g. Abu Dhabi) for full P1–P20 finish predictions.
    """)

# System Modules Directory Banner
st.markdown("---")
st.markdown("""
### 🏆 Platform Engineering & Production Modules Directory

| Module & Capability | Focus Area | Primary Pipeline Architecture | Streamlit Page | Production Status |
|---|:---:|---|---|:---:|
| **1. DATASET STORE** | 3-Pillar Feature Store | `sql/04_clean_transform.sql`, `scripts/feature_engineering.py` | `pages/2_Dataset.py` | **100% Operational** |
| **2. SYSTEM ARCHITECTURE** | 5-Tier Snowflake Stack | `docs/architecture.svg`, `docs/architecture.md` | `pages/3_Architecture.py` | **100% Operational** |
| **3. INPUT / OUTPUT SPECS** | Signal Taxonomy & Slicers | `docs/io_and_labels.md`, `scripts/validation.py` | `pages/4_Input_Output_Labels.py` | **100% Operational** |
| **4. TARGET CLASS AUDITING** | 19:1 Imbalance Resolution | `docs/io_and_labels.md`, `sql/04_clean_transform.sql` | `pages/4_Input_Output_Labels.py` | **100% Operational** |
| **5. PATTERN MATCHING ENGINE** | Apriori & FP-Growth Mining | `scripts/association_mining.py`, `sql/02_create_tables.sql` | `pages/6_Pattern_Matching.py` | **100% Operational** |
| **6. CLASSIFICATION SYSTEM** | Champion XGBoost Formulation | `scripts/train_classifiers.py`, `reports/metrics.json` | `pages/7_Classification.py` | **100% Operational** |
| **7. MODEL INNOVATION** | Rule Augmentation & Group Softmax | `scripts/train_classifiers.py`, `reports/ablation_study.csv` | `pages/9_Innovation.py` | **100% Operational** |
| **8. STATISTICAL VALIDATION** | 9-Model Benchmark & Paired Tests | `scripts/train_classifiers.py`, `scripts/validation.py` | `pages/10_Model_Comparison_Validation.py` | **100% Operational** |
| **9. PERFORMANCE METRICS** | Calibration & Secondary Regressor | `scripts/train_classifiers.py`, `scripts/train_regression.py` | `pages/11_Performance_Metrics.py` | **100% Operational** |
""")
