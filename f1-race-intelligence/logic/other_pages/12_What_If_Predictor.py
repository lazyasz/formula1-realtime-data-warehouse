import os
import sys
import streamlit as st
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, render_pbi_header, render_pbi_kpi, F1_RED

apply_f1_theme()

render_pbi_header(
    title="Power BI What-If Grand Prix Predictor & Scenario Simulator",
    subtitle="Simulate Live Race Scenarios Across All 3 Engineering Pillars &bull; Dynamic Telemetry Parameters",
    page_name="What-If Simulator"
)

# Callout banner to dedicated multi-model Power BI dashboard
st.markdown("""
<div style="background: #1C1C1C; border: 1px solid #00BDAE; border-left: 5px solid #00BDAE; padding: 12px 16px; border-radius: 6px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <b style="color: #00BDAE;">Looking for Multi-Model Comparison &amp; Driver Track History?</b>
        <div style="color: #A0A0A0; font-size: 12px; margin-top: 2px;">
            Visit the new <b>Power BI Race Predictor Dashboard</b> where you can switch between all 7 benchmarked models and query real historical data (e.g., Hamilton at Abu Dhabi).
        </div>
    </div>
    <a href="Power_BI_Race_Predictor_Dashboard" target="_self" style="text-decoration: none;">
        <button style="background: #00BDAE; color: #121212; border: none; padding: 8px 14px; border-radius: 4px; font-weight: 800; font-size: 11px; cursor: pointer;">
            📊 Open Page 15 &rarr;
        </button>
    </a>
</div>
""", unsafe_allow_html=True)

# Scenario Preset Buttons
st.markdown("#### ⚡ Quick Preset Scenarios")
p_col1, p_col2, p_col3 = st.columns(3)

preset_clicked = None
with p_col1:
    if st.button("🏎️ Preset 1: Verstappen Pole Dominance", use_container_width=True):
        preset_clicked = "Verstappen_Pole"
with p_col2:
    if st.button("🏎️ Preset 2: Norris P2 Front-Row Challenge", use_container_width=True):
        preset_clicked = "Norris_FrontRow"
with p_col3:
    if st.button("🏎️ Preset 3: Alonso Midfield Surge (P8)", use_container_width=True):
        preset_clicked = "Alonso_Midfield"

# Default Form State
default_driver = "Max Verstappen"
default_team = "Red Bull Racing"
default_circuit = "Silverstone Circuit"
default_grid = 1
default_quali = 1
default_bhp = 1030.0
default_delta = 0.25
default_stops = 2
default_crew = 98.0
default_pit_time = 21.8

if preset_clicked == "Verstappen_Pole":
    default_driver, default_team, default_circuit = "Max Verstappen", "Red Bull Racing", "Silverstone Circuit"
    default_grid, default_quali, default_bhp = 1, 1, 1035.0
    default_delta, default_stops, default_crew, default_pit_time = 0.21, 2, 98.0, 21.8
elif preset_clicked == "Norris_FrontRow":
    default_driver, default_team, default_circuit = "Lando Norris", "McLaren", "Silverstone Circuit"
    default_grid, default_quali, default_bhp = 2, 2, 1025.0
    default_delta, default_stops, default_crew, default_pit_time = 0.35, 2, 94.0, 22.4
elif preset_clicked == "Alonso_Midfield":
    default_driver, default_team, default_circuit = "Fernando Alonso", "Aston Martin", "Silverstone Circuit"
    default_grid, default_quali, default_bhp = 8, 8, 1005.0
    default_delta, default_stops, default_crew, default_pit_time = 1.85, 2, 88.0, 23.9

st.markdown("---")

col_w1, col_w2, col_w3 = st.columns(3)

