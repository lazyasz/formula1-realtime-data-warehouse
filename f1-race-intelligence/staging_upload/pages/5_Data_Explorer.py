import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import (
    apply_f1_theme,
    get_pbi_plotly_theme,
    get_local_data,
    render_pbi_header,
    render_pbi_kpi,
    F1_RED
)

apply_f1_theme()

render_pbi_header(
    title="Power BI Telemetry Slicer & Dimensional Explorer",
    subtitle="Interactive Slice-and-Dice Across 8,650 Historical F1 Records &bull; Live Cross-Filtering Visuals",
    page_name="Telemetry Slicer View"
)

df = get_local_data("clean_f1_modeling_master.csv")

if df.empty:
    st.warning("No telemetry records loaded. Please verify data directory.")
    st.stop()

# Power BI Top Slicer Ribbon
st.markdown("""
<div class="pbi-slicer-panel">
    <div style="font-size: 13px; font-weight: 700; color: #F2C811; text-transform: uppercase; margin-bottom: 8px;">
        🎛️ Interactive Power BI Canvas Slicers
    </div>
</div>
""", unsafe_allow_html=True)

s_c1, s_c2, s_c3, s_c4 = st.columns([1.2, 1.2, 1.2, 1.2])

min_yr, max_yr = int(df["season"].min()), int(df["season"].max())
with s_c1:
    season_range = st.slider("📅 Season Range Slicer", min_yr, max_yr, (2018, 2024))

constructors = sorted(df["constructor_name"].dropna().unique().tolist())
with s_c2:
    selected_constructors = st.multiselect(
        "🏎️ Constructor Slicer",
        constructors,
        default=["Red Bull Racing", "Ferrari", "Mercedes", "McLaren"] if all(c in constructors for c in ["Red Bull Racing", "Ferrari", "Mercedes", "McLaren"]) else constructors[:4]
    )

circuits = sorted(df["circuit_name"].dropna().unique().tolist())
with s_c3:
    selected_circuits = st.multiselect("🏁 Circuit Slicer", circuits, default=[])

drivers = sorted(df["driver_name"].dropna().unique().tolist())
with s_c4:
    selected_drivers = st.multiselect("👤 Driver Slicer", drivers, default=[])

# Apply filters
filtered_df = df[(df["season"] >= season_range[0]) & (df["season"] <= season_range[1])]

if selected_constructors:
    filtered_df = filtered_df[filtered_df["constructor_name"].isin(selected_constructors)]
if selected_circuits:
    filtered_df = filtered_df[filtered_df["circuit_name"].isin(selected_circuits)]
if selected_drivers:
    filtered_df = filtered_df[filtered_df["driver_name"].isin(selected_drivers)]

# Handle empty filters gracefully
if filtered_df.empty:
    st.warning("No records match the active filter criteria. Please broaden your selection.")
    st.stop()

# Power BI KPI Scorecards
k1, k2, k3, k4 = st.columns(4)

with k1:
    render_pbi_kpi(
        label="Filtered Records",
        value=f"{len(filtered_df):,}",
        delta=f"{filtered_df['season'].nunique()} Seasons",
        delta_color="#118DFF",
        subtext=f"{filtered_df['race_id'].nunique()} Distinct Grands Prix",
        accent="#118DFF",
        icon="📊"
    )

with k2:
    pole_starters = filtered_df[filtered_df["grid_position"] == 1]
    pole_win_pct = (pole_starters["is_win"].sum() / len(pole_starters) * 100) if len(pole_starters) > 0 else 0.0
    render_pbi_kpi(
        label="Pole-to-Win Conversion",
        value=f"{pole_win_pct:.1f}%",
        delta="Grid P1 Advantage",
        delta_color="#00E676",
        subtext=f"{int(pole_starters['is_win'].sum())} Wins from {len(pole_starters)} Poles",
        accent="#00E676",
        icon="🥇"
    )

with k3:
    avg_pit = filtered_df["avg_pit_duration_sec"].mean() if "avg_pit_duration_sec" in filtered_df.columns else 22.4
    render_pbi_kpi(
        label="Avg Pit Duration",
        value=f"{avg_pit:.2f}s",
        delta="Transit + Stop",
        delta_color="#F2C811",
        subtext="DHL Pit Execution Benchmark",
        accent="#F2C811",
        icon="⏱️"
    )

with k4:
    avg_bhp = filtered_df["car_estimated_power_bhp"].mean() if "car_estimated_power_bhp" in filtered_df.columns else 980.0
    render_pbi_kpi(
        label="Avg Engine Power",
        value=f"{avg_bhp:.0f} BHP",
        delta="Hybrid Turbo Era",
        delta_color=F1_RED,
        subtext="Pillar A: Mechanical Spec",
        accent=F1_RED,
        icon="⚡"
    )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Charts Row 1
c1, c2 = st.columns(2)

with c1:
    fig_grid = px.scatter(
        filtered_df, x="grid_position", y="finish_position",
        color="constructor_name", hover_data=["driver_name", "race_name", "season"],
        title="Starting Grid Position vs. Finish Position (Pre-Race Correlation)",
        labels={"grid_position": "Starting Grid Position", "finish_position": "Final Finish Position"},
        opacity=0.7
    )
    fig_grid.add_shape(type="line", x0=1, y0=1, x1=24, y1=24, line=dict(color="#8B949E", dash="dash"))
    st.plotly_chart(get_pbi_plotly_theme(fig_grid), use_container_width=True)

with c2:
    fig_pace = px.box(
        filtered_df, x="constructor_name", y="driver_lap_record_delta_sec",
        color="constructor_name", title="Driver Lap Record Delta to Circuit Record (sec)",
        labels={"driver_lap_record_delta_sec": "Delta to Track Record (s)", "constructor_name": "Constructor"}
    )
    fig_pace.update_layout(showlegend=False)
    st.plotly_chart(get_pbi_plotly_theme(fig_pace), use_container_width=True)

# Charts Row 2
c3, c4 = st.columns(2)

with c3:
    fig_pit = px.scatter(
        filtered_df, x="pit_crew_efficiency_score", y="avg_pit_duration_sec",
        color="constructor_name", size="pit_stop_count",
        title="Pit Crew Efficiency vs. Average Pit Duration (sec)",
        labels={"pit_crew_efficiency_score": "DHL Efficiency Rating", "avg_pit_duration_sec": "Avg Pit Duration (s)"}
    )
    st.plotly_chart(get_pbi_plotly_theme(fig_pit), use_container_width=True)

with c4:
    fig_power = px.histogram(
        filtered_df, x="car_estimated_power_bhp", color="constructor_name",
        nbins=25, title="Engine Power Output Distribution (BHP)",
        labels={"car_estimated_power_bhp": "Engine Power (BHP)"}
    )
    st.plotly_chart(get_pbi_plotly_theme(fig_power), use_container_width=True)

# Tabular Preview
with st.expander("📄 Filtered Telemetry Data Table", expanded=False):
    st.dataframe(filtered_df[[
        "season", "round", "race_name", "driver_name", "constructor_name",
        "grid_position", "finish_position", "is_win", "car_estimated_power_bhp",
        "circuit_lap_record_sec", "driver_lap_record_delta_sec", "avg_pit_duration_sec"
    ]], use_container_width=True)
