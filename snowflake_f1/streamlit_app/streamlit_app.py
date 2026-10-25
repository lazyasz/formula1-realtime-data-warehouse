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
from db_utils import apply_f1_theme, get_snowflake_session, get_local_data, get_local_json, F1_RED

st.set_page_config(
    page_title="ApexIQ - F1 Winner Prediction on Snowflake",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_f1_theme()

# Header Banner
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #161B22 0%, #0D1117 100%); border-left: 6px solid {F1_RED}; padding: 24px 30px; border-radius: 10px; margin-bottom: 25px;">
        <h1 style="color: #FFFFFF; margin: 0; font-size: 32px; font-weight: 800; letter-spacing: 1px;">
            🏎️ FORMULA 1 RACE WINNER PREDICTION PLATFORM
        </h1>
        <p style="color: #8B949E; margin: 8px 0 0 0; font-size: 16px;">
            Powered by <b>Snowflake Data Cloud</b> &amp; <b>Streamlit in Snowflake (SiS)</b> | 3 Core Pillars: Car Features, Lap Records, Pit Stops
        </p>
    </div>
""", unsafe_allow_html=True)

# Connection & System Health Ribbon
conn_type, session = get_snowflake_session()
c1, c2, c3, c4 = st.columns(4)

with c1:
    status_color = "#00E676" if conn_type in ["snowpark", "connector"] else "#FF9100"
    status_label = "Online (Snowpark SiS)" if conn_type == "snowpark" else ("Online (Connector)" if conn_type == "connector" else "Offline (Local Cache)")
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Snowflake Connection</div>
            <div class="metric-value" style="color: {status_color}; font-size: 20px;">● {status_label}</div>
            <div class="metric-delta">Target: F1_PREDICTION_DB</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Dataset Breadth</div>
            <div class="metric-value">8,650 Races</div>
            <div class="metric-delta">21 Seasons (2004–2024)</div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Champion ROC-AUC</div>
            <div class="metric-value" style="color: #00E676;">0.9836</div>
            <div class="metric-delta">+6.06% vs Baseline</div>
        </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Top-1 Winner Hit Rate</div>
            <div class="metric-value" style="color: #00E5FF;">67.6%</div>
            <div class="metric-delta">Top-3 Podium Hit: 97.1%</div>
        </div>
    """, unsafe_allow_html=True)

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