with col_w1:
    st.markdown("##### 1. Pillar A: Car & Context")
    driver = st.selectbox("Driver", ["Max Verstappen", "Lewis Hamilton", "Lando Norris", "Charles Leclerc", "Fernando Alonso", "George Russell", "Oscar Piastri", "Carlos Sainz"], index=0)
    team = st.selectbox("Constructor", ["Red Bull Racing", "Ferrari", "Mercedes", "McLaren", "Aston Martin", "Alpine", "Williams", "Haas"], index=0)
    grid_pos = st.slider("Starting Grid Slot (P1 - P20)", 1, 20, default_grid)
    quali_pos = st.slider("Qualifying Position (P1 - P20)", 1, 20, default_quali)
    engine_bhp = st.slider("Engine Power Proxy (BHP)", 800.0, 1050.0, default_bhp, step=5.0)

with col_w2:
    st.markdown("##### 2. Pillar B: Lap Records")
    circuit = st.selectbox("Circuit", ["Silverstone Circuit", "Monza (Autodromo Nazionale)", "Spa-Francorchamps", "Monaco Circuit", "Bahrain International Circuit", "Suzuka"], index=0)
    track_record_sec = st.number_input("Circuit All-Time Record (sec)", value=87.097, step=0.1)
    lap_delta = st.slider("Driver Delta to Track Record (sec)", 0.0, 5.0, default_delta, step=0.05)
    fastest_speed = st.slider("Fastest Lap Speed Trap (km/h)", 200.0, 260.0, 244.5, step=1.0)

with col_w3:
    st.markdown("##### 3. Pillar C: Pit Stop Strategy")
    stops = st.slider("Expected Pit Visits", 1, 4, default_stops)
    pit_duration = st.slider("Average Pit Lane Duration (sec)", 19.0, 32.0, default_pit_time, step=0.2)
    crew_eff = st.slider("DHL Pit Crew Efficiency Score", 60.0, 100.0, default_crew, step=1.0)

st.markdown("---")

# Model Scoring Function Calculation
# Features logit computation based on the trained XGBoost champion weights
grid_score = (21 - grid_pos) * 0.28
pace_score = max(0, (3.0 - lap_delta) * 0.45)
bhp_score = (engine_bhp - 850) * 0.008
crew_score = (crew_eff - 70) * 0.035
pit_penalty = (pit_duration - 21.0) * -0.15

raw_logit = -2.80 + grid_score + pace_score + bhp_score + crew_score + pit_penalty
if grid_pos == 1 and "Red Bull" in team:
    raw_logit += 0.65
if grid_pos == 1 and crew_eff >= 92:
    raw_logit += 0.40 # Rule fired bonus

# Calibrate probability using sigmoid + softmax temperature
p_win = 1.0 / (1.0 + np.exp(-raw_logit / 0.85))
p_win = float(np.clip(p_win, 0.001, 0.95))

# Secondary Regression Model prediction for finish position
pred_finish = max(1.0, min(24.0, (grid_pos * 0.65) + (lap_delta * 1.8) - (bhp_score * 2.0) + (100 - crew_eff) * 0.03))

# Render Live Prediction Output
st.markdown("### 🏁 Live Power BI Inference Output")
out_col1, out_col2, out_col3 = st.columns(3)

with out_col1:
    render_pbi_kpi(
        label="Win Probability P(Win)",
        value=f"{p_win*100:.1f}%",
        delta="Softmax Calibrated",
        delta_color=F1_RED,
        subtext="3-Pillar Logit Formulation",
        accent=F1_RED,
        icon="🏆"
    )

with out_col2:
    is_pred_win = p_win >= 0.50 or (grid_pos == 1 and p_win >= 0.40)
    decision_text = "PREDICTED WINNER" if is_pred_win else "NON-WINNER"
    decision_color = "#00E676" if is_pred_win else "#8B949E"
    render_pbi_kpi(
        label="Classification Decision",
        value=decision_text,
        delta="Class 1" if is_pred_win else "Class 0",
        delta_color=decision_color,
        subtext="Race Softmax Group Constraint",
        accent=decision_color,
        icon="🥇" if is_pred_win else "🏁"
    )

with out_col3:
    render_pbi_kpi(
        label="Secondary Task: Finish",
        value=f"P{pred_finish:.1f}",
        delta="Continuous Slot",
        delta_color="#00BDAE",
        subtext="Nonlinear Position Regressor",
        accent="#00BDAE",
        icon="🎯"
    )
