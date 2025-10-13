import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import requests

# Apply Break Bread Orange Theme CSS
st.markdown("""
<style>
    /* Break Bread Orange Theme */
    :root {
        --bb-orange: #FE8B00;
        --bb-orange-light: #FF9A2D;
        --bb-orange-dark: #E67A00;
        --bb-black: #000000;
        --bb-dark-gray: #1A1A1A;
        --bb-darker-gray: #111111;
        --bb-light-gray: #F5F5F5;
        --bb-white: #FFFFFF;
        --bb-text-secondary: #888888;
    }
    
    .main {
        background-color: var(--bb-black);
        color: var(--bb-white);
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bb-black) 0%, var(--bb-darker-gray) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--bb-white) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Metrics and Cards */
    [data-testid="stMetric"] {
        background-color: var(--bb-dark-gray);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #333;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    [data-testid="stMetricValue"] {
        color: var(--bb-white) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--bb-text-secondary) !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: inherit !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: var(--bb-orange) !important;
        color: var(--bb-black) !important;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 14px 28px;
        font-size: 16px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(254, 139, 0, 0.3);
    }
    
    .stButton button:hover {
        background-color: var(--bb-orange-light) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(254, 139, 0, 0.4);
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* Secondary Buttons */
    .stButton button[kind="secondary"] {
        background-color: var(--bb-dark-gray) !important;
        color: var(--bb-white) !important;
        border: 1px solid #333;
        box-shadow: none;
    }
    
    .stButton button[kind="secondary"]:hover {
        background-color: #2A2A2A !important;
        border-color: #444;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: var(--bb-darker-gray);
        border-right: 1px solid #333;
    }
    
    /* Input Fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: var(--bb-dark-gray);
        border: 1px solid #333;
        border-radius: 12px;
        color: var(--bb-white);
        padding: 12px 16px;
        font-size: 16px;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: var(--bb-orange);
        box-shadow: 0 0 0 2px rgba(254, 139, 0, 0.2);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bb-dark-gray);
        gap: 8px;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: var(--bb-text-secondary) !important;
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--bb-orange) !important;
        color: var(--bb-black) !important;
        font-weight: 600;
    }
    
    /* Dataframes */
    .dataframe {
        background-color: var(--bb-dark-gray) !important;
        border-radius: 12px;
        border: 1px solid #333;
    }
    
    /* Dividers */
    .stDivider {
        border-color: #333;
    }
    
    /* Toast notifications */
    .stToast {
        background-color: var(--bb-dark-gray) !important;
        border: 1px solid #333;
        border-radius: 12px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bb-dark-gray);
        border: 1px solid #333;
        border-radius: 12px;
    }
    
    /* Radio buttons */
    .stRadio [role="radiogroup"] {
        background-color: var(--bb-dark-gray);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 8px;
    }
    
    .stRadio [role="radio"] {
        background-color: transparent !important;
        color: var(--bb-white) !important;
    }
    
    .stRadio [role="radio"][aria-checked="true"] {
        background-color: var(--bb-orange) !important;
        color: var(--bb-black) !important;
        border-radius: 8px;
    }
    
    /* Fix text colors */
    .stText, .stMarkdown, p, div, span {
        color: var(--bb-white) !important;
    }
    
    /* Fix selectbox text */
    .stSelectbox div[data-baseweb="select"] div {
        color: var(--bb-white) !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Page configuration
# ----------------------------
st.set_page_config(
    page_title="Break Bread",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# Utility Functions
# ----------------------------
def uid():
    """Generate a unique ID."""
    return str(uuid.uuid4())[:8]

def format_money(amount):
    """Format money with dollar sign and 2 decimal places."""
    if amount >= 0:
        return f"${amount:,.2f}"
    else:
        return f"-${abs(amount):,.2f}"

# ----------------------------
# Initialize session state
# ----------------------------
for key, default in [
    ("users", {}),
    ("transactions", []),
    ("orders", []),
    ("requests", []),
    ("auth_user", None),
    ("notifications", []),
   
