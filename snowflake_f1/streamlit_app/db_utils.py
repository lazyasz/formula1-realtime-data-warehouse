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
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

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
        </style>
    """, unsafe_allow_html=True)

def get_plotly_theme(fig):
    """Formats Plotly figure with dark carbon F1 racing palette."""
    fig.update_layout(
        paper_bgcolor=F1_CARD_BG,
        plot_bgcolor="#0F141C",
        font=dict(color="#E6EDF3", family="'Segoe UI', Roboto, sans-serif"),
        title=dict(font=dict(size=16, color="#FFFFFF")),
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(gridcolor="#21262D", zerolinecolor="#30363D"),
        yaxis=dict(gridcolor="#21262D", zerolinecolor="#30363D"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#30363D")
    )
    return fig

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
    """Standardizes all DataFrame column names to lowercase for seamless cross-compatibility."""
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
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

    # Fallback to local clean master dataset
    return get_local_data("clean_f1_modeling_master.csv")

@st.cache_data
def get_local_data(filename: str) -> pd.DataFrame:
    """Loads CSV from data/ or reports/ safely across all candidate project directories."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "data", filename),
        os.path.join(os.path.dirname(__file__), "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "reports", filename),
        os.path.join(os.path.dirname(__file__), "04_pattern_mining", filename),
        os.path.join(os.path.dirname(__file__), "..", filename)
    ]

    # Handle common filename variations
    if "association_rules" in filename:
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "reports", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "04_pattern_mining", "association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "..", "ASSOC_RULES.csv")
        ])
    elif "frequent_itemsets" in filename:
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "reports", "f1_frequent_itemsets.csv"),
            os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", "f1_frequent_itemsets.csv")
        ])

    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, low_memory=False)
                return normalize_columns(df)
            except Exception:
                pass

    # If clean_f1_modeling_master.csv is requested and not found locally, query Snowflake directly
    if "modeling_master" in filename:
        try:
            return query_snowflake("SELECT * FROM CLEAN.F1_MODELING_MASTER")
        except Exception:
            pass

    return pd.DataFrame()

@st.cache_data
def get_local_json(filename: str) -> dict:
    """Loads JSON file from reports/ safely across candidate directories."""
    candidates = [
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
