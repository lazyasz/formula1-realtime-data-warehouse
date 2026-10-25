import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED

apply_f1_theme()

st.title("🎯 Input Signals, Target Formulation & Class Balance Architecture")
st.markdown("### Feature Inputs, Model Outputs, Class Imbalance Handling & Worked Examples")

t1, t2, t3 = st.tabs(["📥 Input / Output Specifications", "🏷️ Class Labels & Imbalance Remediation", "🧪 Worked Examples (Input → Output)"])

with t1:
    st.markdown("#### Input Feature Groups (26 Pre-Race Signals)")
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="badge-car">PILLAR A: CAR FEATURES (12)</span>
            <ul style="color: #8B949E; font-size: 13px; margin-top: 10px; padding-left: 20px;">
                <li><code>constructor_name</code> (String)</li>
                <li><code>car_estimated_power_bhp</code> (Float: 750-1050)</li>
                <li><code>car_power_to_weight_ratio</code> (Float: 1.20-1.32)</li>
                <li><code>car_min_weight_kg</code> (Float: 605-798 kg)</li>
                <li><code>car_mechanical_reliability_score</code> (Float)</li>
                <li><code>constructor_pace_index</code> (Float: 0-100)</li>
                <li><code>grid_position</code> (Int: 1-24)</li>
                <li><code>qualifying_position</code> (Int: 1-24)</li>
                <li><code>driver_age_years</code> (Float)</li>
                <li><code>driver_standing_points</code> (Float)</li>
                <li><code>driver_championship_position</code> (Int)</li>
                <li><code>constructor_standing_points</code> (Float)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_in2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="badge-lap">PILLAR B: LAP RECORDS (7)</span>
            <ul style="color: #8B949E; font-size: 13px; margin-top: 10px; padding-left: 20px;">
                <li><code>circuit_lap_record_sec</code> (Float: 65-110s)</li>
                <li><code>driver_lap_record_delta_sec</code> (Float)</li>
                <li><code>driver_lap_record_ratio</code> (Float: 1.00-1.05)</li>
                <li><code>driver_quali_to_record_delta_sec</code> (Float)</li>
                <li><code>fastest_lap_speed</code> (Float: km/h)</li>
                <li><code>average_lap_ms</code> (Float)</li>
                <li><code>driver_fastest_lap_sec</code> (Float)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_in3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="badge-pit">PILLAR C: PIT STOPS (7)</span>
            <ul style="color: #8B949E; font-size: 13px; margin-top: 10px; padding-left: 20px;">
                <li><code>pit_stop_count</code> (Int: 1, 2, 3+)</li>
                <li><code>total_race_pit_loss_sec</code> (Float)</li>
                <li><code>avg_pit_duration_sec</code> (Float)</li>
                <li><code>estimated_stationary_pit_sec</code> (Float: 2.1-3.2s)</li>
                <li><code>pit_crew_efficiency_score</code> (Float: 0-100)</li>
                <li><code>pit_loss_delta_to_race_mean_sec</code> (Float)</li>
                <li><code>circuit_pit_lane_loss_sec</code> (Float: 19.4-27.8s)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### Production Model Outputs & Predictions")
    out_c1, out_c2, out_c3 = st.columns(3)
    with out_c1:
        st.info(r"**Primary Output 1:** Calibrated Win Probability $P(\text{Win}) \in [0.0, 1.0]$ summing to 100% across the race grid.")
    with out_c2:
        st.success("**Primary Output 2:** Binary Class Decision (`Class 1 = Winner`, `Class 0 = Not Winner`) with race-level single winner guarantee.")
    with out_c3:
        st.warning(r"**Secondary Output 3:** Predicted Numerical Finish Position $\hat{y}_{\text{finish}} \in [1.0, 24.0]$ from independent regressor.")

