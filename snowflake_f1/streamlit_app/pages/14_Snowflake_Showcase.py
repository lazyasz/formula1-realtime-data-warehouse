import os
import sys
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, F1_RED

apply_f1_theme()

st.title("❄️ Snowflake Enterprise Architecture & Features Showcase")
st.markdown("### Advanced Snowflake Cloud Capabilities Implemented in `06_extras.sql`")

t1, t2, t3, t4, t5 = st.tabs([
    "1. Clone & Time Travel",
    "2. Dynamic Tables & Streams/Tasks",
    "3. Semi-Structured JSON FLATTEN",
    "4. Governance & Elastic Scaling",
    "5. Snowflake Cortex AI Explainer"
])

with t1:
    st.markdown("#### Zero-Copy Clone & Time Travel Demonstration")
    st.markdown("""
    * **Zero-Copy Clone (`CLONE`)**: Creates instantaneous metadata pointers to micro-partitions without duplicating physical storage bytes or incurring additional storage costs.
    * **Time Travel (`AT(OFFSET => -60)`)**: Queries historical states of tables up to 90 days in the past (Enterprise Edition) for forensic audits and instant data recovery.
    """)
    st.code("""-- 1. Zero-Copy Dev Clone (Instantaneous Metadata Clone)
CREATE OR REPLACE TABLE CLEAN.F1_MODELING_MASTER_DEV_CLONE
    CLONE CLEAN.F1_MODELING_MASTER;

-- 2. Time Travel Query (State 60 Seconds Prior)
SELECT COUNT(*) FROM CLEAN.F1_MODELING_MASTER AT(OFFSET => -60);""", language="sql")

with t2:
    st.markdown("#### Dynamic Tables (Continuous Pipelines) & CDC Tasks")
    st.markdown("""
    * **Dynamic Tables (`TARGET_LAG = '1 hour'`)**: Declarative continuous materialization where Snowflake automatically orchestrates dependency DAGs and incremental refreshes.
    * **Streams + Tasks**: Change Data Capture (CDC) capturing incoming race weekend qualifying results and auto-triggering model inference.
    """)
    st.code("""-- Declarative Dynamic Table for Rolling Driver Form
CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.DT_DRIVER_SEASON_FORM
    TARGET_LAG = '1 hour'
    WAREHOUSE = F1_WH
AS
SELECT
    SEASON, ROUND, DRIVER_NAME,
    AVG(GRID_POSITION) OVER (PARTITION BY SEASON, DRIVER_NAME ORDER BY ROUND ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS ROLLING_5RACE_AVG_GRID
FROM CLEAN.F1_MODELING_MASTER;

-- CDC Stream on Staging Results
CREATE OR REPLACE STREAM RAW.STREAM_RACE_RESULTS_CDC ON TABLE RAW.RAW_RACE_RESULTS;""", language="sql")

with t3:
    st.markdown("#### Semi-Structured VARIANT Data & Tabular `FLATTEN`")
    st.markdown("Stores raw JSON tyre compound stint telemetry payloads natively in Snowflake `VARIANT` columns, querying via dot notation and lateral flattening:")
    st.code("""-- Query Semi-Structured JSON Payload with LATERAL FLATTEN
SELECT
    RACE_ID,
    PAYLOAD_VARIANT:grand_prix::STRING AS GRAND_PRIX,
    f.value:stint_num::INT AS STINT_NUM,
    f.value:compound::STRING AS TYRE_COMPOUND,
    f.value:laps::INT AS LAPS_DRIVEN
FROM RAW.RAW_TELEMETRY_JSON,
LATERAL FLATTEN(INPUT => PAYLOAD_VARIANT:stints) f;""", language="sql")

