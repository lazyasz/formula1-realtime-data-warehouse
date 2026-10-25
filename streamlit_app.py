"""
===============================================================================
STREAMLIT IN SNOWFLAKE: F1 RACE WINNER PREDICTION & DATA WAREHOUSE DASHBOARD
===============================================================================
Project: Formula 1 Race Winner Prediction (Data Warehousing & Data Mining)
Platform: Streamlit in Snowflake (Snowsight Projects > Streamlit)
Database: F1_DM | Schema: ANALYTICS | Warehouse: F1_WH
===============================================================================
"""

import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="F1 Race Winner Prediction — Data Mining Portfolio",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Carbon Racing CSS
st.markdown("""
<style>
    .main { background-color: #0B0D10; color: #F3F4F6; }
    h1, h2, h3 { color: #FFFFFF; font-family: 'Arial', sans-serif; }
    .stMetric { background: #121418; border: 1px solid #222733; padding: 12px; border-radius: 8px; border-left: 4px solid #E10600; }
</style>
""", unsafe_allow_html=True)

# Snowflake Session Handling with Local Fallback
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    q = lambda sql: session.sql(sql).to_pandas()
    is_snowflake = True
except Exception:
    import sqlite3
    conn = sqlite3.connect("f1_warehouse.db")
    q = lambda sql: pd.read_sql_query(sql.replace("F1_DM.ANALYTICS.", ""), conn)
    is_snowflake = False

# Header
st.title("🏎️ Formula 1 Race Winner Prediction")
st.caption("Data Warehousing (Star Schema) & Data Mining Platform (XGBoost, Apriori, FP-Growth) on Snowflake")

# 5 Core Application Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Race Winner Prediction", 
    "🏎️ Car & Pit Stop Features", 
    "⏱️ Circuit Lap Records", 
    "🛒 Mined Pattern Rules", 
    "📊 7-Algorithm Benchmark"
])

# -----------------------------------------------------------------------------
# TAB 1: PREDICTION (WINNER, CONSTRUCTOR & PODIUM PICKS)
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("🏁 Grand Prix Winner & Constructor Probability Distribution")
    
    try:
        races_df = q("SELECT DISTINCT RACE_NAME, YEAR FROM F1_DM.ANALYTICS.V_TOP_PICKS ORDER BY YEAR DESC, RACE_NAME ASC")
        if not races_df.empty:
            race_options = races_df.apply(lambda r: f"{r['RACE_NAME']} {r['YEAR']}", axis=1).tolist()
            selected_race = st.selectbox("Select Grand Prix Calendar Event:", race_options, index=0)
            
            name, yr = selected_race.rsplit(' ', 1)
            d = q(f"SELECT * FROM F1_DM.ANALYTICS.V_TOP_PICKS WHERE RACE_NAME='{name}' AND YEAR={yr} ORDER BY WIN_PROB DESC")
            t = q(f"SELECT * FROM F1_DM.ANALYTICS.V_TEAM_PROB WHERE RACE_NAME='{name}' AND YEAR={yr} ORDER BY TEAM_WIN_PROB DESC")
            
            if not d.empty and not t.empty:
                col1, col2, col3 = st.columns(3)
                top_driver = d.iloc[0]
                top_team = t.iloc[0]
                podium_names = ", ".join(d.head(3)['DRIVER_NAME'].tolist())
                
                col1.metric("Predicted Winning Driver (P1)", top_driver['DRIVER_NAME'], f"{top_driver['WIN_PROB']:.1%}")
                col2.metric("Predicted Winning Constructor", top_team['TEAM_NAME'], f"{top_team['TEAM_WIN_PROB']:.1%}")
                col3.metric("Predicted Top-3 Podium", podium_names, "Podium Lock")

                st.write("")
                c_left, c_right = st.columns(2)
                
                with c_left:
                    st.caption("Driver Calibrated Win Probability (Sum = 100% per Race)")
                    driver_chart_df = d.set_index('DRIVER_NAME')[['WIN_PROB']].head(10)
                    st.bar_chart(driver_chart_df)
                    
                with c_right:
                    st.caption("Constructor Aggregated Win Probability")
                    team_chart_df = t.set_index('TEAM_NAME')[['TEAM_WIN_PROB']].head(8)
                    st.bar_chart(team_chart_df)
                    
                with st.expander("🔍 View Complete Starting Grid Classification Probabilities"):
                    st.dataframe(d[['PREDICTED_RANK', 'DRIVER_NAME', 'TEAM_NAME', 'WIN_PROB']], use_container_width=True)
            else:
                st.warning("No predictions found for this event.")
        else:
            st.info("No prediction data currently loaded in V_TOP_PICKS.")
    except Exception as e:
        st.error(f"Error querying prediction views: {e}")

