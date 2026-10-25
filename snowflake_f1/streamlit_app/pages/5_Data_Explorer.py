import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, get_plotly_theme, get_local_data, F1_RED

apply_f1_theme()

st.title("🔍 Data Explorer & Interactive Telemetry Slicer")
st.markdown("### Slice and Dice 8,650 Grand Prix Records Across 21 Seasons")

df = get_local_data("clean_f1_modeling_master.csv")

if df.empty:
    st.warning("No telemetry records loaded. Please verify data directory.")
    st.stop()

# Sidebar Filters
st.sidebar.markdown("### 🎛️ Global Slicers")

min_yr, max_yr = int(df["season"].min()), int(df["season"].max())
season_range = st.sidebar.slider("Season Range", min_yr, max_yr, (2018, 2024))

constructors = sorted(df["constructor_name"].dropna().unique().tolist())
selected_constructors = st.sidebar.multiselect("Constructors", constructors, default=["Red Bull Racing", "Ferrari", "Mercedes", "McLaren"] if all(c in constructors for c in ["Red Bull Racing", "Ferrari", "Mercedes", "McLaren"]) else constructors[:4])

circuits = sorted(df["circuit_name"].dropna().unique().tolist())
selected_circuits = st.sidebar.multiselect("Circuits", circuits, default=[])

drivers = sorted(df["driver_name"].dropna().unique().tolist())
selected_drivers = st.sidebar.multiselect("Drivers", drivers, default=[])

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

st.markdown(f"**Showing {len(filtered_df):,} filtered records** across {filtered_df['season'].nunique()} seasons and {filtered_df['race_id'].nunique()} Grands Prix.")

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
    # Add diagonal line
    fig_grid.add_shape(type="line", x0=1, y0=1, x1=24, y1=24, line=dict(color="#8B949E", dash="dash"))
    st.plotly_chart(get_plotly_theme(fig_grid), use_container_width=True)

with c2:
    fig_pace = px.box(
        filtered_df, x="constructor_name", y="driver_lap_record_delta_sec",
        color="constructor_name", title="Driver Lap Record Delta to Circuit Record (sec)",
        labels={"driver_lap_record_delta_sec": "Delta to Track Record (s)", "constructor_name": "Constructor"}
    )
    fig_pace.update_layout(showlegend=False)
    st.plotly_chart(get_plotly_theme(fig_pace), use_container_width=True)

# Charts Row 2
c3, c4 = st.columns(2)

with c3:
    fig_pit = px.scatter(
        filtered_df, x="pit_crew_efficiency_score", y="avg_pit_duration_sec",
        color="constructor_name", size="pit_stop_count",
        title="Pit Crew Efficiency vs. Average Pit Duration (sec)",
        labels={"pit_crew_efficiency_score": "DHL Efficiency Rating", "avg_pit_duration_sec": "Avg Pit Duration (s)"}
    )
    st.plotly_chart(get_plotly_theme(fig_pit), use_container_width=True)

with c4:
    fig_power = px.histogram(
        filtered_df, x="car_estimated_power_bhp", color="constructor_name",
        nbins=25, title="Engine Power Output Distribution (BHP)",
        labels={"car_estimated_power_bhp": "Engine Power (BHP)"}
    )
    st.plotly_chart(get_plotly_theme(fig_power), use_container_width=True)

# Tabular Preview
with st.expander("📄 Filtered Telemetry Data Table", expanded=False):
    st.dataframe(filtered_df[[
        "season", "round", "race_name", "driver_name", "constructor_name",
        "grid_position", "finish_position", "is_win", "car_estimated_power_bhp",
        "circuit_lap_record_sec", "driver_lap_record_delta_sec", "avg_pit_duration_sec"
    ]], use_container_width=True)
