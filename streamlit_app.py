import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import requests

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
# Market Data Functions
# ----------------------------
def get_stock_data(symbol, period="1mo"):
    """Fetch stock/ETF data with historical prices."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        # Calculate change from previous close
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
    """Get all major indices in one call."""
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
            # Fallback data
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
        # Use Yahoo Finance for crypto
        symbol_map = {
            'bitcoin': 'BTC-USD',
            'ethereum': 'ETH-USD'
        }
        yahoo_symbol = symbol_map.get(coin_id, 'BTC-USD')
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period=f"{days}d")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change_percent = ((current_price - prev_price) / prev_price) * 100
        else:
            current_price = 50000 if coin_id == 'bitcoin' else 3000
            change_percent = random.uniform(-5, 5)
            hist = None
        
        return {
            'symbol': coin_id.upper(),
            'current_price': current_price,
            'change_percent': change_percent,
            'historical': hist,
            'source': 'Yahoo Finance',
            'last_updated': datetime.now()
        }
    except:
        return get_crypto_demo_data(coin_id, days)

def get_crypto_prices():
    """Get multiple cryptocurrency prices quickly."""
    coins = ['bitcoin', 'ethereum']
    results = []
    
    for coin in coins:
        data = get_crypto_data(coin, 1)
        if data:
            symbol_map = {
                'bitcoin': 'BTC-USD',
                'ethereum': 'ETH-USD'
            }
            data['symbol'] = symbol_map.get(coin, coin.upper())
            results.append(data)
    
    return results

def get_crypto_demo_data(coin_id="bitcoin", days=30):
    """Fallback demo data for cryptocurrencies."""
    base_prices = {
        'bitcoin': 51234.56,
        'ethereum': 2890.12
    }
    
    return {
        'symbol': coin_id.upper(),
        'current_price': base_prices.get(coin_id, 1000),
        'change_percent': random.uniform(-5, 5),
        'historical': None,
        'source': 'Demo Data',
        'last_updated': datetime.now()
    }

def create_price_chart(historical_data, title, chart_type="line"):
    """Create a Plotly chart from historical data."""
    if historical_data is None or historical_data.empty:
        return None
        
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Close'],
        mode='lines',
        name=title,
        line=dict(color='#FE8B00')
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400,
        template="plotly_dark",
        showlegend=False
    )
    
    return fig

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
    ("quick_contact", None),
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

def fake_login(username=None, code=None):
    """Demo login with optional 2FA simulation."""
    if code and len(code) == 6 and code.isdigit():
        # 2FA verification - accept any 6-digit code in demo
        return {"status": "SUCCESS", "user_id": "user_1"}
    
    user = find_user(username)
    if user and user.get("password") == "demo123":
        return {"status": "SUCCESS", "user_id": user["user_id"]}
    elif user:
        return {"status": "2FA_REQUIRED", "message": "Enter any 6-digit code"}
    else:
        return {"status": "ERROR", "message": "User not found"}

def logout():
    """Logout current user."""
    st.session_state.auth_user = None

def fraud_check(transaction):
    """Basic fraud detection."""
    warnings = []
    if transaction["amount"] > 10000:
        warnings.append("Large transaction amount")
    return warnings

def break_bread(sender_id, recipient_identifier, amount, note=""):
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

def register_user(app_id, email, password, personal, banking, initial_deposit):
    """Register a new user."""
    if find_user(app_id) or find_user(email):
        return False, "User already exists", None
    
    user_id = f"user_{uid()}"
    new_user = {
        "user_id": user_id,
        "app_id": app_id,
        "email": email,
        "password": password,
        "balance": float(initial_deposit),
        "portfolio": {},
        "watchlist": [],
        "settings": {"dark_mode": False, "price_alerts": {}},
        "personal": personal,
        "banking": banking
    }
    
    st.session_state.users[user_id] = new_user
    return True, "Registration successful", user_id

def get_cached_data(symbol, period="1mo"):
    """Get market data with caching."""
    return get_stock_data(symbol, period)

def mini_indices():
    """Get major indices data."""
    indices_data = get_major_indices()
    return [
        {
            "name": idx["name"],
            "price": idx["price"],
            "chg_pct": idx["change_percent"]
        }
        for idx in indices_data
    ]

def place_order(user_id, symbol, side, cash_amount=None, units=None):
    """Place a trading order."""
    user = get_user(user_id)
    if not user:
        return False, "User not found", None
    
    data = get_cached_data(symbol, "1d")
    if not data:
        return False, "Invalid symbol", None
    
    current_price = data["current_price"]
    
    if side == "buy":
        if cash_amount is None:
            return False, "Cash amount required for buy orders", None
        
        units = cash_amount / current_price
        total_cost = cash_amount
        
        if user["balance"] < total_cost:
            return False, "Insufficient funds", None
        
        user["balance"] -= total_cost
        
    else:  # sell
        if units is None:
            return False, "Units required for sell orders", None
        
        portfolio_units = user["portfolio"].get(symbol, {}).get("units", 0)
        if units > portfolio_units:
            return False, "Insufficient units", None
        
        total_cost = units * current_price
        user["balance"] += total_cost
    
    # Update portfolio
    if symbol not in user["portfolio"]:
        user["portfolio"][symbol] = {"units": 0, "avg_cost": 0}
    
    if side == "buy":
        old_units = user["portfolio"][symbol]["units"]
        old_avg = user["portfolio"][symbol]["avg_cost"]
        new_units = old_units + units
        new_avg = ((old_units * old_avg) + (units * current_price)) / new_units
        
        user["portfolio"][symbol]["units"] = new_units
        user["portfolio"][symbol]["avg_cost"] = new_avg
    else:
        user["portfolio"][symbol]["units"] -= units
        if user["portfolio"][symbol]["units"] <= 0:
            del user["portfolio"][symbol]
    
    # Record order
    order = {
        "order_id": uid(),
        "user_id": user_id,
        "symbol": symbol,
        "side": side,
        "units": units,
        "fill_price": current_price,
        "value": total_cost,
        "status": "filled",
        "ts": datetime.now()
    }
    st.session_state.orders.append(order)
    
    return True, "Order executed successfully", order

def portfolio_value(user_id):
    """Calculate total portfolio value."""
    user = get_user(user_id)
    if not user:
        return 0
    
    total = 0
    for symbol, position in user["portfolio"].items():
        data = get_cached_data(symbol, "1d")
        if data:
            total += position["units"] * data["current_price"]
    return total

def unrealized_gains(user_id):
    """Calculate unrealized gains/losses."""
    user = get_user(user_id)
    if not user:
        return 0
    
    total = 0
    for symbol, position in user["portfolio"].items():
        data = get_cached_data(symbol, "1d")
        if data:
            current_value = position["units"] * data["current_price"]
            cost_basis = position["units"] * position["avg_cost"]
            total += current_value - cost_basis
    return total

def diversification_score(user_id):
    """Calculate diversification score (simplified)."""
    user = get_user(user_id)
    if not user or not user["portfolio"]:
        return 0
    
    # Simple score based on number of holdings
    num_holdings = len(user["portfolio"])
    return min(num_holdings * 20, 100)

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
# UI Components
# ----------------------------
def _clean_symbol(text: str) -> str:
    """Normalize ticker inputs."""
    return (text or "").strip().upper()

def show_login():
    # Centered logo on login page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/breakbread-logo.png", width=400)
        st.markdown("<h1 style='text-align: center; color: #FE8B00; font-size: 3.5rem; font-weight: 700;'>Break Bread</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #FFFFFF; margin-bottom: 3rem;'>Build Wealth Together</h3>", unsafe_allow_html=True)
    
    st.header("Welcome to Break Bread")

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.subheader("Login")
            username = st.text_input("Username (App ID)", key="login_username", placeholder="janedoe or johndoe")
            password = st.text_input("Password", type="password", key="login_password", value="demo123")
            
            if st.button("Login", type="primary", key="login_btn"):
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    result = fake_login(username, password)
                    
                    if isinstance(result, dict):
                        status = result.get("status")
                        if status == "SUCCESS":
                            st.session_state.auth_user = result["user_id"]
                            user = get_user(result["user_id"])
                            if user and not user.get("watchlist") and len(user.get("portfolio", {})) <= 1:
                                user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                                add_notification("🎯 Starter watchlist added! Check out popular stocks & crypto.")
                            toast_success("Login successful!")
                            st.rerun()
                        elif status == "2FA_REQUIRED":
                            st.info("2FA required. Enter any 6-digit code on the right (demo).")
                        else:
                            st.error(result.get("message", "Login failed"))
                    else:
                        st.error("Login failed")

        with col2:
            st.subheader("Enter 2FA Code")
            code = st.text_input("6-digit code", placeholder="123456", key="login_2fa_code_input_tab")
            
            if st.button("Verify Code", key="verify_2fa_btn_tab"):
                if not code or len(code) != 6 or not code.isdigit():
                    st.error("Please enter a valid 6-digit code")
                else:
                    verify = fake_login(code=code)
                    if isinstance(verify, dict) and verify.get("status") == "SUCCESS":
                        st.session_state.auth_user = verify["user_id"]
                        user = get_user(verify["user_id"])
                        if user and not user.get("watchlist") and len(user.get("portfolio", {})) <= 1:
                            user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                            add_notification("🎯 Starter watchlist added! Check out popular stocks & crypto.")
                        toast_success("Login successful!")
                        st.rerun()
                    else:
                        msg = verify.get("message", "Invalid code") if isinstance(verify, dict) else "Invalid code"
                        st.error(msg)

    with tab_signup:
        st.subheader("Create your account (Demo)")
        with st.form("signup_form", clear_on_submit=True):
            st.markdown("**Account**")
            app_id = st.text_input("Username (App ID)", placeholder="yourhandle", key="su_appid")
            email = st.text_input("Email", placeholder="you@example.com", key="su_email")
            password = st.text_input("Password", type="password", key="su_password")

            st.markdown("---")
            st.markdown("**Personal Information**")
            full_name = st.text_input("Full Name", key="su_fullname")
            phone = st.text_input("Phone", key="su_phone")
            dob = st.date_input("Date of Birth", key="su_dob", max_value=datetime.now().date())
            address = st.text_input("Address", key="su_address")
            ssn_last4 = st.text_input("SSN (last 4) — demo only", max_chars=4, key="su_ssn4")

            st.markdown("---")
            st.markdown("**Banking Information** (demo only — do not use real numbers)")
            bank_account = st.text_input("Bank Account Number", key="su_bank_acct", value="123456789")
            bank_routing = st.text_input("Routing Number", key="su_bank_routing", value="021000021")
            initial_deposit = st.number_input("Initial Deposit ($)", min_value=0.0, value=100.0, step=50.0, key="su_init_dep")

            agreed = st.checkbox("I understand this is a demo and not a real bank.", value=True, key="su_agree")
            submitted = st.form_submit_button("Create Account", type="primary", key="su_submit")

            if submitted:
                if not agreed:
                    st.warning("Please acknowledge this is a demo.")
                elif not app_id or not email or not password:
                    st.warning("Please fill in all required account fields.")
                else:
                    personal = {
                        "full_name": full_name, 
                        "phone": phone, 
                        "dob": str(dob),
                        "address": address, 
                        "ssn_last4": ssn_last4,
                    }
                    banking = {
                        "account_number": bank_account, 
                        "routing_number": bank_routing
                    }
                    
                    ok, msg, user_id = register_user(
                        app_id=app_id, 
                        email=email, 
                        password=password,
                        personal=personal, 
                        banking=banking, 
                        initial_deposit=initial_deposit,
                    )
                    
                    if ok:
                        toast_success(msg)
                        add_notification(f"🎉 Welcome {app_id}! Account created with ${initial_deposit:.2f} initial deposit.")
                        st.success("Account created successfully! You can now log in with your credentials.")
                        st.balloons()
                    else:
                        st.error(msg)

def show_main_app():
    user = get_user(st.session_state.auth_user)
    if not user:
        logout()
        st.rerun()

    with st.sidebar:
        # User profile section with logo
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #FE8B00 0%, #FF9A2D 100%);
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 16px rgba(254, 139, 0, 0.3);
        '>
        """, unsafe_allow_html=True)
        
        # Logo in sidebar
        st.image("assets/breakbread-logo.png", width=80)
        
        st.markdown(f"""
            <h3 style='color: #000000; margin: 0.5rem 0 0.25rem 0; font-weight: 600;'>{user['app_id']}</h3>
            <p style='color: #000000; margin: 0; opacity: 0.8; font-size: 0.9rem;'>Break Bread Member</p>
        </div>
        """, unsafe_allow_html=True)

        # Balance card
        st.markdown(f"""
        <div style='
            background-color: #1A1A1A;
            padding: 1.25rem;
            border-radius: 16px;
            border: 1px solid #333;
            margin-bottom: 1.5rem;
        '>
            <p style='color: #888; margin: 0; font-size: 0.9rem; font-weight: 500;'>Available Cash</p>
            <h3 style='color: #FE8B00; margin: 0.5rem 0; font-size: 1.5rem; font-weight: 600;'>{format_money(user["balance"])}</h3>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("""
        <div style='margin-bottom: 1rem;'>
            <h4 style='color: #FFFFFF; margin: 0; font-weight: 600;'>Navigation</h4>
        </div>
        """, unsafe_allow_html=True)
        
        nav_options = [
            ("🏠 Dashboard", "Dashboard"),
            ("💸 Banking", "Banking"), 
            ("📈 Markets", "Markets"),
            ("💼 Portfolio", "Portfolio"),
            ("⚙️ Settings", "Settings")
        ]
        
        for icon_label, value in nav_options:
            if st.button(f"**{icon_label}**", 
                        key=f"nav_{value}", 
                        use_container_width=True,
                        type="primary" if st.session_state.get("app_nav_radio") == value else "secondary"):
                st.session_state.app_nav_radio = value
                st.rerun()

        # Market Overview
        st.markdown("---")
        st.markdown("""
        <div style='margin: 1rem 0;'>
            <h4 style='color: #FFFFFF; margin: 0 0 1rem 0; font-weight: 600;'>Market Overview</h4>
        </div>
        """, unsafe_allow_html=True)
        
        indices = mini_indices()
        for index in indices[:3]:
            change_color = "#00D54B" if index["chg_pct"] >= 0 else "#FF4444"
            st.markdown(f"""
            <div style='
                background-color: #1A1A1A;
                padding: 1rem;
                border-radius: 12px;
                border: 1px solid #333;
                margin-bottom: 0.5rem;
            '>
                <div style='display: flex; justify-content: between; align-items: center;'>
                    <span style='color: #FFFFFF; font-weight: 500;'>{index['name']}</span>
                    <div style='text-align: right;'>
                        <div style='color: #FFFFFF; font-weight: 600;'>{format_money(index['price'])}</div>
                        <div style='color: {change_color}; font-size: 0.8rem; font-weight: 500;'>{index['chg_pct']:+.2f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Logout button
        st.markdown("---")
        if st.button("**🚪 Logout**", use_container_width=True, type="secondary"):
            logout()
            st.rerun()

    # Main content area based on navigation
    if st.session_state.get("app_nav_radio") == "Dashboard":
        show_dashboard(user)
    elif st.session_state.get("app_nav_radio") == "Banking":
        show_banking(user)
    elif st.session_state.get("app_nav_radio") == "Markets":
        show_markets(user)
    elif st.session_state.get("app_nav_radio") == "Portfolio":
        show_portfolio(user)
    elif st.session_state.get("app_nav_radio") == "Settings":
        show_settings(user)
    else:
        show_dashboard(user)

# ADD THE MISSING FUNCTIONS

def show_dashboard(user):
    """Show the main dashboard."""
    st.header("Dashboard")
    
    # Header with balance
    total_balance = portfolio_value(user["user_id"]) + user["balance"]
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #FE8B00 0%, #FF9A2D 100%);
            padding: 2.5rem;
            border-radius: 24px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(254, 139, 0, 0.3);
        '>
            <h3 style='color: #000000; margin: 0; font-size: 1.1rem; font-weight: 600; opacity: 0.9;'>TOTAL BALANCE</h3>
            <h1 style='color: #000000; margin: 1rem 0; font-size: 3rem; font-weight: 700; letter-spacing: -0.02em;'>{format_money(total_balance)}</h1>
            <div style='
                display: inline-block;
                background: rgba(0, 0, 0, 0.2);
                padding: 8px 16px;
                border-radius: 20px;
                margin-top: 0.5rem;
            '>
                <p style='color: #000000; margin: 0; font-size: 0.9rem; font-weight: 600;'>Break Bread</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Quick Actions
        # Quick Actions
    st.subheader("Quick Actions")
    actions_col1, actions_col2, actions_col3, actions_col4 = st.columns(4)
    
    with actions_col1:
        if st.button("💸 Send Money", use_container_width=True):
            st.session_state.app_nav_radio = "Banking"
            st.rerun()
    
    with actions_col2:
        if st.button("📈 Invest", use_container_width=True):
            st.session_state.app_nav_radio = "Markets"
            st.rerun()
    
    with actions_col3:
        if st.button("💰 Deposit", use_container_width=True, type="primary"):
            ok, _ = simulate_paycheck(user["user_id"])
            if ok:
                toast_success("💰 $2,000 added to your balance!")
                st.rerun()