# -----------------------------------------------------------------------------
# TAB 2: CAR AND PIT STOP FEATURES
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("🏎️ Constructor Engineering & Pit Stop Telemetry Benchmarks")
    
    try:
        p = q("SELECT * FROM F1_DM.ANALYTICS.V_PIT_BY_TEAM")
        if not p.empty:
            yr_min = int(p['YEAR'].min())
            yr_max = int(p['YEAR'].max())
            yr_sel = st.slider("Select Season Year:", yr_min, yr_max, yr_max)
            
            st.markdown(f"#### Average Pit Stop Duration (s) by Team — Season {yr_sel}")
            pit_season = p[p['YEAR'] == yr_sel].sort_values('AVG_PIT_S')
            st.bar_chart(pit_season.set_index('TEAM_NAME')['AVG_PIT_S'])
        
        st.markdown("#### Car-Feature Proxies (Constructor Rolling Form)")
        form_df = q("""
            SELECT 
                c.TEAM_NAME, 
                ROUND(AVG(f.TEAM_POINTS_L5), 2) AS POINTS_FORM_L5, 
                ROUND(AVG(f.TEAM_DNF_RATE_L10) * 100, 1) AS DNF_RATE_L10_PCT,
                ROUND(AVG(f.TEAM_QUALI_GAP_L5), 3) AS QUALI_GAP_TO_POLE_PCT
            FROM F1_DM.ANALYTICS.FEATURES f
            JOIN F1_DM.ANALYTICS.DIM_CONSTRUCTOR c ON c.CONSTRUCTORID = f.CONSTRUCTORID
            WHERE f.YEAR = 2024
            GROUP BY c.TEAM_NAME
            ORDER BY POINTS_FORM_L5 DESC
        """)
        st.dataframe(form_df, use_container_width=True)
        st.caption("Pillar 1 & 3: Evaluates constructor pace deficits, wheel-gun execution times, and mechanical reliability.")
    except Exception as e:
        st.error(f"Error loading Car & Pit features: {e}")

# -----------------------------------------------------------------------------
# TAB 3: CIRCUIT LAP RECORDS
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("⏱️ Official FIA Circuit Track Lap Records")
    try:
        lr = q("SELECT * FROM F1_DM.ANALYTICS.V_LAP_RECORD ORDER BY LAP_RECORD_S ASC")
        st.dataframe(lr, use_container_width=True)
        st.caption("Pillar 2: Official all-time race lap records strictly established prior to target races.")
        st.bar_chart(lr.set_index('CIRCUIT_NAME')['LAP_RECORD_S'])
    except Exception as e:
        st.error(f"Error loading circuit lap records: {e}")

# -----------------------------------------------------------------------------
# TAB 4: FREQUENT PATTERN MINING & ASSOCIATION RULES
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("🛒 Market Basket Analysis: FP-Growth vs. Apriori Benchmark")
    try:
        rules_df = q("SELECT * FROM F1_DM.ANALYTICS.ASSOC_RULES ORDER BY LIFT DESC")
        st.dataframe(rules_df, use_container_width=True)
        st.caption("Filter: Consequent = RESULT=WIN with Lift > 1.2. Demonstrates candidate-free efficiency of FP-Growth.")
    except Exception as e:
        st.error(f"Error loading association rules: {e}")

# -----------------------------------------------------------------------------
# TAB 5: 7-ALGORITHM CLASSIFICATION BENCHMARK
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("📊 7 Classification Algorithms Comparison & Validation Test")
    try:
        metrics_df = q("SELECT * FROM F1_DM.ANALYTICS.MODEL_METRICS WHERE SPLIT='TEST' ORDER BY TOP1_RACE_ACC DESC")
        st.dataframe(metrics_df, use_container_width=True)
        st.caption("Evaluated strictly on the 2024 Out-of-Sample Test Season across 24 Grands Prix.")
        
        if not metrics_df.empty:
            chart_m = metrics_df.set_index('MODEL')[['TOP1_RACE_ACC', 'TOP3_HIT', 'ROC_AUC']]
            st.bar_chart(chart_m)
    except Exception as e:
        st.error(f"Error loading model benchmark metrics: {e}")

st.divider()
st.caption("Formula 1 Winner Prediction Data Warehouse & Mining Architecture • Snowflake Native Implementation")
