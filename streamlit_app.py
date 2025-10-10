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
    page_icon="assets/favicon.png",  # Using emoji as fallback
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

def seed_price_path(base_value, days, volatility=0.02):
    """Generate simulated price path for charts."""
    prices = [base_value]
    for _ in range(days - 1):
        change = random.uniform(-volatility, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    return prices

# ----------------------------
# Enhanced Market Data Functions
# ----------------------------
def get_stock_data(symbol, period="1mo"):
    """Fetch stock/ETF data with historical prices."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
            
        info = ticker.info
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
            '52w_high': info.get('fiftyTwoWeekHigh', current_price * 1.2),
            '52w_low': info.get('fiftyTwoWeekLow', current_price * 0.8),
            'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0,
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
        '^DJI': 'Dow Jones',
        '^RUT': 'Russell 2000'
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
                'Dow Jones': 38000 + random.randint(-300, 300),
                'Russell 2000': 2000 + random.randint(-50, 50)
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

def get_treasury_yields():
    """Fetch latest Treasury yields with historical context."""
    try:
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"
        params = {
            'filter': 'security_desc:eq:Treasury Notes',
            'sort': '-record_date',
            'page[size]': '5'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'data' in data and data['data']:
            latest = data['data'][0]
            base_rate = float(latest.get('avg_interest_rate_amt', 4.5))
            
            return {
                '1_month': base_rate,
                '2_year': base_rate + 0.4,
                '10_year': base_rate + 1.0,
                'source': 'U.S. Treasury FiscalData API',
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
        else:
            return get_treasury_demo_data()
            
    except Exception as e:
        return get_treasury_demo_data()

def get_treasury_demo_data():
    """Fallback demo data for Treasury yields."""
    return {
        '1_month': 5.32,
        '2_year': 4.89,
        '10_year': 4.45,
        'source': 'U.S. Treasury (Demo Data)',
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    }

def get_crypto_data(coin_id="bitcoin", days=30):
    """Fetch cryptocurrency data with historical prices."""
    try:
        # Current price and market data
        price_url = "https://api.coingecko.com/api/v3/simple/price"
        price_params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        
        response = requests.get(price_url, params=price_params, timeout=10)
        
        if response.status_code == 200:
            price_data = response.json()[coin_id]
            
            # Get historical data from Yahoo Finance as fallback
            symbol_map = {
                'bitcoin': 'BTC-USD',
                'ethereum': 'ETH-USD'
            }
            yahoo_symbol = symbol_map.get(coin_id, 'BTC-USD')
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=f"{days}d")
            
            return {
                'symbol': coin_id.upper(),
                'current_price': price_data['usd'],
                'change_percent': price_data.get('usd_24h_change', 0),
                'historical': hist,
                'source': 'CoinGecko API + Yahoo Finance',
                'last_updated': datetime.now()
            }
        else:
            return get_crypto_demo_data(coin_id, days)
            
    except Exception as e:
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
    
    base_price = base_prices.get(coin_id, 1000)
    
    # Generate historical data using yfinance as fallback
    symbol_map = {
        'bitcoin': 'BTC-USD',
        'ethereum': 'ETH-USD'
    }
    yahoo_symbol = symbol_map.get(coin_id, 'BTC-USD')
    
    try:
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period=f"{days}d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change_percent = ((current_price - prev_price) / prev_price) * 100
        else:
            current_price = base_price
            change_percent = random.uniform(-5, 5)
            hist = None
    except:
        current_price = base_price
        change_percent = random.uniform(-5, 5)
        hist = None
    
    return {
        'symbol': symbol_map.get(coin_id, coin_id.upper()),
        'current_price': current_price,
        'change_percent': change_percent,
        'historical': hist,
        'source': 'Demo Data',
        'last_updated': datetime.now()
    }

def get_metals_prices():
    """Get precious metals prices."""
    try:
        # Try Yahoo Finance for metals
        metals = {
            'GC=F': {'name': 'Gold', 'demo_price': 1987.65},
            'SI=F': {'name': 'Silver', 'demo_price': 23.45},
            'PL=F': {'name': 'Platinum', 'demo_price': 987.32}
        }
        
        results = {}
        for symbol, info in metals.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    source = 'Yahoo Finance'
                else:
                    price = info['demo_price']
                    source = 'Demo Data'
            except:
                price = info['demo_price']
                source = 'Demo Data'
            
            results[info['name'].lower()] = {
                'price': price,
                'source': source,
                'last_updated': datetime.now()
            }
        
        return results
        
    except Exception as e:
        # Fallback to demo data
        return {
            'gold': {'price': 1987.65, 'source': 'Demo Data', 'last_updated': datetime.now()},
            'silver': {'price': 23.45, 'source': 'Demo Data', 'last_updated': datetime.now()},
            'platinum': {'price': 987.32, 'source': 'Demo Data', 'last_updated': datetime.now()}
        }

def create_price_chart(historical_data, title, chart_type="line"):
    """Create a Plotly chart from historical data."""
    if historical_data is None or historical_data.empty:
        return None
        
    fig = go.Figure()
    
    if chart_type == "candlestick" and all(col in historical_data.columns for col in ['Open', 'High', 'Low', 'Close']):
        fig.add_trace(go.Candlestick(
            x=historical_data.index,
            open=historical_data['Open'],
            high=historical_data['High'],
            low=historical_data['Low'],
            close=historical_data['Close'],
            name=title
        ))
    else:
        # Line chart for simple close prices
        fig.add_trace(go.Scatter(
            x=historical_data.index,
            y=historical_data['Close'],
            mode='lines',
            name=title,
            line=dict(color='#1f77b4')
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400,
        template="plotly_white",
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
    # Convert to old format for compatibility
    return [
        {
            "name": idx["name"],
            "price": idx["price"],
            "chg_pct": idx["change_percent"]
        }
        for idx in indices_data
    ]

def chart(historical_data, symbol, chart_type="line"):
    """Create a chart from historical data."""
    return create_price_chart(historical_data, f"{symbol} Price", chart_type)

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

def toast_warn(message):
    """Show warning toast."""
    st.toast(f"⚠️ {message}")

def add_notification(message):
    """Add a notification."""
    notification = {
        "id": uid(),
        "message": message,
        "timestamp": datetime.now(),
        "read": False
    }
    st.session_state.notifications.append(notification)

def get_notifications():
    """Get all notifications."""
    return st.session_state.notifications

def price_alerts_tick(user):
    """Check price alerts (simplified)."""
    # This would normally check current prices against alert thresholds
    pass

# ----------------------------
# UI Components
# ----------------------------
def _clean_symbol(text: str) -> str:
    """Normalize ticker inputs."""
    return (text or "").strip().upper()

def show_login():
    # ADDED LOGO CODE HERE - This is the right place for it
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Display your logo image
        st.image("assets/breakbread-logo.png", width=512)  # Reduced width for better fit
        st.markdown("<h3 style='text-align: center; font-size:36px;'><b><i>Break Bread. Build Wealth.</i></b></h3>", unsafe_allow_html=True)
    
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
        # User profile section
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #FE8B00 0%, #FF9A2D 100%);
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 16px rgba(254, 139, 0, 0.3);
        '>
            <div style='
                background: rgba(0, 0, 0, 0.2);
                padding: 8px;
                border-radius: 12px;
                display: inline-block;
                margin-bottom: 0.5rem;
            '>
                <img src="https://breakbread-app-2yphdh8ckmnctashqklne5.streamlit.app/favicon.ico" width="24" style='border-radius: 6px;'>
            </div>
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
        for index in indices[:3]:  # Show first 3 indices
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
        show_dashboard(user)  # Default to dashboard

def show_dashboard(user):
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

    # Quick Actions - Break Bread Style
    st.markdown("""
    <div style='margin-bottom: 1rem;'>
        <h3 style='color: #FFFFFF; margin-bottom: 1rem;'>Quick Actions</h3>
    </div>
    """, unsafe_allow_html=True)
    
    actions_col1, actions_col2, actions_col3, actions_col4 = st.columns(4)
    
    with actions_col1:
        if st.button("**💸 Send**", use_container_width=True, help="Send money to friends"):
            st.session_state.app_nav_radio = "Banking"
            st.rerun()
    
    with actions_col2:
        if st.button("**📈 Invest**", use_container_width=True, help="Explore investments"):
            st.session_state.app_nav_radio = "Markets"
            st.rerun()
    
    with actions_col3:
        if st.button("**💰 Paycheck**", use_container_width=True, help="Simulate paycheck"):
            ok, _ = simulate_paycheck(user["user_id"])
            if ok:
                toast_success("💰 Paycheck deposited!")
                st.rerun()
    
    with actions_col4:
        if st.button("**💳 Cards**", use_container_width=True, help="Manage cards (Coming Soon)"):
            toast_info("💳 Card management coming soon!")

    # Portfolio Metrics - Dark Cards
    st.markdown("""
    <div style='margin: 2rem 0 1rem 0;'>
        <h3 style='color: #FFFFFF; margin-bottom: 1rem;'>Portfolio Overview</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        portfolio_val = portfolio_value(user["user_id"])
        st.markdown(f"""
        <div style='
            background-color: #1A1A1A;
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid #333;
            height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <p style='color: #888; margin: 0; font-size: 0.9rem; font-weight: 500;'>Portfolio Value</p>
            <h3 style='color: #FFFFFF; margin: 0.5rem 0; font-size: 1.4rem; font-weight: 600;'>{format_money(portfolio_val)}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        unrealized = unrealized_gains(user["user_id"])
        color = "#00D54B" if unrealized >= 0 else "#FF4444"
        st.markdown(f"""
        <div style='
            background-color: #1A1A1A;
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid #333;
            height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <p style='color: #888; margin: 0; font-size: 0.9rem; font-weight: 500;'>Today's P/L</p>
            <h3 style='color: {color}; margin: 0.5rem 0; font-size: 1.4rem; font-weight: 600;'>{format_money(unrealized)}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        div_score = diversification_score(user["user_id"])
        score_color = "#FE8B00" if div_score >= 70 else "#FF9A2D" if div_score >= 40 else "#FF4444"
        st.markdown(f"""
        <div style='
            background-color: #1A1A1A;
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid #333;
            height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <p style='color: #888; margin: 0; font-size: 0.9rem; font-weight: 500;'>Diversity Score</p>
            <h3 style='color: {score_color}; margin: 0.5rem 0; font-size: 1.4rem; font-weight: 600;'>{div_score}/100</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        recent_tx = len([t for t in st.session_state.transactions if t["sender_id"] == user["user_id"] and (datetime.now() - t["ts"]).days <= 7])
        st.markdown(f"""
        <div style='
            background-color: #1A1A1A;
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid #333;
            height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <p style='color: #888; margin: 0; font-size: 0.9rem; font-weight: 500;'>Weekly Activity</p>
            <h3 style='color: #FFFFFF; margin: 0.5rem 0; font-size: 1.4rem; font-weight: 600;'>{recent_tx}</h3>
        </div>
        """, unsafe_allow_html=True)

    # Recent Activity
    st.markdown("""
    <div style='margin: 2rem 0 1rem 0;'>
        <h3 style='color: #FFFFFF; margin-bottom: 1rem;'>Recent Activity</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Get recent transactions for this user
    user_activities = []
    recent_transactions = [t for t in st.session_state.transactions 
                          if t["sender_id"] == user["user_id"] or t["recipient_id"] == user["user_id"]]
    recent_transactions.sort(key=lambda x: x["ts"], reverse=True)
    
    for tx in recent_transactions[:5]:  # Show last 5 transactions
        if tx["sender_id"] == user["user_id"]:
            activity_type = "Sent"
            amount = f"-{format_money(tx['amount'])}"
            color = "#FF4444"
        else:
            activity_type = "Received" 
            amount = f"+{format_money(tx['amount'])}"
            color = "#00D54B"
        
        user_activities.append({
            "Type": activity_type,
            "Amount": amount,
            "Date": tx["ts"].strftime("%m/%d/%Y"),
            "Note": tx.get("note", "")
        })

    if user_activities:
        # Create a styled dataframe
        df = pd.DataFrame(user_activities)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent activity. Start by sending money or making investments!")

def show_banking(user):
    # Break Bread Style Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            border: 1px solid #333;
        '>
            <h3 style='color: #FFFFFF; margin: 0 0 0.5rem 0; font-weight: 600;'>Available Balance</h3>
            <h1 style='color: #FE8B00; margin: 0; font-size: 2.8rem; font-weight: 700;'>{format_money(user["balance"])}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("**+ Add Cash**\n\n💵", use_container_width=True, type="primary"):
            ok, _ = simulate_paycheck(user["user_id"])
            if ok:
                toast_success("💰 $2,000 added to your balance!")
                st.rerun()

    # Tabs with Break Bread styling
    tab1, tab2, tab3 = st.tabs(["💸 **Send**", "📥 **Request**", "📊 **History**"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Send Money")
            recipient = st.text_input("Recipient (Username or Email)", key="send_recipient")
            amount = st.number_input("Amount ($)", min_value=0.01, value=10.0, key="send_amount")
            note = st.text_input("Note (Optional)", key="send_note")
            
            if st.button("Send Payment", type="primary", key="send_btn"):
                if not recipient:
                    st.error("Please enter a recipient")
                elif amount > user["balance"]:
                    st.error("Insufficient funds")
                else:
                    ok, msg = send_money(user["user_id"], recipient, amount, note)
                    if ok:
                        toast_success(msg)
                        add_notification(f"💸 Sent {format_money(amount)} to {recipient}")
                        st.rerun()
                    else:
                        st.error(msg)
        
        with col2:
            st.subheader("Quick Send")
            demo_users = [u for u in st.session_state.users.values() if u["user_id"] != user["user_id"]]
            for demo_user in demo_users[:2]:
                if st.button(f"Send $10 to {demo_user['app_id']}", key=f"quick_send_{demo_user['user_id']}"):
                    ok, msg = send_money(user["user_id"], demo_user["app_id"], 10.0, "Quick send")
                    if ok:
                        toast_success(f"Sent $10 to {demo_user['app_id']}")
                        st.rerun()
                    else:
                        st.error(msg)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Request Money")
            request_recipient = st.text_input("From (Username or Email)", key="request_recipient")
            request_amount = st.number_input("Amount ($)", min_value=0.01, value=10.0, key="request_amount")
            request_note = st.text_input("Note", key="request_note", value="Can you send me some money?")
            
            if st.button("Send Request", type="primary", key="request_btn"):
                if not request_recipient:
                    st.error("Please enter a recipient")
                else:
                    ok, msg = request_money(user["user_id"], request_recipient, request_amount, request_note)
                    if ok:
                        toast_success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    with tab3:
        st.subheader("Transaction History")
        # Show user's transactions
        user_transactions = [t for t in st.session_state.transactions 
                           if t["sender_id"] == user["user_id"] or t["recipient_id"] == user["user_id"]]
        user_transactions.sort(key=lambda x: x["ts"], reverse=True)
        
        if user_transactions:
            transaction_data = []
            for tx in user_transactions:
                if tx["sender_id"] == user["user_id"]:
                    direction = "Sent"
                    amount = f"-{format_money(tx['amount'])}"
                    counterparty = get_user(tx["recipient_id"])["app_id"]
                else:
                    direction = "Received"
                    amount = f"+{format_money(tx['amount'])}"
                    counterparty = get_user(tx["sender_id"])["app_id"]
                
                transaction_data.append({
                    "Date": tx["ts"].strftime("%Y-%m-%d %H:%M"),
                    "Type": direction,
                    "Counterparty": counterparty,
                    "Amount": amount,
                    "Note": tx.get("note", "")
                })
            
            st.dataframe(pd.DataFrame(transaction_data), use_container_width=True)
        else:
            st.info("No transactions yet. Send or request money to get started!")

# ... (rest of your existing functions remain the same - show_markets, show_portfolio, show_settings, etc.)

def show_stocks_etfs():
    st.subheader("📊 Stocks & ETFs")
    
    # Major indices
    st.write("**Major Indices**")
    indices = get_major_indices()
    cols = st.columns(len(indices))
    
    for i, index in enumerate(indices):
        with cols[i]:
            delta_color = "normal"  # Let Streamlit decide based on value
            st.metric(
                label=index['name'],
                value=f"${index['price']:,.2f}",
                delta=f"{index['change_percent']:+.2f}%",
                delta_color=delta_color
            )
            st.caption(f"Source: {index.get('source', 'Yahoo Finance')}")

    # Popular stocks
    st.write("**Popular Stocks**")
    popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META']
    stock_cols = st.columns(3)
    
    for i, symbol in enumerate(popular_stocks):
        with stock_cols[i % 3]:
            data = get_stock_data(symbol, '1d')
            if data:
                st.metric(
                    label=symbol,
                    value=f"${data['current_price']:,.2f}",
                    delta=f"{data['change_percent']:+.2f}%"
                )

def show_crypto_assets():
    st.subheader("₿ Cryptocurrencies")
    
    crypto_data = get_crypto_prices()
    cols = st.columns(len(crypto_data))
    
    for i, crypto in enumerate(crypto_data):
        with cols[i]:
            st.metric(
                label=crypto['symbol'],
                value=f"${crypto['current_price']:,.2f}",
                delta=f"{crypto['change_percent']:+.2f}%"
            )
            st.caption(f"Source: {crypto['source']}")

    # Historical chart for Bitcoin
    st.write("**Bitcoin - 7 Day History**")
    btc_data = get_crypto_data('bitcoin', 7)
    if btc_data and btc_data['historical'] is not None:
        fig = create_price_chart(btc_data['historical'], "Bitcoin (7 Days)")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Historical data temporarily unavailable")

def show_bonds_treasuries():
    st.subheader("📋 Government Bonds & Fixed Income")
    
    treasury_data = get_treasury_yields()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Fixed Income Overview
        Government bonds provide stable income with varying levels of risk 
        and return profiles across different maturities.
        """)
        
        # Current Yields
        st.subheader("Current Government Yields")
        if treasury_data:
            t1, t2, t3 = st.columns(3)
            with t1:
                st.metric("1-Month Treasury", f"{treasury_data['1_month']:.2f}%")
            with t2:
                st.metric("2-Year Treasury", f"{treasury_data['2_year']:.2f}%")
            with t3:
                st.metric("10-Year Treasury", f"{treasury_data['10_year']:.2f}%")
            
            st.caption(f"Source: {treasury_data['source']} | Updated: {treasury_data['last_updated']}")
    
    with col2:
        st.markdown("### Quick Access")
        st.write("""
        **Explore More:**
        - **Treasury Bonds** → Full government bond access
        - **Municipal Bonds** → Tax-advantaged local bonds
        - **Corporate Bonds** → Higher yields (coming soon)
        """)
        
        st.info("""
        **Yield Curve Insight:**
        Monitor the relationship between short and long-term rates for economic signals.
        """)

def show_treasury_bonds():
    st.subheader("🇺🇸 U.S. Treasury Bonds")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### About Treasury Bonds
        U.S. Treasury bonds are debt securities issued by the federal government 
        to finance government spending. They are considered among the safest investments 
        because they are backed by the full faith and credit of the U.S. government.
        
        **Key Features:**
        - Backed by U.S. government
        - Tax advantages (exempt from state/local taxes)
        - Various maturities (4 weeks to 30 years)
        - Regular interest payments
        """)
        
        # Current Treasury Rates
        st.subheader("Current Treasury Rates")
        treasury_data = get_treasury_yields()
        if treasury_data:
            t1, t2, t3 = st.columns(3)
            with t1:
                st.metric("4-Week Bill", f"{treasury_data.get('4_week', 5.25):.2f}%")
            with t2:
                st.metric("2-Year Note", f"{treasury_data.get('2_year', 4.89):.2f}%")
            with t3:
                st.metric("10-Year Bond", f"{treasury_data.get('10_year', 4.45):.2f}%")
    
    with col2:
        st.markdown("### How to Invest")
        st.info("""
        **TreasuryDirect.gov**
        - Direct purchase from U.S. Treasury
        - No fees or commissions
        - Minimum investment: $100
        - Automatic reinvestment available
        """)
        
        if st.button("🪙 Visit TreasuryDirect", use_container_width=True):
            st.markdown("[Open TreasuryDirect.gov](https://www.treasurydirect.gov/)")
        
        st.markdown("### Investment Options")
        st.write("""
        - **Treasury Bills**: 4 weeks to 1 year
        - **Treasury Notes**: 2 to 10 years  
        - **Treasury Bonds**: 20 to 30 years
        - **TIPS**: Inflation-protected
        - **Floating Rate Notes**: Variable interest
        """)

def show_precious_metals():
    st.subheader("🥇 Precious Metals Investing")
    
    # Current Metals Prices
    metals_data = get_metals_prices()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Why Invest in Precious Metals?
        Precious metals can provide portfolio diversification and act as a hedge 
        against inflation and economic uncertainty.
        
        **Common Investment Options:**
        - Physical bullion (coins, bars)
        - ETFs and mutual funds
        - Mining company stocks
        - Futures and options
        """)
        
        # Current Prices
        st.subheader("Current Spot Prices")
        if metals_data:
            m1, m2, m3 = st.columns(3)
            with m1:
                if 'gold' in metals_data:
                    st.metric("Gold", f"${metals_data['gold']['price']:,.2f}/oz")
            with m2:
                if 'silver' in metals_data:
                    st.metric("Silver", f"${metals_data['silver']['price']:,.2f}/oz")
            with m3:
                if 'platinum' in metals_data:
                    st.metric("Platinum", f"${metals_data['platinum']['price']:,.2f}/oz")
    
    with col2:
        st.markdown("### Trusted Platforms")
        
        st.info("""
        **APMEX** - Largest online precious metals dealer
        - Huge selection of coins and bars
        - Competitive pricing
        - Secure storage options
        """)
        
        if st.button("🪙 Visit APMEX", use_container_width=True):
            st.markdown("[Open APMEX.com](https://www.apmex.com/)")
        
        st.markdown("### Learning Resources")
        if st.button("📚 APMEX Learning Center", use_container_width=True):
            st.markdown("[Open APMEX Learning Center](https://learn.apmex.com/)")

def show_startup_investing():
    st.subheader("🚀 Startup & Equity Crowdfunding")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Invest in Innovation
        Equity crowdfunding allows everyday investors to buy shares in startups 
        and early-stage companies.
        
        **SEC Regulations:**
        - Non-accredited investors can participate
        - Investment limits based on income/net worth
        - 12-month limit: 5-10% of income/net worth
        - Platforms must be SEC-registered
        """)
        
        st.warning("""
        **High Risk Warning:** Startup investing is speculative and carries 
        substantial risk of loss. Most startups fail. Only invest money 
        you can afford to lose completely.
        """)
        
        # Investment Limits Info
        st.subheader("Investment Limits")
        st.write("""
        **Based on annual income/net worth:**
        - If either is < $124,000: **$2,500** or 5% of greater amount
        - If both are ≥ $124,000: **$124,000** or 10% of annual income/net worth
        - Maximum across all platforms: **$124,000** per year
        """)
    
    with col2:
        st.markdown("### Leading Platforms")
        
        platforms = [
            ("Wefunder", "https://wefunder.com/", "Community-focused, diverse startups"),
            ("StartEngine", "https://www.startengine.com/explore", "Tech and innovation focus"),
            ("Republic", "https://republic.com/", "Curated selection, various sectors"),
            ("AngelList", "https://venture.angellist.com/v/start-investing", "VC-backed startups")
        ]
        
        for name, url, description in platforms:
            st.info(f"**{name}**\n\n{description}")
            if st.button(f"Visit {name}", key=f"btn_{name}"):
                st.markdown(f"[Open {name}]({url})")
        
        st.markdown("### Resources")
        if st.button("📊 SEC Crowdfunding Guide", use_container_width=True):
            st.markdown("[Open SEC Guide](https://www.sec.gov/oiea/investor-alerts-bulletins/ib_crowdfunding-.html)")
        
        if st.button("📈 Forbes Startup Guide", use_container_width=True):
            st.markdown("[Open Forbes Guide](https://www.forbes.com/advisor/investing/invest-in-startups/)")

def show_business_marketplace():
    st.subheader("🏢 Business Acquisition Marketplace")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Buy an Established Business
        Acquiring an existing business can provide immediate cash flow, 
        established operations, and proven business models.
        
        **Advantages vs Startups:**
        - Existing customer base
        - Proven revenue streams
        - Established systems and processes
        - Historical financial data
        - Trained employees
        """)
        
        st.subheader("Business Types Available")
        st.write("""
        - **Main Street Businesses**: $100K - $5M valuation
        - **Small Manufacturing**: $1M - $10M revenue
        - **Service Businesses**: Consulting, agencies, contractors
        - **Franchises**: Brand recognition with support
        - **E-commerce**: Online stores with established traffic
        """)
    
    with col2:
        st.markdown("### Marketplace Platform")
        
        st.info("""
        **BizBuySell** - Largest business marketplace
        - 45,000+ businesses for sale
        - All industries and price ranges
        - Confidential listing process
        - Business valuation tools
        """)
        
        if st.button("🏢 Browse Businesses", use_container_width=True):
            st.markdown("[Open BizBuySell](https://www.bizbuysell.com/)")
        
        st.markdown("### Due Diligence Checklist")
        st.write("""
        ✅ Financial records (3+ years)
        ✅ Customer concentration
        ✅ Market position & competition
        ✅ Legal and compliance status
        ✅ Employee and supplier contracts
        ✅ Physical assets condition
        """)

def show_royalty_investing():
    st.subheader("🎵 Royalty & Intellectual Property Investing")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Invest in Royalties
        Royalty investing allows you to earn income from intellectual property 
        like music, patents, film rights, and trademarks.
        
        **How It Works:**
        - Purchase a share of future royalty streams
        - Receive regular income payments
        - No active management required
        - Diversification from traditional assets
        """)
        
        st.subheader("Royalty Types")
        st.write("""
        - **Music Royalties**: Songwriting, publishing, master recordings
        - **Patent Royalties**: Technology, pharmaceuticals, inventions  
        - **Film & TV Royalties**: Streaming rights, syndication
        - **Mineral Royalties**: Oil, gas, mining rights
        - **Brand Royalties**: Trademarks, franchising
        """)
        
        # Example Royalty Returns
        st.subheader("Typical Returns")
        returns_data = {
            "Music Catalogs": "8-12%",
            "Patent Portfolios": "12-20%", 
            "Film Libraries": "6-10%",
            "Mineral Rights": "8-15%"
        }
        
        for asset_type, returns in returns_data.items():
            st.write(f"**{asset_type}**: {returns}")
    
    with col2:
        st.markdown("### Platform Access")
        
        st.info("""
        **Royalty Exchange** - Leading royalty marketplace
        - Vetted royalty offerings
        - Transparent bidding process
        - Secondary market liquidity
        - Professional due diligence
        """)
        
        if st.button("🎵 Browse Royalties", use_container_width=True):
            st.markdown("[Open Royalty Exchange](https://www.royaltyexchange.com/)")
        
        st.markdown("### Investment Considerations")
        st.write("""
        **Pros:**
        - Passive income streams
        - Portfolio diversification
        - Inflation hedging potential
        - Non-correlated returns
        
        **Cons:**
        - Limited liquidity
        - Complex valuation
        - Industry-specific risks
        - Due diligence intensive
        """)

def show_municipal_bonds():
    st.subheader("🏛️ Municipal Bonds")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Invest in Local Communities
        Municipal bonds are debt securities issued by state and local governments 
        to fund public projects like schools, roads, and infrastructure.
        
        **Key Benefits:**
        - Tax-free interest (federal and often state)
        - Generally high credit quality
        - Regular interest payments
        - Support community development
        """)
        
        st.subheader("Municipal Bond Types")
        st.write("""
        - **General Obligation (GO) Bonds**: Backed by taxing power
        - **Revenue Bonds**: Backed by project revenues  
        - **Taxable Munis**: For certain projects, taxable interest
        - **Zero-Coupon Munis**: Purchased at discount, no regular interest
        - **Build America Bonds**: Federal subsidy for infrastructure
        """)
    
    with col2:
        st.markdown("### Market Access")
        
        st.info("""
        **MunicipalBonds.com** - Comprehensive muni platform
        - Real-time bond pricing
        - Credit analysis tools
        - Tax-equivalent yield calculator
        - Educational resources
        """)
        
        if st.button("🏛️ Browse Muni Bonds", use_container_width=True):
            st.markdown("[Open MunicipalBonds.com](https://www.municipalbonds.com/)")
        
        st.markdown("### Risk Assessment")
        st.write("""
        **Credit Risks:**
        - Issuer financial health
        - Economic conditions
        - Tax base stability
        - Project viability
        
        **Market Risks:**
        - Interest rate changes
        - Inflation expectations
        - Liquidity constraints
        - Call provisions
        """)
        
        st.markdown("### Resources")
        if st.button("📚 Learn About Muni Bonds", use_container_width=True):
            st.markdown("[Open Investopedia Guide](https://www.investopedia.com/terms/m/municipalbond.asp)")

def show_universal_research():
    st.subheader("🔍 Universal Research Tool")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        symbol = st.text_input(
            "Research Any Asset", 
            value="AAPL",
            placeholder="AAPL, BTC-USD, GC=F, etc.",
            key="universal_research"
        )
    
    with col2:
        period = st.selectbox("Period", ["1d", "1wk", "1mo", "3mo", "1y"], key="research_period")
    
    with col3:
        st.write("")  # Spacer
        if st.button("Research Asset", type="primary"):
            st.session_state.research_symbol = symbol
            st.rerun()
    
    # Research results
    if hasattr(st.session_state, 'research_symbol'):
        symbol = st.session_state.research_symbol
        data = get_stock_data(symbol, period)
        
        if data:
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"${data['current_price']:,.2f}")
            with col2:
                st.metric("Change", f"${data['change']:+.2f}")
            with col3:
                st.metric("Change %", f"{data['change_percent']:+.2f}%")
            with col4:
                st.metric("52W Range", f"${data['52w_low']:.0f}-${data['52w_high']:.0f}")
            
            st.caption(f"Data Source: {data['source']} | Last Updated: {data['last_updated'].strftime('%Y-%m-%d %H:%M')}")
            
            # Historical chart
            if not data['historical'].empty:
                fig = create_price_chart(data['historical'], f"{symbol} Price History")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Could not fetch data for {symbol}. Try a different symbol.")

def show_markets(user):
    st.header("📈 Multi-Asset Markets")
    
    # Expanded investment categories
    asset_tabs = st.tabs([
        "Stocks & ETFs", 
        "Crypto", 
        "Bonds & Treasuries",
        "Treasury Bonds",  # New tab
        "Precious Metals",  # New tab
        "Startup Investing",  # New tab
        "Business Marketplace",  # New tab
        "Royalty Investing",  # New tab
        "Municipal Bonds"  # New tab
    ])
    
    with asset_tabs[0]:
        show_stocks_etfs()
    
    with asset_tabs[1]:
        show_crypto_assets()
    
    with asset_tabs[2]:
        show_bonds_treasuries()
    
    with asset_tabs[3]:
        show_treasury_bonds()
    
    with asset_tabs[4]:
        show_precious_metals()
    
    with asset_tabs[5]:
        show_startup_investing()
    
    with asset_tabs[6]:
        show_business_marketplace()
    
    with asset_tabs[7]:
        show_royalty_investing()
    
    with asset_tabs[8]:
        show_municipal_bonds()
    
    # Universal research tool
    st.markdown("---")
    show_universal_research()

def show_portfolio(user):
    st.header("Portfolio")

    if not user["watchlist"]:
        c1, c2 = st.columns([3, 1])
        with c2:
            if st.button("🎯 Add Starter Watchlist", use_container_width=True, key="pf_add_watchlist"):
                user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                toast_success("Starter watchlist added!")
                add_notification("🎯 Starter watchlist added with popular stocks & crypto")
                st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1:
        total_value = portfolio_value(user["user_id"])
        st.metric("Portfolio Value", format_money(total_value))
    with c2:
        unrealized = unrealized_gains(user["user_id"])
        st.metric("Unrealized P/L", format_money(unrealized))
    with c3:
        div_score = diversification_score(user["user_id"])
        st.metric("Diversification Score", f"{div_score}/100")

    st.subheader("Trade")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        symbol = _clean_symbol(st.text_input("Symbol", value="AAPL", key="trade_symbol"))
    with c2:
        side = st.selectbox("Side", ["buy", "sell"], key="trade_side")
    with c3:
        if side == "buy":
            cash_amount = st.number_input("Amount ($)", min_value=1.0, value=100.0, key="trade_cash")
            units = None
        else:
            available_units = float(user["portfolio"].get(symbol, {}).get("units", 0))
            if available_units > 0:
                units = st.number_input("Units", min_value=0.01, max_value=available_units, value=min(1.0, available_units), step=0.1, help=f"Available: {available_units:.4f} units", key="trade_units")
            else:
                st.info("No units available to sell for this symbol.")
                units = None
            cash_amount = None
    with c4:
        st.write("")
        if st.button("Place Order", type="primary", key="place_order_btn"):
            ok, msg, order = place_order(user["user_id"], symbol, side, cash_amount, units)
            if ok:
                action = "bought" if side == "buy" else "sold"
                toast_success(f"Order filled: {action} {order['units']:.4f} {symbol}")
                add_notification(f"📊 {action.title()} {order['units']:.4f} {symbol} for {format_money(order['value'])}")
                st.rerun()
            else:
                st.error(msg)

    st.subheader("Positions")
    if user["portfolio"]:
        rows = []
        for sym, position in user["portfolio"].items():
            data = get_cached_data(sym, "1d")
            if data:
                current_price = data["current_price"]
                value = position["units"] * current_price
                cost_basis = position["units"] * position["avg_cost"]
                unrealized_pl = value - cost_basis
                unrealized_pct = (unrealized_pl / cost_basis) * 100 if cost_basis > 0 else 0
                rows.append(
                    {
                        "Symbol": sym,
                        "Units": f"{position['units']:.4f}",
                        "Avg Cost": format_money(position["avg_cost"]),
                        "Last Price": format_money(current_price),
                        "Value": format_money(value),
                        "Unrealized $": format_money(unrealized_pl),
                        "Unrealized %": f"{unrealized_pct:.2f}%",
                    }
                )
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("Position data temporarily unavailable")
    else:
        st.info("No positions yet. Buy stocks or crypto to build your portfolio!")

    st.subheader("Watchlist")
    if user["watchlist"]:
        for sym in list(user["watchlist"]):
            data = get_cached_data(sym, "1d")
            if data:
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                with c1:
                    st.write(f"**{sym}**")
                with c2:
                    st.metric("Price", format_money(data["current_price"]), f"{data['change_percent']:.2f}%")
                with c3:
                    if st.button("View", key=f"view_{sym}"):
                        st.info(f"View {sym} in Markets tab")
                with c4:
                    if st.button("Remove", key=f"remove_{sym}"):
                        user["watchlist"].remove(sym)
                        add_notification(f"📉 Removed {sym} from watchlist")
                        st.rerun()
            else:
                st.write(f"❌ {sym} - Data unavailable")
    else:
        st.info("Watchlist is empty. Add symbols from the Markets tab or use the 'Add Starter Watchlist' button above!")

def show_settings(user):
    st.header("Settings")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Preferences")
        dark_mode = st.toggle("Dark Mode", value=user["settings"]["dark_mode"], key="pref_dark_mode")
        if dark_mode != user["settings"]["dark_mode"]:
            user["settings"]["dark_mode"] = dark_mode
            toast_success("Preferences updated")
            add_notification("⚙️ Preferences updated")

    with c2:
        st.subheader("Price Alerts")
        symbol = _clean_symbol(st.text_input("Symbol for Alert", value="BTC-USD", key="alert_symbol"))
        threshold = st.number_input("Alert Threshold ($)", min_value=0.01, value=50000.0, key="alert_threshold")

        if st.button("Set Alert", key="set_alert_btn"):
            if symbol:
                user["settings"]["price_alerts"][symbol] = threshold
                toast_success(f"Alert set for {symbol} at {format_money(threshold)}")
                add_notification(f"🔔 Price alert set: {symbol} at {format_money(threshold)}")
            else:
                st.warning("Enter a valid symbol before setting an alert.")

        if user["settings"]["price_alerts"]:
            st.write("Current Alerts:")
            for alert_symbol, alert_threshold in list(user["settings"]["price_alerts"].items()):
                c3, c4 = st.columns([3, 1])
                with c3:
                    st.write(f"{alert_symbol}: {format_money(alert_threshold)}")
                with c4:
                    if st.button("Remove", key=f"remove_alert_{alert_symbol}"):
                        del user["settings"]["price_alerts"][alert_symbol]
                        add_notification(f"🔕 Price alert removed: {alert_symbol}")
                        st.rerun()

# ----------------------------
# Main App
# ----------------------------
def main():
    # Initialize demo users
    ensure_demo_users()
    
    # Auth gate
    if not st.session_state.get("auth_user"):
        show_login()
        return

    show_main_app()

if __name__ == "__main__":
    main()