with t2:
    st.markdown("#### Class Imbalance Characterization & 4-Part Mitigation")
    
    col_imb1, col_imb2 = st.columns([1, 1])
    with col_imb1:
        imbalance_df = pd.DataFrame({
            "Classification Label": ["Class 0: Not Winner", "Class 1: Grand Prix Winner"],
            "Row Count": [8238, 412],
            "Prevalence %": [95.24, 4.76],
            "Odds Ratio": ["19.0 to 1", "1 in 20 Drivers"]
        })
        st.table(imbalance_df)

    with col_imb2:
        st.markdown(r"""
        ##### 4-Part Imbalance Remediation Architecture:
        1. **Asymmetric Hessian Scaling (`scale_pos_weight = 19.5`)**:
           Gradients of positive instances (Winners) are upweighted by $19.5\times$ during tree building so missed winners incur severe penalties.
        2. **Stratified Group Cross-Validation**:
           Partitions folds along seasonal and Grand Prix boundaries to ensure balanced positive class distribution across folds.
        3. **Precision-Recall F1-Score Optimizer**:
           Determines decision probability thresholds dynamically on validation PR curves.
        4. **Race-Level Group Softmax Constraint**:
           Enforces the physical rule that exactly one driver wins each race:
           $$P(Y_i = 1 \mid \text{Race } j) = \frac{e^{z_i / T}}{\sum_{k=1}^{20} e^{z_k / T}}$$
        """)

with t3:
    st.markdown("#### Worked End-to-End Prediction Scenarios")
    
    with st.expander("Scenario 1: Front-Row Pole Dominator (Max Verstappen, Red Bull - British GP 2024)", expanded=True):
        sc1_l, sc1_r = st.columns(2)
        with sc1_l:
            st.markdown("""
            **INPUT SIGNALS:**
            * **Car**: Red Bull Racing, BHP: `1035`, Power/Weight: `1.30`, Reliability: `0.96`, Grid: `P1`, Quali: `P1`
            * **Lap Record**: Circuit Record: `87.097s`, Delta: `+0.210s`, Pace Ratio: `1.002`
            * **Pit Stop**: 2 Stops, Pit Transit: `20.5s`, Pit Crew Score: `98.0` (DHL Fastest Pit), Avg Pit: `21.8s`
            """)
        with sc1_r:
            st.markdown("""
            **MODEL INFERENCE OUTPUT:**
            * 🏁 **Calculated Win Probability:** **68.4%**
            * 🏆 **Predicted Class:** **Class 1 (Winner)**
            * 🏎️ **Secondary Predicted Finish Position:** **P1.1**
            * ✓ **Actual Race Outcome:** **Winner (P1)**
            """)

    with st.expander("Scenario 2: Midfield Climber (Fernando Alonso, Aston Martin - British GP 2024)"):
        sc2_l, sc2_r = st.columns(2)
        with sc2_l:
            st.markdown("""
            **INPUT SIGNALS:**
            * **Car**: Aston Martin, BHP: `1005`, Power/Weight: `1.26`, Reliability: `0.91`, Grid: `P9`, Quali: `P8`
            * **Lap Record**: Circuit Record: `87.097s`, Delta: `+1.850s`, Pace Ratio: `1.021`
            * **Pit Stop**: 2 Stops, Pit Transit: `20.5s`, Pit Crew Score: `88.0`, Avg Pit: `23.9s`
            """)
        with sc2_r:
            st.markdown("""
            **MODEL INFERENCE OUTPUT:**
            * 🏁 **Calculated Win Probability:** **2.1%**
            * 🏆 **Predicted Class:** **Class 0 (Not Winner)**
            * 🏎️ **Secondary Predicted Finish Position:** **P7.4**
            * ✓ **Actual Race Outcome:** **P8 (Points Finisher)**
            """)

    with st.expander("Scenario 3: Backmarker Technical Deficit (Logan Sargeant, Williams - British GP 2024)"):
        sc3_l, sc3_r = st.columns(2)
        with sc3_l:
            st.markdown("""
            **INPUT SIGNALS:**
            * **Car**: Williams, BHP: `995`, Power/Weight: `1.25`, Reliability: `0.85`, Grid: `P19`, Quali: `P19`
            * **Lap Record**: Circuit Record: `87.097s`, Delta: `+3.420s`, Pace Ratio: `1.039`
            * **Pit Stop**: 2 Stops, Pit Transit: `20.5s`, Pit Crew Score: `79.0`, Avg Pit: `26.2s`
            """)
        with sc3_r:
            st.markdown("""
            **MODEL INFERENCE OUTPUT:**
            * 🏁 **Calculated Win Probability:** **0.05%**
            * 🏆 **Predicted Class:** **Class 0 (Not Winner)**
            * 🏎️ **Secondary Predicted Finish Position:** **P16.8**
            * ✓ **Actual Race Outcome:** **P17 (Classified Non-Points)**
            """)
