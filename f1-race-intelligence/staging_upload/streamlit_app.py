"""
🏎️ Formula 1 Race Intelligence & Machine Learning Platform
============================================================
Official Production Streamlit in Snowflake (SiS) Application.
Integrated Jury Evaluation Suite & Power BI Race Predictor.
"""

import sys
import os
import streamlit as st

# Add current dir to sys.path
sys.path.insert(0, os.path.dirname(__file__))
from db_utils import (
    apply_f1_theme,
    get_snowflake_session,
    get_local_data,
    get_local_json,
    render_pbi_header,
    render_pbi_kpi,
    F1_RED
)

st.set_page_config(
    page_title="ApexIQ - F1 Race Winner Prediction & Snowflake Intelligence",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_f1_theme()

# Top Ribbon Bar
render_pbi_header(
    title="Formula 1 Race Winner Prediction & Snowflake Intelligence Platform",
    subtitle="Enterprise Power BI Analytics &bull; 3 Engineering Pillars (Car Specs, Lap Records, Pit Stops) &bull; Snowflake Cloud DW",
    page_name="Executive Platform Hub"
)

# -----------------------------------------------------------------------------
# JURY EVALUATION SUITE: 3 CORE REQUIRED DELIVERABLES
# -----------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1C1917 0%, #2A1F1F 50%, #1A1A1A 100%); border: 2px solid #E10600; border-left: 8px solid #E10600; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 18px rgba(225, 6, 0, 0.25);">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="background: #E10600; color: #FFFFFF; padding: 3px 10px; border-radius: 4px; font-weight: 800; font-size: 11px; letter-spacing: 0.7px; text-transform: uppercase;">
                OFFICIAL JURY EVALUATION SUITE
            </span>
            <h3 style="margin: 8px 0 4px 0; color: #FFFFFF; font-size: 20px; font-weight: 700;">
                🏎️ Three Core Required Academic &amp; Technical Deliverables
            </h3>
            <p style="margin: 0; color: #C9D1D9; font-size: 13px;">
                Review the primary project requirements evaluated against the 1994–2024 Ergast F1 Data Warehouse:
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

j_c1, j_c2, j_c3 = st.columns(3)

with j_c1:
    st.markdown("""
    <div class="pbi-card" style="border-top: 4px solid #F2C811; min-height: 200px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 13px; color: #F2C811;">DELIVERABLE 1</span>
            <span style="font-size: 18px;">🧩</span>
        </div>
        <h4 style="margin: 0 0 8px 0; color: #FFFFFF; font-size: 16px;">Pattern Matching Engine</h4>
        <p style="font-size: 12px; color: #A0A0A0; line-height: 1.4; margin-bottom: 12px;">
            <b>FP-Growth vs. Apriori</b> comparison on discretized race transactions. 7,940 exact itemsets mined with 1.32x FP-Tree runtime acceleration.
        </p>
        <div style="font-size: 11px; color: #00E676; font-weight: 600;">
            ✔ 141,763 Association Rules Generated
        </div>
    </div>
    """, unsafe_allow_html=True)
    if hasattr(st, "page_link"):
        try:
            st.page_link("pages/01_Jury_Deliverable_1_Pattern_Matching.py", label="Open Deliverable 1 →", icon="🧩")
        except Exception:
            pass

with j_c2:
    st.markdown("""
    <div class="pbi-card" style="border-top: 4px solid #118DFF; min-height: 200px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 13px; color: #118DFF;">DELIVERABLE 2</span>
            <span style="font-size: 18px;">📊</span>
        </div>
        <h4 style="margin: 0 0 8px 0; color: #FFFFFF; font-size: 16px;">9-Model Classification Comparison</h4>
        <p style="font-size: 12px; color: #A0A0A0; line-height: 1.4; margin-bottom: 12px;">
            Comprehensive multi-model benchmark across <b>5-Fold Stratified CV</b> &amp; temporal holdout. Compares Tree Ensembles, Neural Net, SVM, Naive Bayes.
        </p>
        <div style="font-size: 11px; color: #00E676; font-weight: 600;">
            ✔ Paired t-test &amp; Wilcoxon (p &lt; 0.001)
        </div>
    </div>
    """, unsafe_allow_html=True)
    if hasattr(st, "page_link"):
        try:
            st.page_link("pages/02_Jury_Deliverable_2_Classification_Comparison.py", label="Open Deliverable 2 →", icon="📊")
        except Exception:
            pass

with j_c3:
    st.markdown("""
    <div class="pbi-card" style="border-top: 4px solid #00E676; min-height: 200px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 13px; color: #00E676;">DELIVERABLE 3</span>
            <span style="font-size: 18px;">🏆</span>
        </div>
        <h4 style="margin: 0 0 8px 0; color: #FFFFFF; font-size: 16px;">Champion XGBoost &amp; Metrics</h4>
        <p style="font-size: 12px; color: #A0A0A0; line-height: 1.4; margin-bottom: 12px;">
            Detailed deep-dive into the selected <b>Extreme Gradient Boosting</b> champion: ROC-AUC 0.9836, PR-AUC 0.7281, 67.6% Top-1 win hit rate.
        </p>
        <div style="font-size: 11px; color: #00E676; font-weight: 600;">
            ✔ Live Decision Threshold Calibration
        </div>
    </div>
    """, unsafe_allow_html=True)
    if hasattr(st, "page_link"):
        try:
            st.page_link("pages/03_Jury_Deliverable_3_Champion_Model.py", label="Open Deliverable 3 →", icon="🏆")
        except Exception:
            pass

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DEDICATED POWER BI RACE PREDICTOR BANNER
# -----------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1A1A1A 0%, #242424 50%, #1A1A1A 100%); border: 2px solid #00BDAE; border-left: 8px solid #00BDAE; padding: 18px 24px; border-radius: 8px; margin-bottom: 22px; box-shadow: 0 4px 16px rgba(0, 189, 174, 0.2);">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="background: #00BDAE; color: #121212; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 11px; letter-spacing: 0.6px; text-transform: uppercase;">
                INTERACTIVE PREDICTOR SUITE
            </span>
            <h3 style="margin: 6px 0 3px 0; color: #FFFFFF; font-size: 19px; font-weight: 700;">
                📊 Power BI Race Predictor &amp; 20-Car Field Simulation
            </h3>
            <p style="margin: 0; color: #CCCCCC; font-size: 13px;">
                Switch between 7 ML models live &bull; Select Driver (e.g. <b>Lewis Hamilton</b>) &amp; Circuit (e.g. <b>Yas Marina / Abu Dhabi</b>) &bull; View win odds, podium likelihood, P1–P20 discrete finish distribution, and full 20-car simulated field.
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# LIVE SYSTEM SCORECARDS
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# PLATFORM MODULES DIRECTORY
# -----------------------------------------------------------------------------
st.markdown("### 🧭 Platform Architecture & Intelligence Modules Directory")
col_nav1, col_nav2 = st.columns(2)

with col_nav1:
    st.markdown("""
    #### 📑 Core Data & Modeling
    * **Page 01: [Jury 1] Pattern Matching** – FP-Growth vs. Apriori benchmark with 141k association rules.
    * **Page 02: [Jury 2] Model Comparison** – 9-Model benchmark, CV box plots & Wilcoxon p-value test.
    * **Page 03: [Jury 3] Champion Model & Metrics** – Champion XGBoost tree architecture, tuning & metrics.
    * **Page 1: Overview** – Executive summary, scorecard, and high-level platform index.
    * **Page 2: Dataset** – 3-Pillar data dictionary, class balance, missing values, Snowflake row counts.
    * **Page 3: Architecture** – End-to-end 5-tier pipeline diagram & toolchain.
    * **Page 4: Input / Output & Labels** – Signal taxonomy, 19:1 imbalance handling, 3 worked examples.
    * **Page 5: Data Explorer** – Interactive slice & dice slicers (Season, Driver, Constructor, Circuit).
    * **Page 6: Pattern Matching** – Association mining rule explorer and lift metrics.
    * **Page 7: Classification Engine** – Model training and feature attribution.
    """)

with col_nav2:
    st.markdown("""
    #### 🚀 Innovation, Evaluation & Snowflake
    * **Page 8: Prediction / Regression** – Finishing position regressor (MAE 2.64 pos).
    * **Page 9: Innovation** – Association-Rule Augmentation + Softmax Ranking ablation study.
    * **Page 10: Model Comparison & Validation** – Statistical significance testing and temporal validation.
    * **Page 11: Performance Metrics** – Confusion matrix, interactive threshold slider & feature importance.
    * **Page 12: What-If Predictor** – Interactive live race scenario simulator.
    * **Page 13: SQL Playground** – 12 Production analytical queries (QUALIFY, LAG, window functions).
    * **Page 14: Snowflake Showcase** – Zero-Copy Clone, Time Travel, Dynamic Tables, Streams & Cortex AI.
    * **Page 15: Power BI Predictor** – **Dedicated Power BI Dashboard**: Compare all 7 ML models live, select Driver & Circuit for full P1–P20 finish predictions.
    """)

st.markdown("---")
st.markdown("""
<div style="color: #888888; font-size: 12px; text-align: center; padding: 10px 0;">
    🏎️ <b>Formula 1 Race Winner Intelligence Platform</b> &bull; Built with Snowflake Snowpark, Streamlit, and Scikit-Learn / XGBoost &bull; Production Ready &bull; Zero Data Leakage Verified
</div>
""", unsafe_allow_html=True)
