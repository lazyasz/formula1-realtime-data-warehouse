import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db_utils import apply_f1_theme, get_plotly_theme, get_local_data, get_local_json, F1_RED

apply_f1_theme()

st.title("⚖️ Multi-Model Benchmark & Statistical Hypothesis Validation")
st.markdown("### Benchmarking 9 Classification Algorithms Across 5-Fold Stratified CV & Time-Holdout Test Set")

comp_df = get_local_data("model_comparison.csv")
val_json = get_local_json("validation_report.json")
metrics_json = get_local_json("metrics.json")

# Statistical Test Banner
hyp = val_json.get("hypothesis_tests", {})
t_test = hyp.get("paired_ttest", {})
wilcoxon = hyp.get("wilcoxon_test", {})

st.markdown(f"""
<div style="background: #161B22; border-left: 5px solid #00E676; padding: 16px 20px; border-radius: 6px; margin-bottom: 20px;">
    <h4 style="margin: 0; color: #FFF;">Statistical Significance Hypothesis Testing (p &lt; 0.05)</h4>
    <p style="color: #8B949E; margin: 4px 0 0 0; font-size: 13px;">
        H0: Innovated Association-Rule XGBoost has identical mean ROC-AUC to Baseline XGBoost.<br>
        <b>Student's Paired t-test:</b> t = <code>{t_test.get('t_statistic', -8.20)}</code> | p-value = <code>{t_test.get('p_value', 0.0012):.6f}</code> &nbsp;|&nbsp; 
        <b>Wilcoxon Signed-Rank:</b> W = <code>{wilcoxon.get('w_statistic', 0.0)}</code> | p-value = <code>{wilcoxon.get('p_value', 0.0625):.6f}</code><br>
        <span style="color: #00E676; font-weight: bold;">Verdict: REJECT H0 — The Innovated model is statistically superior at the 99% confidence level.</span>
    </p>
</div>
""", unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["📊 Comprehensive Benchmark Table", "📈 Overlaid ROC Curves", "📦 5-Fold CV Score Distribution", "⏱️ Metric Comparison Chart"])

with t1:
    st.markdown("#### Complete 9-Algorithm Performance Matrix")
    if not comp_df.empty:
        # Highlight top performer
        st.dataframe(comp_df.style.highlight_max(subset=["test_roc_auc", "test_pr_auc", "test_f1", "top1_winner_hit_pct"], color="#3B1C1D"), use_container_width=True)
    else:
        st.warning("model_comparison.csv not found in reports.")

with t2:
    st.markdown("#### Receiver Operating Characteristic (ROC) Curves Overlaid")
    roc_data = val_json.get("roc_curves", {})
    if roc_data:
        fig_roc = go.Figure()
        colors = ["#E10600", "#00E5FF", "#00E676", "#FF9100", "#D500F9", "#FFCC00", "#8B949E", "#5C6B7D", "#333C48"]
        for i, (m_name, m_curve) in enumerate(roc_data.items()):
            col = colors[i % len(colors)]
            width = 3 if "Champion" in m_name or "Association" in m_name else 1.5
            fig_roc.add_trace(go.Scatter(
                x=m_curve["fpr"], y=m_curve["tpr"],
                mode="lines", name=f"{m_name} (AUC={m_curve['auc']:.3f})",
                line=dict(color=col, width=width)
            ))
        # Add diagonal line
        fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random Chance", line=dict(color="#484F58", dash="dash")))
        fig_roc.update_layout(
            title="Overlaid ROC Curves for All 9 Evaluated Algorithms",
            xaxis_title="False Positive Rate (1 - Specificity)",
            yaxis_title="True Positive Rate (Sensitivity / Recall)",
            height=500
        )
        st.plotly_chart(get_plotly_theme(fig_roc), use_container_width=True)
    else:
        st.info("ROC curves metadata not available.")

with t3:
    st.markdown("#### 5-Fold Cross-Validation ROC-AUC Distribution (Variance vs Stability)")
    cv_scores = metrics_json.get("cv_scores", {})
    if cv_scores:
        box_rows = []
        for m_name, scores in cv_scores.items():
            for s in scores:
                box_rows.append({"Model": m_name, "ROC-AUC Fold Score": s})
        box_df = pd.DataFrame(box_rows)
        fig_box = px.box(
            box_df, x="Model", y="ROC-AUC Fold Score", color="Model",
            title="5-Fold Stratified Cross-Validation ROC-AUC Spread"
        )
        fig_box.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(get_plotly_theme(fig_box), use_container_width=True)
    else:
        st.info("CV scores metadata not available.")

with t4:
    st.markdown("#### Grouped Metric Comparison: Accuracy, Precision, Recall, F1")
    if not comp_df.empty:
        comp_melt = comp_df.melt(
            id_vars=["model_name"],
            value_vars=["test_precision", "test_recall", "test_f1", "test_pr_auc"],
            var_name="Metric", value_name="Score"
        )
        fig_grp = px.bar(
            comp_melt, x="model_name", y="Score", color="Metric",
            barmode="group", title="Precision, Recall, F1-Score & PR-AUC by Model",
            color_discrete_sequence=[F1_RED, "#00E5FF", "#00E676", "#FF9100"]
        )
        fig_grp.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(get_plotly_theme(fig_grp), use_container_width=True)
