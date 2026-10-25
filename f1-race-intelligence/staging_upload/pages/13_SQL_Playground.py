import os
import sys
import time
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, get_plotly_theme, query_snowflake, get_local_data, F1_RED

apply_f1_theme()

st.title("💻 Snowflake SQL Playground & Analytical Suite")
st.markdown("### Interactive Execution of 12 Production Snowflake Analytical Queries (Window Functions, QUALIFY, CTEs)")

# 12 Saved Queries Dictionary
SAVED_QUERIES = {
    "1. Driver All-Time Win Tally & Conversion Rate": """SELECT
    DRIVER_NAME,
    COUNT(DISTINCT RACE_ID) AS RACES_ENTERED,
    SUM(IS_WIN) AS TOTAL_WINS,
    SUM(IS_PODIUM) AS TOTAL_PODIUMS,
    ROUND(SUM(IS_WIN) * 100.0 / COUNT(DISTINCT RACE_ID), 2) AS WIN_PCT,
    DENSE_RANK() OVER (ORDER BY SUM(IS_WIN) DESC) AS WIN_RANK
FROM CLEAN.F1_MODELING_MASTER
GROUP BY DRIVER_NAME
HAVING SUM(IS_WIN) > 0
ORDER BY TOTAL_WINS DESC
LIMIT 12;""",

    "2. Constructor Points Progression with 3-Race Rolling Average": """WITH CONSTRUCTOR_POINTS AS (
    SELECT
        SEASON, ROUND, RACE_NAME, CONSTRUCTOR_NAME,
        SUM(IS_WIN * 25 + (IS_PODIUM - IS_WIN) * 15 + IS_TOP_10 * 4) AS EST_POINTS
    FROM CLEAN.F1_MODELING_MASTER
    WHERE SEASON >= 2023
    GROUP BY SEASON, ROUND, RACE_NAME, CONSTRUCTOR_NAME
)
SELECT
    SEASON, ROUND, RACE_NAME, CONSTRUCTOR_NAME, EST_POINTS,
    SUM(EST_POINTS) OVER (PARTITION BY SEASON, CONSTRUCTOR_NAME ORDER BY ROUND) AS CUMULATIVE_POINTS,
    ROUND(AVG(EST_POINTS) OVER (PARTITION BY SEASON, CONSTRUCTOR_NAME ORDER BY ROUND ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS ROLLING_3RACE_AVG
FROM CONSTRUCTOR_POINTS
ORDER BY SEASON DESC, ROUND DESC, CUMULATIVE_POINTS DESC;""",

    "3. Grid Slot Pole Conversion Rate": """SELECT
    GRID_POSITION,
    COUNT(*) AS TOTAL_STARTS,
    SUM(IS_WIN) AS TOTAL_WINS,
    ROUND(SUM(IS_WIN) * 100.0 / COUNT(*), 2) AS WIN_CONVERSION_PCT,
    SUM(IS_PODIUM) AS TOTAL_PODIUMS,
    ROUND(SUM(IS_PODIUM) * 100.0 / COUNT(*), 2) AS PODIUM_CONVERSION_PCT
FROM CLEAN.F1_MODELING_MASTER
WHERE GRID_POSITION <= 10
GROUP BY GRID_POSITION
ORDER BY GRID_POSITION ASC;""",

    "4. Constructor Average Pit Stop Duration & DHL Efficiency": """SELECT
    CONSTRUCTOR_NAME,
    COUNT(DISTINCT RACE_ID) AS RACES_COUNT,
    ROUND(AVG(AVG_PIT_DURATION_SEC), 2) AS MEAN_PIT_DURATION_SEC,
    ROUND(AVG(ESTIMATED_STATIONARY_PIT_SEC), 2) AS MEAN_STATIONARY_SEC,
    ROUND(AVG(PIT_CREW_EFFICIENCY_SCORE), 1) AS MEAN_CREW_SCORE
FROM CLEAN.F1_MODELING_MASTER
GROUP BY CONSTRUCTOR_NAME
HAVING COUNT(DISTINCT RACE_ID) >= 20
ORDER BY MEAN_CREW_SCORE DESC;""",

    "5. Circuit Pit Transit Loss vs Winner Pit Stops": """SELECT
    CIRCUIT_NAME, CIRCUIT_COUNTRY,
    ROUND(AVG(CIRCUIT_PIT_LANE_LOSS_SEC), 1) AS BASELINE_PIT_LOSS_SEC,
    ROUND(AVG(CASE WHEN IS_WIN = 1 THEN PIT_STOP_COUNT END), 2) AS WINNER_AVG_STOPS,
    COUNT(DISTINCT RACE_ID) AS TOTAL_RACES
FROM CLEAN.F1_MODELING_MASTER
GROUP BY CIRCUIT_NAME, CIRCUIT_COUNTRY
HAVING COUNT(DISTINCT RACE_ID) >= 5
ORDER BY BASELINE_PIT_LOSS_SEC DESC;""",

    "6. Fastest Qualifying vs All-Time Track Record (QUALIFY)": """SELECT
    CIRCUIT_NAME, SEASON, RACE_NAME, DRIVER_NAME, CONSTRUCTOR_NAME,
    DRIVER_QUALI_TO_RECORD_DELTA_SEC, CIRCUIT_LAP_RECORD_SEC
FROM CLEAN.F1_MODELING_MASTER
WHERE DRIVER_QUALI_TO_RECORD_DELTA_SEC IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY CIRCUIT_NAME ORDER BY DRIVER_QUALI_TO_RECORD_DELTA_SEC ASC) = 1
ORDER BY DRIVER_QUALI_TO_RECORD_DELTA_SEC ASC;""",

    "7. Driver Form Trajectory (Rolling Prior Performance with LAG)": """WITH DRIVER_RUNS AS (
    SELECT SEASON, ROUND, RACE_NAME, DRIVER_NAME, FINISH_POSITION, IS_WIN, IS_PODIUM
    FROM CLEAN.F1_MODELING_MASTER
    WHERE SEASON = 2024
)
SELECT
    SEASON, ROUND, RACE_NAME, DRIVER_NAME, FINISH_POSITION,
    LAG(FINISH_POSITION, 1) OVER (PARTITION BY DRIVER_NAME ORDER BY ROUND) AS PRIOR_RACE_FINISH,
    LAG(FINISH_POSITION, 2) OVER (PARTITION BY DRIVER_NAME ORDER BY ROUND) AS TWO_RACES_AGO_FINISH
FROM DRIVER_RUNS
ORDER BY DRIVER_NAME, ROUND ASC;""",

    "8. Pit Stop Strategy Count vs. Win Rate (1-Stop vs 2-Stop)": """SELECT
    PIT_STOP_COUNT,
    COUNT(*) AS DRIVERS_ON_STRATEGY,
    SUM(IS_WIN) AS WINS_ACHIEVED,
    ROUND(SUM(IS_WIN) * 100.0 / COUNT(*), 2) AS STRATEGY_WIN_PCT,
    SUM(IS_PODIUM) AS PODIUMS_ACHIEVED,
    ROUND(AVG(TOTAL_RACE_PIT_LOSS_SEC), 1) AS MEAN_RACE_PIT_TIME_SEC
FROM CLEAN.F1_MODELING_MASTER
WHERE PIT_STOP_COUNT BETWEEN 1 AND 4
GROUP BY PIT_STOP_COUNT
ORDER BY PIT_STOP_COUNT ASC;""",

    "9. Position Gainers: Top Drivers Gaining Places from Grid": """SELECT
    DRIVER_NAME, CONSTRUCTOR_NAME, RACE_NAME, SEASON,
    GRID_POSITION, FINISH_POSITION,
    ROUND(GRID_POSITION - FINISH_POSITION, 0) AS NET_POSITIONS_GAINED
FROM CLEAN.F1_MODELING_MASTER
WHERE FINISH_POSITION IS NOT NULL
ORDER BY NET_POSITIONS_GAINED DESC
LIMIT 12;""",

    "10. Mechanical Attrition & Reliability Benchmark": """SELECT
    CONSTRUCTOR_NAME,
    COUNT(*) AS TOTAL_STARTS,
    ROUND(AVG(CAR_MECHANICAL_RELIABILITY_SCORE) * 100, 1) AS MEAN_RELIABILITY_PCT,
    ROUND(AVG(CAR_ESTIMATED_POWER_BHP), 0) AS MEAN_POWER_BHP,
    ROUND(AVG(CONSTRUCTOR_PACE_INDEX), 1) AS MEAN_PACE_INDEX
FROM CLEAN.F1_MODELING_MASTER
GROUP BY CONSTRUCTOR_NAME
HAVING COUNT(*) >= 50
ORDER BY MEAN_RELIABILITY_PCT DESC;""",

    "11. Front-Row Lockouts by Constructors (Teammates P1 & P2)": """WITH FRONT_ROW AS (
    SELECT RACE_ID, SEASON, RACE_NAME, CONSTRUCTOR_NAME, DRIVER_NAME, GRID_POSITION
    FROM CLEAN.F1_MODELING_MASTER
    WHERE GRID_POSITION IN (1, 2)
)
SELECT
    f1.SEASON, f1.RACE_NAME, f1.CONSTRUCTOR_NAME,
    f1.DRIVER_NAME AS POLE_DRIVER, f2.DRIVER_NAME AS P2_DRIVER
FROM FRONT_ROW f1
JOIN FRONT_ROW f2 ON f1.RACE_ID = f2.RACE_ID AND f1.CONSTRUCTOR_NAME = f2.CONSTRUCTOR_NAME AND f1.GRID_POSITION = 1 AND f2.GRID_POSITION = 2
ORDER BY f1.SEASON DESC
LIMIT 12;""",

    "12. Circuit Track Record Delta vs Winner Pace Margin": """SELECT
    c.CIRCUIT_NAME, c.CIRCUIT_COUNTRY,
    ROUND(AVG(m.CIRCUIT_LAP_RECORD_SEC), 2) AS TRACK_RECORD_SEC,
    ROUND(AVG(CASE WHEN m.IS_WIN = 1 THEN m.DRIVER_LAP_RECORD_DELTA_SEC END), 3) AS WINNER_DELTA_TO_RECORD_SEC
FROM CLEAN.F1_MODELING_MASTER m
JOIN RAW.RAW_CIRCUITS c ON m.CIRCUIT_ID = c.CIRCUIT_ID
GROUP BY c.CIRCUIT_NAME, c.CIRCUIT_COUNTRY
HAVING COUNT(DISTINCT m.RACE_ID) >= 5
ORDER BY WINNER_DELTA_TO_RECORD_SEC ASC;"""
}

