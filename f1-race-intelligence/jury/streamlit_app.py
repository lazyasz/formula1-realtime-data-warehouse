"""
🏎️ Formula 1 Race Winner Intelligence — Official Jury Evaluation Portal
========================================================================
Interactive Evaluation Suite for Panel Evaluation & Assessment.
Focused exclusively on the 3 core required deliverables:
1. Pattern Matching (FP-Growth vs. Apriori Association Rules)
2. Classification Model Comparison (9 Algorithms, 5-Fold Stratified CV, Holdout Validation)
3. Champion Classification Model with Performance Metrics Suite & Threshold Calibration
"""

import sys
import os
import streamlit as st

# Path resolution for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(__file__))

from db_utils import (
    apply_f1_theme,
    get_snowflake_session,
    render_pbi_header,
    render_pbi_kpi,
    F1_RED
)

try:
    st.set_page_config(
        page_title="F1 Race Intelligence — Jury Evaluation Portal",
        page_icon="🏎️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception:
    pass

apply_f1_theme()

render_pbi_header(
    title="Formula 1 Race Intelligence — Official Jury Evaluation Portal",
    subtitle="3 Core Academic & Engineering Deliverables &bull; Snowflake Cloud DW &bull; 1994–2024 Motorsport Telemetry",
    page_name="Jury Executive Hub"
)

# Executive Welcome Banner for Jury Panel
st.markdown("""
<div style="background: linear-gradient(135deg, #161B22 0%, #21262D 50%, #161B22 100%); border: 2px solid #E10600; border-left: 8px solid #E10600; padding: 20px 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(225, 6, 0, 0.25);">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="background: #E10600; color: #FFFFFF; padding: 3px 10px; border-radius: 4px; font-weight: 800; font-size: 11px; letter-spacing: 0.8px; text-transform: uppercase;">
                ACADEMIC &amp; TECHNICAL EVALUATION
            </span>
            <h3 style="margin: 8px 0 4px 0; color: #FFFFFF; font-size: 22px; font-weight: 700;">
                Welcome, Evaluation Jury &amp; Reviewers
            </h3>
            <p style="margin: 0; color: #C9D1D9; font-size: 14px; max-width: 900px;">
                This project implements an enterprise-grade Formula 1 predictive data warehouse and machine learning platform. The workspace has been streamlined specifically for review into <b>3 core deliverables</b>:
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid #00E676; padding: 6px 14px; border-radius: 16px; font-weight: 700; font-size: 12px;">
                ● All 3 Deliverables Operational
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# System KPIs Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_pbi_kpi("1. Pattern Discovery", "7,940 Sets", "141,763 Rules", "#00BDAE", "FP-Growth vs. Apriori", "#00BDAE", "🧩")
with c2:
    render_pbi_kpi("2. Benchmark Models", "9 Algorithms", "5-Fold CV + Holdout", "#118DFF", "Decision Trees to XGBoost", "#118DFF", "📊")
with c3:
    render_pbi_kpi("3. Champion ROC-AUC", "0.9836", "+6.06% vs Baseline", "#00E676", "Rule-Augmented XGBoost", "#00E676", "🏆")
with c4:
    render_pbi_kpi("Top-1 Winner Hit", "67.6%", "Top-3: 97.1%", "#F2C811", "Exact Winner Identification", "#F2C811", "🥇")

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

# The 3 Core Deliverable Feature Cards
st.markdown("### 🎯 Explore the 3 Jury Deliverable Dashboards:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card" style="border-left: 4px solid #00BDAE; min-height: 280px;">
        <span style="background: rgba(0, 189, 174, 0.2); color: #00BDAE; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 800;">
            DELIVERABLE 1
        </span>
        <h4 style="margin: 10px 0 6px 0; color: #FFFFFF;">🧩 Pattern Matching Engine</h4>
        <p style="color: #8B949E; font-size: 13px; line-height: 1.5;">
            <b>Association Rule Mining on Race Transactions:</b><br>
            &bull; Direct speed and memory benchmark of <b>FP-Growth vs. Apriori</b>.<br>
            &bull; Mathematical verification of exact itemset equivalence (7,940 sets).<br>
            &bull; Discovered rules targeting <code>RESULT=Winner</code> (e.g. Pole + Sub-2.5s Pit Stop &rarr; 19.47x Lift).<br>
            &bull; Interactive support, confidence, and lift slicers.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Open Pattern Matching Dashboard", key="btn_d1", use_container_width=True):
        st.switch_page("pages/1_Pattern_Matching.py")

with col2:
    st.markdown("""
    <div class="metric-card" style="border-left: 4px solid #118DFF; min-height: 280px;">
        <span style="background: rgba(17, 141, 255, 0.2); color: #118DFF; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 800;">
            DELIVERABLE 2
        </span>
        <h4 style="margin: 10px 0 6px 0; color: #FFFFFF;">📊 Classification Model Comparison</h4>
        <p style="color: #8B949E; font-size: 13px; line-height: 1.5;">
            <b>Comprehensive Multi-Model Benchmarking:</b><br>
            &bull; Benchmarks 9 classification algorithms (Logistic Regression, Decision Trees, Random Forest, GBDT, LightGBM, XGBoost, etc.).<br>
            &bull; 5-Fold Stratified Cross-Validation + Chronological 2022–2024 Holdout.<br>
            &bull; Rigorous hypothesis testing (Student's Paired t-test and Wilcoxon signed-rank test).<br>
            &bull; Multi-metric sorting by ROC-AUC, PR-AUC, F1, and Top-1 Hit Rate.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Open Model Comparison Dashboard", key="btn_d2", use_container_width=True):
        st.switch_page("pages/2_Classification_Comparison.py")

with col3:
    st.markdown("""
    <div class="metric-card" style="border-left: 4px solid #E10600; min-height: 280px;">
        <span style="background: rgba(225, 6, 0, 0.2); color: #FF7B7B; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 800;">
            DELIVERABLE 3
        </span>
        <h4 style="margin: 10px 0 6px 0; color: #FFFFFF;">🏆 Model &amp; Performance Metrics</h4>
        <p style="color: #8B949E; font-size: 13px; line-height: 1.5;">
            <b>Champion XGBoost with Live Metric Suite:</b><br>
            &bull; Mathematics, 2nd-order Hessian gradients, and decision tree logic.<br>
            &bull; <b>Interactive Decision Threshold Slider</b> with live Confusion Matrix recomputation.<br>
            &bull; Precision-Recall curves built for extreme 19:1 winner class imbalance.<br>
            &bull; 3-Pillar Feature Attribution (Car Specs, Lap Records, Pit Stops).<br>
            &bull; Production Snowflake SQL UDF in-database inference simulation.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Open Champion Model & Metrics", key="btn_d3", use_container_width=True):
        st.switch_page("pages/3_Model_Classification_and_Performance_Metrics.py")

st.markdown("---")
st.markdown("""
<div style="color: #8B949E; font-size: 12px; text-align: center;">
    <b>Folder Organization Note:</b> All primary deliverables and dashboards are organized under <code>/jury</code>. All underlying architecture diagrams, dimensional star schemas, raw pipelines, and supplementary materials are preserved in <code>/logic</code>.
</div>
""", unsafe_allow_html=True)
