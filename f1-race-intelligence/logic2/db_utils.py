"""
Formula 1 Snowflake & Streamlit Utility Helper
=============================================
Manages Snowflake Snowpark Session / Local Connector with seamless offline fallback:
- Prioritizes snowflake.snowpark.context.get_active_session() in SiS
- Falls back to snowflake.connector with .env credentials
- Falls back to local CSV/JSON in reports/ and data/ when offline
- Provides F1 dark racing theme Plotly styling and metric cards
"""

import os
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Safe environment loading (optional in Snowflake SiS)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

F1_RED = "#E10600"
F1_DARK_BG = "#0B0D10"
F1_CARD_BG = "#161B22"
F1_BORDER = "#30363D"
F1_TEXT_MUTED = "#8B949E"

def apply_f1_theme():
    """Applies custom dark carbon and F1 racing red CSS styling with high-contrast visibility."""
    st.markdown(f"""
        <style>
        /* Base Application Layout */
        .stApp {{
            background-color: {F1_DARK_BG} !important;
            color: #E6EDF3 !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        /* Headings & Text */
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }}
        .stApp p, .stApp span, .stApp label, .stApp div {{
            color: #E6EDF3;
        }}

        /* High-Contrast Sidebar */
        [data-testid="stSidebar"] {{
            background-color: #0D1117 !important;
            border-right: 1px solid {F1_BORDER} !important;
        }}
        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebarNav"] span,
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] li,
        [data-testid="stSidebarNav"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
        [data-testid="stSidebarNavItems"] span,
        [data-testid="stSidebarNavItems"] a,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] a {{
            color: #FFFFFF !important;
        }}
        [data-testid="stSidebarNav"] {{
            padding-top: 1rem;
        }}
        [data-testid="stSidebarNav"] a {{
            color: #C9D1D9 !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            padding: 8px 14px !important;
            border-radius: 6px !important;
            margin-bottom: 3px !important;
            transition: all 0.2s ease !important;
            background-color: transparent !important;
        }}
        [data-testid="stSidebarNav"] a span {{
            color: #E6EDF3 !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            background-color: rgba(225, 6, 0, 0.2) !important;
            color: #FFFFFF !important;
            transform: translateX(4px);
        }}
        [data-testid="stSidebarNav"] a:hover span {{
            color: #FFFFFF !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNav"] li[aria-selected="true"] a {{
            background: linear-gradient(90deg, rgba(225, 6, 0, 0.35) 0%, rgba(225, 6, 0, 0.08) 100%) !important;
            border-left: 4px solid {F1_RED} !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNav"] li[aria-selected="true"] a span {{
            color: #FFFFFF !important;
        }}

        /* Metric Cards */
        .metric-card {{
            background-color: {F1_CARD_BG};
            border-left: 4px solid {F1_RED};
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.4);
            border: 1px solid #21262D;
            border-left: 4px solid {F1_RED};
        }}
        .metric-label {{
            font-size: 12px;
            color: {F1_TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
            margin-bottom: 6px;
        }}
        .metric-value {{
            font-size: 26px;
            font-weight: 800;
            color: #FFFFFF !important;
            letter-spacing: 0.5px;
        }}
        .metric-delta {{
            font-size: 12px;
            color: #00E676;
            margin-top: 5px;
            font-weight: 500;
        }}

        /* Badges */
        .badge-car {{
            background: rgba(225, 6, 0, 0.25);
            color: #FF7B7B !important;
            border: 1px solid #E10600;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        .badge-lap {{
            background: rgba(0, 229, 255, 0.25);
            color: #00E5FF !important;
            border: 1px solid #00E5FF;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        .badge-pit {{
            background: rgba(255, 204, 0, 0.25);
            color: #FFD54F !important;
            border: 1px solid #FFCC00;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}

        /* Tables & Markdown */
        table {{
            color: #E6EDF3 !important;
            background-color: #161B22 !important;
            border-collapse: collapse !important;
            width: 100%;
            margin: 15px 0;
            border-radius: 6px;
            overflow: hidden;
        }}
        th {{
            background-color: #21262D !important;
            color: #FFFFFF !important;
            border: 1px solid #30363D !important;
            padding: 10px 14px !important;
            font-size: 13px !important;
            text-transform: uppercase;
        }}
        td {{
            border: 1px solid #30363D !important;
            padding: 10px 14px !important;
            font-size: 14px !important;
        }}
        tr:nth-child(even) {{
            background-color: #0E1217 !important;
        }}

        /* Power BI Visual Card & KPI Design System */
        .pbi-card {{
            background-color: #242424 !important;
            border: 1px solid #383838 !important;
            border-radius: 6px !important;
            padding: 16px 20px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.45) !important;
            transition: all 0.25s ease !important;
        }}
        .pbi-card:hover {{
            border-color: #00BDAE !important;
            box-shadow: 0 6px 18px rgba(0, 189, 174, 0.15) !important;
        }}
        .pbi-header-ribbon {{
            background: linear-gradient(135deg, #1A1A1A 0%, #242424 50%, #1A1A1A 100%) !important;
            border-bottom: 2px solid #00BDAE !important;
            border-radius: 8px !important;
            padding: 14px 22px !important;
            margin-bottom: 18px !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            box-shadow: 0 4px 14px rgba(0,0,0,0.5) !important;
        }}
        .pbi-slicer-panel {{
            background: #1C1C1C !important;
            border: 1px solid #383838 !important;
            border-radius: 8px !important;
            padding: 16px 20px !important;
            margin-bottom: 20px !important;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5) !important;
        }}
        .pbi-kpi-container {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: #242424;
            border: 1px solid #383838;
            border-top: 4px solid #00BDAE;
            border-radius: 6px;
            padding: 14px 18px;
            min-height: 110px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.35);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .pbi-kpi-container:hover {{
            transform: translateY(-2px);
            border-top-color: #00E676;
            box-shadow: 0 6px 16px rgba(0, 230, 118, 0.15);
        }}
        .pbi-kpi-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .pbi-kpi-label {{
            font-size: 11px !important;
            font-weight: 700 !important;
            color: #CCCCCC !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            font-family: 'Segoe UI', sans-serif !important;
        }}
        .pbi-kpi-val {{
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            font-family: 'Segoe UI', -apple-system, sans-serif !important;
            margin: 6px 0 2px 0 !important;
            line-height: 1.1 !important;
        }}
        .pbi-kpi-sub {{
            font-size: 11px !important;
            color: #A0A0A0 !important;
            font-weight: 500 !important;
        }}
        .pbi-pill-filter {{
            display: inline-block;
            background: #2E2E2E;
            color: #00BDAE !important;
            border: 1px solid #4A4A4A;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 4px;
        }}
        .pbi-visual-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333333;
            padding-bottom: 8px;
            margin-bottom: 12px;
        }}
        .pbi-visual-title {{
            font-size: 14px !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        .pbi-visual-actions {{
            color: #888888;
            font-size: 13px;
            display: flex;
            gap: 8px;
        }}
        </style>
    """, unsafe_allow_html=True)

