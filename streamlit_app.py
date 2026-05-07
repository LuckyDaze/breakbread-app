import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import yfinance as yf
import requests

# ----------------------------
# Page configuration (MUST BE FIRST)
# ----------------------------
st.set_page_config(
    page_title="Break Bread",
    page_icon="assets/Break Bread - Bread Only.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# THE FINTECH BRANDING FIX
# ----------------------------
hide_st_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #FE8B00 !important;
    }
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

components.html(
    """
    <script>
        const observer = new MutationObserver(function(mutations) {
            if (window.parent.document.title !== "Break Bread") {
                window.parent.document.title = "Break Bread";
            }
        });
        const titleElement = window.parent.document.querySelector("title");
        if (titleElement) {
            observer.observe(titleElement, { childList: true });
            window.parent.document.title = "Break Bread"; 
        }
    </script>
    """,
    height=0,
    width=0,
)

# ----------------------------
# Safe Asset Loaders
# ----------------------------
css_path = "assets/custom_styles.css"
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background-color: #000000; color: #FFFFFF; }
        h1, h2, h3 { color: #FE8B00 !important; }
    </style>
    """, unsafe_allow_html=True)

logo_path = "assets/BB_logo.png"
def display_logo(width=None, use_container_width=False):
    if os.path.exists(logo_path):
        st.image(
            logo_path, 
            width=width, 
            use_container_width=use_container_width
        )
    else:
        st.markdown(
            "<h1 style='text-align: center; color: #FE8B00; font-size: 3.5rem; font-weight: 700;'>Break Bread</h1>", 
            unsafe_allow_html=True
        )

# ----------------------------
# Utility Functions
# ----------------------------
def uid():
    return str(uuid.uuid4())[:8]

def format_money(amount):
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
    ("app_nav_radio", "Dashboard"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------------
# Core App Functions
# ----------------------------
def ensure_demo_users():
    if not st.session_state.users:
        demo_users = [
            {
                "user_id": "user_1",
                "app_id": "janedoe", 
                "email": "jane@example.com",
                "password": "demo123",
                "balance": 5000.0,
                "portfolio": {},
                "watchlist": [],
                "settings": {"dark_mode": False, "price_alerts": {}}
            },
            {
                "user_id": "user_2", 
                "app_id": "johndoe",
                "email": "john@example.com", 
                "password": "demo123",
                "balance": 3000.0,
                "portfolio": {},
                "watchlist": [],
                "settings": {"dark_mode": False, "price_alerts": {}}
            }
        ]
        for user in demo_users:
            st.session_state.users[user["user_id"]] = user

def get_user(user_id):
    return st.session_state.users.get(user_id)

def find_user(identifier):
    if not identifier:
        return None
    identifier = identifier.strip().lower()
    for user in st.session_state.users.values():
        if user["app_id"].lower() == identifier or user["email"].lower() == identifier:
            return user
    return None

def fake_login(username=None, password=None):
    user = find_user(username)
    if user and user.get("password") == password:
        return {"status": "SUCCESS", "user_id": user["user_id"]}
    elif user:
        return {"status": "ERROR", "message": "Invalid password"}
    else:
