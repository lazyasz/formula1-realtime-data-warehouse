"""
🏎️ Formula 1 Race Intelligence — Jury Evaluation Platform
===========================================================
Streamlined Multi-Page Application for Review & Evaluation.
Exclusively focuses on the 3 core required deliverables:
1. Pattern Matching (FP-Growth vs. Apriori)
2. Classification Model Comparison (9 Benchmark Algorithms)
3. Champion Model Classification with Live Performance Metrics
"""

import sys
import os
import streamlit as st

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="ApexIQ - F1 Race Winner Intelligence (Jury Suite)",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Multi-Page Navigation explicitly isolated to the Jury deliverables
jury_hub = st.Page("jury/streamlit_app.py", title="Jury Executive Hub", icon="🏎️", default=True)
p1 = st.Page("jury/pages/1_Pattern_Matching.py", title="1. Pattern Matching", icon="🧩")
p2 = st.Page("jury/pages/2_Classification_Comparison.py", title="2. Model Comparison", icon="📊")
p3 = st.Page("jury/pages/3_Model_Classification_and_Performance_Metrics.py", title="3. Champion Model & Metrics", icon="🏆")

pg = st.navigation({
    "Jury Evaluation Suite": [jury_hub, p1, p2, p3]
})

pg.run()