def get_plotly_theme(fig):
    """Formats Plotly figure with dark carbon F1 racing palette."""
    fig.update_layout(
        paper_bgcolor=F1_CARD_BG,
        plot_bgcolor="#0F141C",
        font=dict(color="#E6EDF3", family="'Segoe UI', Roboto, sans-serif"),
        title=dict(font=dict(size=15, color="#FFFFFF")),
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(gridcolor="#21262D", zerolinecolor="#30363D"),
        yaxis=dict(gridcolor="#21262D", zerolinecolor="#30363D"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#30363D")
    )
    return fig

def get_pbi_plotly_theme(fig):
    """Formats Plotly figure with authentic Microsoft Power BI Dark Visual styling."""
    fig.update_layout(
        paper_bgcolor="#242424",
        plot_bgcolor="#1E1E1E",
        font=dict(color="#FFFFFF", family="'Segoe UI', -apple-system, sans-serif", size=11),
        title=dict(font=dict(size=14, color="#FFFFFF", family="'Segoe UI', sans-serif")),
        margin=dict(l=35, r=35, t=45, b=35),
        xaxis=dict(
            gridcolor="#333333",
            zerolinecolor="#4A4A4A",
            tickfont=dict(color="#CCCCCC", size=10)
        ),
        yaxis=dict(
            gridcolor="#333333",
            zerolinecolor="#4A4A4A",
            tickfont=dict(color="#CCCCCC", size=10)
        ),
        colorway=["#00BDAE", "#E10600", "#F2C811", "#118DFF", "#00E676", "#E66C37", "#A05BF5", "#8B949E"],
        legend=dict(
            bgcolor="rgba(36,36,36,0.85)",
            bordercolor="#383838",
            font=dict(color="#CCCCCC", size=10)
        )
    )
    return fig

def render_pbi_header(title: str, subtitle: str, page_name: str = "Page 1", filters_summary: str = ""):
    """Renders a Power BI Desktop / Service top ribbon bar."""
    st.markdown(f"""
        <div class="pbi-header-ribbon">
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #F2C811; color: #121212; padding: 2px 7px; border-radius: 3px; font-weight: 900; font-size: 11px; letter-spacing: 0.5px;">POWER BI</span>
                    <h2 style="margin: 0; color: #FFFFFF; font-size: 20px; font-weight: 700;">{title}</h2>
                </div>
                <div style="color: #A0A0A0; font-size: 12px; margin-top: 3px;">
                    {subtitle}
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: #2E2E2E; color: #00BDAE; border: 1px solid #4A4A4A; padding: 4px 12px; border-radius: 14px; font-size: 11px; font-weight: 600;">
                    📊 {page_name}
                </span>
                <div style="color: #00E676; font-size: 10px; margin-top: 4px; font-weight: 600;">
                    ● Slicers Connected &bull; Real-Time Cross-Filtering
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    if filters_summary:
        st.markdown(f"""
            <div style="background: #1A1A1A; border: 1px solid #333333; padding: 6px 14px; border-radius: 6px; margin-top: -10px; margin-bottom: 16px; font-size: 11px; color: #AAAAAA;">
                <b style="color: #F2C811;">Active Slicers:</b> {filters_summary}
            </div>
        """, unsafe_allow_html=True)

def render_pbi_kpi(label: str, value: str, delta: str = None, delta_color: str = "#00E676", subtext: str = "", accent: str = "#00BDAE", icon: str = "📊"):
    """Renders a high-contrast Power BI KPI Card visual."""
    delta_html = f'<span style="color: {delta_color}; font-size: 11px; font-weight: 700; margin-left: 8px;">{delta}</span>' if delta else ''
    st.markdown(f"""
        <div class="pbi-kpi-container" style="border-top-color: {accent};">
            <div class="pbi-kpi-header">
                <span class="pbi-kpi-label">{label}</span>
                <span style="font-size: 14px; opacity: 0.85;">{icon}</span>
            </div>
            <div>
                <div class="pbi-kpi-val" style="color: {accent};">
                    {value} {delta_html}
                </div>
                <div class="pbi-kpi-sub">{subtext}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_snowflake_session():
    """Returns active Snowpark session, local connector, or None."""
    # 1. Check for active Streamlit in Snowflake (SiS) context
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        if session:
            return ("snowpark", session)
    except Exception:
        pass

    # 2. Check for local connector using credentials in .env
    acc = os.getenv("SNOWFLAKE_ACCOUNT", "")
    usr = os.getenv("SNOWFLAKE_USER", "")
    pwd = os.getenv("SNOWFLAKE_PASSWORD", "")
    if acc and acc != "your_snowflake_account_identifier" and usr and pwd:
        try:
            import snowflake.connector
            conn = snowflake.connector.connect(
                user=usr,
                password=pwd,
                account=acc,
                warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "F1_WH"),
                database=os.getenv("SNOWFLAKE_DATABASE", "F1_PREDICTION_DB"),
                schema=os.getenv("SNOWFLAKE_SCHEMA", "CLEAN")
            )
            return ("connector", conn)
        except Exception:
            pass

    return ("offline", None)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes all DataFrame column names to lowercase and ensures target alias compatibility."""
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Bidirectional aliases for target and key columns
        alias_pairs = [
            ("is_win", "target_is_win"),
            ("is_podium", "target_is_podium"),
            ("finish_position", "target_finish_position"),
            ("is_points", "target_is_points"),
            ("is_dnf", "target_is_dnf"),
            ("qualifying_position", "grid_position"),
        ]
        for c1, c2 in alias_pairs:
            if c1 in df.columns and c2 not in df.columns:
                df[c2] = df[c1]
            elif c2 in df.columns and c1 not in df.columns:
                df[c1] = df[c2]
    return df

@st.cache_data(ttl=600)
def query_snowflake(sql_query: str) -> pd.DataFrame:
    """Executes SQL against Snowflake with column normalization, or falls back to local data."""
    conn_type, session = get_snowflake_session()
    
    if conn_type == "snowpark" and session:
        try:
            df = session.sql(sql_query).to_pandas()
            return normalize_columns(df)
        except Exception as e:
            st.warning(f"Snowpark SQL execution error: {e}. Falling back to cached data.")

    elif conn_type == "connector" and session:
        try:
            df = pd.read_sql(sql_query, session)
            return normalize_columns(df)
        except Exception as e:
            st.warning(f"Snowflake connector query error: {e}. Falling back to cached data.")

    # If session execution fails or is offline, return empty DataFrame rather than mismatched dataset
    return pd.DataFrame()

@st.cache_data
def get_local_data(filename: str) -> pd.DataFrame:
    """Loads CSV from data/ or reports/ safely across all candidate project directories."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "logic", "data", filename),
        os.path.join(os.path.dirname(__file__), "logic", "data", "processed", filename),
        os.path.join(os.path.dirname(__file__), "logic", "reports", filename),
        os.path.join(os.path.dirname(__file__), "jury", "1_Pattern_Matching", filename),
        os.path.join(os.path.dirname(__file__), "jury", "2_Classification_Comparison", filename),
        os.path.join(os.path.dirname(__file__), "jury", "3_Model_Classification_with_Performance_Metrics", filename),
        os.path.join(os.path.dirname(__file__), "jury", filename),
        os.path.join(os.path.dirname(__file__), "data", filename),
        os.path.join(os.path.dirname(__file__), "data", "processed", filename),
        os.path.join(os.path.dirname(__file__), "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", "processed", filename),
        os.path.join(os.path.dirname(__file__), "..", "reports", filename),
        os.path.join(os.path.dirname(__file__), "04_pattern_mining", filename),
        os.path.join(os.path.dirname(__file__), "..", filename)
    ]

    # Handle modeling master and features variations
    if "modeling_master" in filename or "race_lab_features" in filename.lower():
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"),
            os.path.join(os.path.dirname(__file__), "logic", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"),
            os.path.join(os.path.dirname(__file__), "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"),
            os.path.join(os.path.dirname(__file__), "data", "F1_RACE_LAB_FEATURES_1994_2024.csv"),
            os.path.join(os.path.dirname(__file__), "data", "clean_f1_modeling_master.csv"),
            os.path.join(os.path.dirname(__file__), "..", "data", "clean_f1_modeling_master.csv"),
        ])

    # Handle common filename variations
    if "association_rules" in filename:
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "jury", "1_Pattern_Matching", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "jury", "1_Pattern_Matching", "association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "logic", "reports", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "reports", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "04_pattern_mining", "association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "..", "ASSOC_RULES.csv")
        ])
    elif "frequent_itemsets" in filename:
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "jury", "1_Pattern_Matching", "f1_frequent_itemsets.csv"),
            os.path.join(os.path.dirname(__file__), "jury", "1_Pattern_Matching", "frequent_itemsets.csv"),
            os.path.join(os.path.dirname(__file__), "logic", "reports", "f1_frequent_itemsets.csv"),
            os.path.join(os.path.dirname(__file__), "reports", "f1_frequent_itemsets.csv"),
            os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", "f1_frequent_itemsets.csv")
        ])

    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, low_memory=False)
                if not df.empty:
                    return normalize_columns(df)
            except Exception:
                pass

    # Direct Snowflake warehouse fallbacks when file is absent from disk
    if "association_rules" in filename or "pattern_rules" in filename:
        try:
            df = query_snowflake("SELECT * FROM ML.ASSOCIATION_RULES")
            if not df.empty:
                return normalize_columns(df)
        except Exception:
            pass

    if "model_comparison" in filename:
        try:
            df = query_snowflake("SELECT * FROM ML.MODEL_COMPARISON")
            if not df.empty:
                return normalize_columns(df)
        except Exception:
            pass

    if "feature_importance" in filename:
        try:
            df = query_snowflake("SELECT * FROM ML.FEATURE_IMPORTANCE")
            if not df.empty:
                return normalize_columns(df)
        except Exception:
            pass

    # If clean_f1_modeling_master.csv is requested and not found locally, query Snowflake directly
    if "modeling_master" in filename or "race_lab_features" in filename.lower():
        try:
            df = query_snowflake("SELECT * FROM CLEAN.F1_MODELING_MASTER")
            if not df.empty:
                return normalize_columns(df)
        except Exception:
            pass

    return pd.DataFrame()

@st.cache_data
def get_local_json(filename: str) -> dict:
    """Loads JSON file from reports/ safely across candidate directories."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "logic", "reports", filename),
        os.path.join(os.path.dirname(__file__), "logic", "data", filename),
        os.path.join(os.path.dirname(__file__), "jury", "1_Pattern_Matching", filename),
        os.path.join(os.path.dirname(__file__), "jury", "2_Classification_Comparison", filename),
        os.path.join(os.path.dirname(__file__), "jury", "3_Model_Classification_with_Performance_Metrics", filename),
        os.path.join(os.path.dirname(__file__), "jury", filename),
        os.path.join(os.path.dirname(__file__), "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", filename),
        os.path.join(os.path.dirname(__file__), "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", filename)
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}
