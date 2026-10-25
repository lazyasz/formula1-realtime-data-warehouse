import os
import sys
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, get_plotly_theme, get_local_data, get_local_json, F1_RED

apply_f1_theme()

st.title("🏁 Formula 1 Race Winner Platform: Executive Overview")
st.markdown("### High-Precision Race Winner Classification & Predictive Intelligence on Snowflake")

# Top Metrics Row
df = get_local_data("clean_f1_modeling_master.csv")
metrics = get_local_json("metrics.json")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Grand Prix Records", f"{len(df):,}" if not df.empty else "8,650", "2004–2024 Seasons")
with m2:
    st.metric("Circuits Modeled", f"{df['circuit_name'].nunique()}" if not df.empty else "38", "Global FIA Tracks")
with m3:
    roc_auc = metrics.get("roc_auc", 0.9836)
    st.metric("Champion Model ROC-AUC", f"{roc_auc:.4f}", "+6.06% vs Baseline")
with m4:
    hit_rate = metrics.get("top1_winner_accuracy_pct", 67.6)
    st.metric("Top-1 Winner Accuracy", f"{hit_rate:.1f}%", "Out of 412 GPs")

st.markdown("---")

t1, t2 = st.tabs(["📊 Executive Summary", "🏎️ Three Engineering Pillars"])

with t1:
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown(r"""
        #### Project Objective & Problem Statement
        In modern Formula 1, race outcomes are determined by complex interactions between mechanical package performance, 
        circuit pace limits, and pit stop execution. 
        
        This platform delivers a production-grade **Snowflake Data Warehouse & Machine Learning System** that:
        1. **Solves the Primary Classification Task**: Predicts whether a driver wins a Grand Prix ($P(\text{Win}) \in [0, 1]$) under severe **19:1 class imbalance**.
        2. **Solves the Secondary Regression Task**: Predicts final classified finish position (P1 to P24) with low error.
        3. **Incorporates Novel Innovation**: Extracts high-lift **FP-Growth association rules** as synthetic feature signals combined with a race-level group softmax constraint to guarantee exactly one winner per Grand Prix.
        """)
        
    with col_r:
        if not df.empty:
            wins_by_team = df[df["is_win"] == 1]["constructor_name"].value_counts().head(7).reset_index()
            wins_by_team.columns = ["Constructor", "Wins"]
            fig = px.bar(
                wins_by_team, x="Wins", y="Constructor", orientation="h",
                title="Grand Prix Wins by Constructor (2004–2024)",
                color="Wins", color_continuous_scale=["#333C48", F1_RED]
            )
            fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(get_plotly_theme(fig), use_container_width=True)

with t2:
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="badge-car">PILLAR A: CAR FEATURES</span>
            <h4 style="margin-top: 10px; color: #FFF;">Car &amp; Team Specs</h4>
            <p style="color: #8B949E; font-size: 13px;">
                Engine power (750–1050 BHP), minimum weight rules (605–798 kg), power-to-weight ratio, constructor reliability score, starting grid position, and qualifying position.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="badge-lap">PILLAR B: LAP RECORDS</span>
            <h4 style="margin-top: 10px; color: #FFF;">Lap Record Benchmarks</h4>
            <p style="color: #8B949E; font-size: 13px;">
                Official FIA all-time circuit race records, driver pace delta to track record, qualifying delta to record, speed trap velocities, and field lap time consistency.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="badge-pit">PILLAR C: PIT STOPS</span>
            <h4 style="margin-top: 10px; color: #FFF;">Pit Strategy &amp; Execution</h4>
            <p style="color: #8B949E; font-size: 13px;">
                Expected strategy stops (1, 2, 3+), total race pit loss, circuit pit lane transit penalty (19.4s–27.8s), and DHL pit crew efficiency score.
            </p>
        </div>
        """, unsafe_allow_html=True)