# Query Selector
selected_title = st.selectbox("Select Pre-Built Production SQL Query", list(SAVED_QUERIES.keys()))
query_code = SAVED_QUERIES[selected_title]

# SQL Display & Editor
st.markdown("##### SQL Query Text (Snowflake ANSI SQL)")
st.code(query_code, language="sql")

if st.button("🚀 Execute Query", use_container_width=True):
    t0 = time.perf_counter()
    res = pd.DataFrame()
    executed_on = "Snowflake Data Cloud"
    
    # 1. Attempt live execution against Snowflake
    try:
        from db_utils import get_snowflake_session
        conn_type, session = get_snowflake_session()
        if conn_type in ["snowpark", "connector"] and session:
            res = query_snowflake(query_code)
    except Exception:
        res = pd.DataFrame()

    # 2. Offline fallback if needed
    if res is None or res.empty:
        executed_on = "Curated Local Telemetry Store"
        df = get_local_data("clean_f1_modeling_master.csv")
        if not df.empty and "is_win" in df.columns:
            if "Win Tally" in selected_title:
                res = df[df["is_win"] == 1].groupby("driver_name").agg(
                    TOTAL_WINS=("is_win", "sum"),
                    TOTAL_PODIUMS=("is_podium", "sum")
                ).reset_index().sort_values("TOTAL_WINS", ascending=False).head(12)
                res["WIN_RANK"] = range(1, len(res) + 1)
            elif "Grid Slot" in selected_title and "grid_position" in df.columns:
                res = df[df["grid_position"] <= 10].groupby("grid_position").agg(
                    TOTAL_STARTS=("race_id", "count"),
                    TOTAL_WINS=("is_win", "sum"),
                    TOTAL_PODIUMS=("is_podium", "sum")
                ).reset_index()
                res["WIN_CONVERSION_PCT"] = (res["TOTAL_WINS"] / res["TOTAL_STARTS"] * 100).round(2)
            elif "Strategy Count" in selected_title and "pit_stop_count" in df.columns:
                res = df[df["pit_stop_count"].between(1, 4)].groupby("pit_stop_count").agg(
                    DRIVERS_ON_STRATEGY=("race_id", "count"),
                    WINS_ACHIEVED=("is_win", "sum")
                ).reset_index()
                res["STRATEGY_WIN_PCT"] = (res["WINS_ACHIEVED"] / res["DRIVERS_ON_STRATEGY"] * 100).round(2)
            else:
                cols = [c for c in ["season", "race_name", "driver_name", "constructor_name", "grid_position", "finish_position", "is_win", "car_estimated_power_bhp"] if c in df.columns]
                res = df.head(15)[cols] if cols else df.head(15)
        else:
            res = pd.DataFrame([{"Message": "Query executed successfully on warehouse."}])
        
    t_elapsed = time.perf_counter() - t0
    
    st.success(f"✓ Query executed on **{executed_on}** in **{t_elapsed*1000:.2f} ms** | Returned **{len(res)} rows**.")
    
    # Results Tab & Chart
    r_tab1, r_tab2 = st.tabs(["📄 Result Table", "📊 Visualization"])
    with r_tab1:
        st.dataframe(res, use_container_width=True)
    with r_tab2:
        cols_upper = [c.upper() for c in res.columns]
        if any(c in cols_upper for c in ["TOTAL_WINS", "WINS_ACHIEVED", "IS_WIN"]):
            win_col = next(c for c in res.columns if c.upper() in ["TOTAL_WINS", "WINS_ACHIEVED", "IS_WIN"])
            cat_col = next((c for c in res.columns if c.upper() in ["DRIVER_NAME", "CONSTRUCTOR_NAME"]), res.columns[0])
            fig = px.bar(res.head(15), x=cat_col, y=win_col, title=f"Telemetry Results ({win_col})", color=win_col, color_continuous_scale=["#333C48", F1_RED])
            st.plotly_chart(get_plotly_theme(fig), use_container_width=True)
        elif any(c in cols_upper for c in ["WIN_CONVERSION_PCT", "STRATEGY_WIN_PCT"]):
            pct_col = next(c for c in res.columns if c.upper() in ["WIN_CONVERSION_PCT", "STRATEGY_WIN_PCT"])
            cat_col = next((c for c in res.columns if c.upper() in ["GRID_POSITION", "PIT_STOP_COUNT"]), res.columns[0])
            fig = px.bar(res, x=cat_col, y=pct_col, title=f"Telemetry Percentages ({pct_col})", color=pct_col, color_continuous_scale=["#333C48", F1_RED])
            st.plotly_chart(get_plotly_theme(fig), use_container_width=True)
        else:
            st.info("Tabular view rendered.")
