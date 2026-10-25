import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, F1_RED

apply_f1_theme()

st.title("🏛️ End-to-End Modern Data Stack Architecture & Snowflake Pipeline")
st.markdown("### End-to-End Modern Data Stack & Machine Learning Lifecycle on Snowflake")

import base64

# Render Architecture SVG
svg_candidates = [
    os.path.join(os.path.dirname(__file__), "..", "docs", "architecture.svg"),
    os.path.join(os.path.dirname(__file__), "docs", "architecture.svg"),
    os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "docs", "architecture.svg"),
    os.path.join(os.path.dirname(__file__), "architecture.svg")
]
svg_content = None
for p in svg_candidates:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            svg_content = f.read()
        break

if svg_content:
    b64_svg = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    st.markdown(
        f'<div style="background: #0B0D10; border-radius: 12px; border: 1px solid #30363D; padding: 15px; margin-bottom: 25px; text-align: center;">'
        f'<img src="data:image/svg+xml;base64,{b64_svg}" style="width: 100%; max-width: 1400px; height: auto; border-radius: 8px; display: block; margin: 0 auto;" alt="Formula 1 Modern Data Stack Architecture" />'
        f'</div>',
        unsafe_allow_html=True
    )
else:
    st.info("Architecture vector specification rendered in documentation suite.")

st.markdown("---")

st.markdown("### 🛠️ 5-Tier Pipeline Component Breakdown & Toolchain")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 1. Ingestion & Staging Tier (Python / SnowSQL)
    * **Source Data**: 8,650 historical race results (2004–2024), 412 Grands Prix across 38 circuits.
    * **Snowflake Stage**: `@RAW.F1_RAW_STAGE` with gzip compression and CSV file format parsing.
    * **Raw Storage**: Declarative `COPY INTO` loading immutable dimensional tables:
      `RAW_RACES`, `RAW_DRIVERS`, `RAW_CONSTRUCTORS`, `RAW_CIRCUITS`, `RAW_RACE_RESULTS`.
    
    #### 2. Feature Store Tier (Snowflake SQL / Snowpark)
    * **Table**: `CLEAN.F1_MODELING_MASTER` at the atomic grain of 1 row per driver per race.
    * **The 3 Pillars**:
      * **Car Specs**: BHP (750–1,050), Min Weight (605–798 kg), Reliability, Starting Grid.
      * **Lap Records**: FIA Circuit records, Driver Delta (sec), Pace Ratio, Qualifying Delta.
      * **Pit Strategy**: Stops Count (1, 2, 3+), Transit Loss, Stationary Time, DHL Crew Score.
    * **Leakage Isolation**: Strict pre-race boundaries (no finish time, race points, or finish position as inputs).
    """)

with col2:
    st.markdown("""
    #### 3. Pattern Mining & ML Engine (MLxtend / Scikit-Learn / XGBoost)
    * **FP-Growth & Apriori**: Discretizes telemetry into items; discovers 7,940 frequent itemsets and 141,763 rules.
    * **Classifier Benchmark**: 8 baselines evaluated on 5-fold stratified CV & 2021–2024 holdout test set.
    * **Champion Innovation**: Association-Rule Feature Augmentation + Cost-Sensitive Hessian Scaling (`scale_pos_weight = 19.5`) + Group Softmax argmax constraint.
    * **Secondary Regression**: Independent Random Forest Regressor predicting finish position.
    
    #### 4. Snowflake Serving & Streamlit UI (SiS & Cortex AI)
    * **Registry Tables**: `ML.MODEL_COMPARISON`, `ML.ASSOCIATION_RULES`, `ML.MODEL_METRICS`.
    * **Snowflake Enterprise**: Zero-Copy Clone, Time Travel, Dynamic Tables, Streams & Tasks, Secure Views.
    * **Streamlit in Snowflake**: 14 multi-page dashboard with interactive What-If scenario simulations.
    """)
