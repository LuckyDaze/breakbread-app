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
# 1. Hide the Streamlit Menu, Header, and Footer via CSS
hide_st_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove the extra top white-space padding so the app sits flush */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. Hack the Browser Tab to permanently remove " · Streamlit" via JS
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
# 1. Safely load external CSS
css_path = "assets/custom_styles.css"
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    # Basic fallback theme so the app doesn't look completely broken if the file is missing
    st.markdown("""
    <style>
        .stApp { background-color: #000000; color: #FFFFFF; }
        h1, h2, h3 { color: #FE8B00 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Safely load the Logo
logo_path = "assets/BB_logo.png"
def display_logo(width=None, use_container_width=False):
    if os.path.exists(logo_path):
        st.image(logo_path, width=width, use_container_width=use_container_width)
    else:
        # Fallback text if the image isn't found
        st.markdown("<h1 style='text-align: center; color: #FE8B00; font-size: 3.5rem; font-weight: 700;'>Break Bread</h1>", unsafe_allow_html=True)


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
    ("app_nav_radio", "Dashboard"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------------
# Core App Functions
# ----------------------------
def ensure_demo_users():
    """Ensure demo users exist in session state."""
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
    """Get user by ID."""
    return st.session_state.users.get(user_id)

def find_user(identifier):
    """Find user by app_id or email."""
    if not identifier:
        return None
    identifier = identifier.strip().lower()
    for user in st.session_state.users.values():
        if user["app_id"].lower() == identifier or user["email"].lower() == identifier:
            return user
    return None

def fake_login(username=None, password=None):
    """Demo login."""
    user = find_user(username)
    if user and user.get("password") == password:
        return {"status": "SUCCESS", "user_id": user["user_id"]}
    elif user:
        return {"status": "ERROR", "message": "Invalid password"}
    else:
        return {"status": "ERROR", "message": "User not found"}

def logout():
    """Logout current user."""
    st.session_state.auth_user = None
    st.rerun()

def send_money(sender_id, recipient_identifier, amount, note=""):
    """Send money to another user."""
    recipient = find_user(recipient_identifier)
    if not recipient:
        return False, "Recipient not found"
    
    sender = get_user(sender_id)
    if not sender:
        return False, "Sender not found"
    
    if sender["balance"] < amount:
        return False, "Insufficient funds"
    
    # Deduct from sender
    sender["balance"] -= amount
    # Add to recipient  
    recipient["balance"] += amount
    
    # Record transaction
    transaction = {
        "transaction_id": uid(),
        "sender_id": sender_id,
        "recipient_id": recipient["user_id"],
        "amount": amount,
        "fee": 0.0,
        "note": note,
        "status": "completed",
        "ts": datetime.now()
    }
    st.session_state.transactions.append(transaction)
    
    return True, "Payment sent successfully"

def request_money(requestor_id, recipient_identifier, amount, note=""):
    """Request money from another user."""
    recipient = find_user(recipient_identifier)
    if not recipient:
        return False, "Recipient not found"
    
    request_data = {
        "request_id": uid(),
        "requestor_id": requestor_id,
        "recipient_id": recipient["user_id"],
        "amount": amount,
        "note": note,
        "status": "pending",
        "ts": datetime.now()
    }
    st.session_state.requests.append(request_data)
    return True, "Money request sent"

def simulate_paycheck(user_id):
    """Simulate paycheck deposit."""
    user = get_user(user_id)
    if not user:
        return False, "User not found"
    
    user["balance"] += 2000.0
    return True, "Paycheck deposited"

def toast_success(message):
    """Show success toast."""
    st.toast(f"✅ {message}")

def toast_info(message):
    """Show info toast."""
    st.toast(f"ℹ️ {message}")

def add_notification(message):
    """Add a notification."""
    notification = {
        "id": uid(),
        "message": message,
        "timestamp": datetime.now(),
        "read": False
    }
    st.session_state.notifications.append(notification)

# ----------------------------
# Investment Vehicle Functions
# ----------------------------
def get_stock_data(symbol, period="1mo"):
    """Fetch stock/ETF data."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        if len(hist) > 1:
            prev_price = hist['Close'].iloc[-2]
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100
        else:
            change = 0
            change_percent = 0
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent,
            'historical': hist,
            'source': 'Yahoo Finance',
            'last_updated': datetime.now()
        }
    except Exception as e:
        return None

def get_major_indices():
    """Get major indices data."""
    indices = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ', 
        '^DJI': 'Dow Jones'
    }
    
    results = []
    for symbol, name in indices.items():
        data = get_stock_data(symbol, '1d')
        if data:
            results.append({
                'name': name,
                'symbol': symbol,
                'price': data['current_price'],
                'change': data['change'],
                'change_percent': data['change_percent'],
                'source': data['source']
            })
        else:
            base_prices = {
                'S&P 500': 5000 + random.randint(-100, 100),
                'NASDAQ': 16000 + random.randint(-200, 200),
                'Dow Jones': 38000 + random.randint(-300, 300)
            }
            results.append({
                'name': name,
                'symbol': symbol,
                'price': base_prices[name],
                'change': random.uniform(-50, 50),
                'change_percent': random.uniform(-2, 2),
                'source': 'Yahoo Finance (Demo)'
            })
    
    return results

def get_crypto_data(coin_id="bitcoin", days=30):
    """Fetch cryptocurrency data."""
    try:
        symbol_map = {
            'bitcoin': 'BTC-USD',
            'ethereum': 'ETH-USD'
        }
        yahoo_symbol = symbol_map.get(coin_id, 'BTC-USD')
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period=f"{days}d")
        
        if not hist.empty:
            current_price = hist