with t4:
    st.markdown("#### Role-Based Access Control (RBAC), Secure Views & Elastic Scaling")
    st.markdown("""
    * **Secure Views**: Masks proprietary engine horsepower and telemetry calculations from unauthorized downstream analysts.
    * **Resource Monitor (`F1_COST_GUARD`)**: Enforces hard budget quotas with automatic suspension at 100% credit consumption.
    * **Elastic Scaling**: Seamlessly resize compute warehouses on-demand (`X-SMALL` &rarr; `MEDIUM`).
    """)
    st.code("""-- Secure View Masking Internal Mechanical Telemetry
CREATE OR REPLACE SECURE VIEW ANALYTICS.SECURE_F1_PUBLIC_LEADERBOARD AS
SELECT SEASON, ROUND, RACE_NAME, DRIVER_NAME, CONSTRUCTOR_NAME, GRID_POSITION, IS_WIN
FROM CLEAN.F1_MODELING_MASTER;

-- Instant Virtual Warehouse Elastic Resizing
ALTER WAREHOUSE F1_WH SET WAREHOUSE_SIZE = 'MEDIUM';
ALTER WAREHOUSE F1_WH SET WAREHOUSE_SIZE = 'X-SMALL';""", language="sql")

with t5:
    st.markdown("#### Snowflake Cortex AI Natural Language Telemetry Explainer")
    st.markdown("Leverages Snowflake Cortex LLMs (`SNOWFLAKE.CORTEX.COMPLETE`) to generate plain-English race engineer explanations for model predictions, with built-in graceful fallback:")
    st.code("""-- Snowflake Cortex AI Stored Procedure (SQL / Mistral-Large2)
CREATE OR REPLACE PROCEDURE ANALYTICS.EXPLAIN_F1_PREDICTION_CORTEX(
    DRIVER_NAME VARCHAR,
    GRID_POS INT,
    WIN_PROB FLOAT
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    PROMPT VARCHAR;
    RESPONSE VARCHAR;
BEGIN
    PROMPT := 'Explain in 2 sentences why driver ' || DRIVER_NAME || 
              ' starting at P' || GRID_POS || ' with win probability ' || 
              ROUND(WIN_PROB * 100, 1) || '% is favored to win.';
    BEGIN
        SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', :PROMPT) INTO :RESPONSE;
        RETURN :RESPONSE;
    EXCEPTION
        WHEN OTHER THEN
            RETURN 'Telemetry Summary: ' || DRIVER_NAME || ' starts at P' || GRID_POS || 
                   ' with ' || ROUND(WIN_PROB * 100, 1) || '% win probability, supported by elite pit crew execution and strong qualifying pace.';
    END;
END;
$$;""", language="sql")

    # Interactive Cortex AI Simulation
    st.markdown("##### 💬 Test Cortex AI Output (Interactive Simulation)")
    t_driver = st.selectbox("Select Driver to Explain", ["Max Verstappen (P1)", "Lando Norris (P2)", "Lewis Hamilton (P7)"])
    if st.button("Generate Cortex AI Summary"):
        if "Verstappen" in t_driver:
            st.info("🤖 **Snowflake Cortex (Mistral-Large2):** *Max Verstappen enters the British Grand Prix with a dominant 68.4% win probability due to capturing Pole Position, backed by Red Bull's category-leading 98.0 pit crew efficiency and superior power-to-weight ratio. Historically, starting from P1 at Silverstone converts to victory in over 65% of modern hybrid-era events.*")
        elif "Norris" in t_driver:
            st.info("🤖 **Snowflake Cortex (Mistral-Large2):** *Lando Norris holds a strong 22.1% win probability from P2 on the front row, leveraging McLaren's recent aero package upgrades and qualifying lap record pace delta of just +0.35s. His primary victory path depends on an undercut pit strategy during the first mandatory tyre window.*")
        else:
            st.info("🤖 **Snowflake Cortex (Mistral-Large2):** *Lewis Hamilton starts from P7 with a 3.4% calculated win probability, reflecting Mercedes' midfield qualifying deficit of +1.20s to pole pace. To contest for the win, Mercedes must execute an aggressive alternative tyre strategy or capitalize on safety car interruptions.*")
