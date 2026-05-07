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
        st.image(logo_path, width=width, use_container_width=use_container_width)
    else:
        st.markdown("<h1 style='text-align: center; color: #FE8B00; font-size: 3.5rem; font-weight: 700;'>Break Bread</h1>", unsafe_allow_html=True)

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
        return {"status": "ERROR", "message": "User not found"}

def logout():
    st.session_state.auth_user = None
    st.rerun()

def send_money(sender_id, recipient_identifier, amount, note=""):
    recipient = find_user(recipient_identifier)
    if not recipient:
        return False, "Recipient not found"
    
    sender = get_user(sender_id)
    if not sender:
        return False, "Sender not found"
    
    if sender["balance"] < amount:
        return False, "Insufficient funds"
    
    sender["balance"] -= amount
    recipient["balance"] += amount
    
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
    user = get_user(user_id)
    if not user:
        return False, "User not found"
    user["balance"] += 2000.0
    return True, "Paycheck deposited"

def toast_success(message):
    st.toast(f"✅ {message}")

def toast_info(message):
    st.toast(f"ℹ️ {message}")

# ----------------------------
# Investment Vehicle Functions
# ----------------------------
def get_stock_data(symbol, period="1mo"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty: return None
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
    except Exception:
        return None

def get_major_indices():
    indices = {'^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^DJI': 'Dow Jones'}
    results = []
    for symbol, name in indices.items():
        data = get_stock_data(symbol, '1d')
        if data:
            results.append({
                'name': name, 'symbol': symbol, 'price': data['current_price'],
                'change': data['change'], 'change_percent': data['change_percent'], 'source': data['source']
            })
        else:
            base_prices = {'S&P 500': 5000 + random.randint(-100, 100), 'NASDAQ': 16000 + random.randint(-200, 200), 'Dow Jones': 38000 + random.randint(-300, 300)}
            results.append({
                'name': name, 'symbol': symbol, 'price': base_prices[name],
                'change': random.uniform(-50, 50), 'change_percent': random.uniform(-2, 2), 'source': 'Demo'
            })
    return results

def get_crypto_data(coin_id="bitcoin", days=30):
    try:
        symbol_map = {'bitcoin': 'BTC-USD', 'ethereum': 'ETH-USD'}
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
            'symbol': coin_id.upper(), 'current_price': current_price,
            'change_percent': change_percent, 'historical': hist, 'source': 'Yahoo Finance'
        }
    except:
        return get_crypto_demo_data(coin_id, days)

def get_crypto_prices():
    coins = ['bitcoin', 'ethereum']
    results = []
    for coin in coins:
        data = get_crypto_data(coin, 1)
        if data:
            data['symbol'] = {'bitcoin': 'BTC-USD', 'ethereum': 'ETH-USD'}.get(coin, coin.upper())
            results.append(data)
    return results

def get_crypto_demo_data(coin_id="bitcoin", days=30):
    base_prices = {'bitcoin': 51234.56, 'ethereum': 2890.12}
    return {
        'symbol': coin_id.upper(), 'current_price': base_prices.get(coin_id, 1000),
        'change_percent': random.uniform(-5, 5), 'historical': None, 'source': 'Demo Data'
    }

def get_treasury_yields():
    return {'1_month': 5.32, '2_year': 4.89, '10_year': 4.45, 'source': 'Demo', 'last_updated': datetime.now().strftime('%Y-%m-%d')}

def get_metals_prices():
    return {
        'gold': {'price': 1987.65, 'source': 'Demo'},
        'silver': {'price': 23.45, 'source': 'Demo'},
        'platinum': {'price': 987.32, 'source': 'Demo'}
    }

def create_price_chart(historical_data, title, chart_type="line"):
    if historical_data is None or historical_data.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Close'], mode='lines', name=title, line=dict(color='#FE8B00')))
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Price ($)", height=400, template="plotly_dark", showlegend=False)
    return fig

def mini_indices():
    indices_data = get_major_indices()
    return [{"name": idx["name"], "price": idx["price"], "chg_pct": idx["change_percent"]} for idx in indices_data]

# ----------------------------
# Investment Vehicle Display Functions
# ----------------------------
def show_stocks_etfs():
    st.subheader("📊 Stocks & ETFs")
    st.write("**Major Indices**")
    indices = get_major_indices()
    cols = st.columns(len(indices))
    for i, index in enumerate(indices):
        with cols[i]:
            st.metric(label=index['name'], value=f"${index['price']:,.2f}", delta=f"{index['change_percent']:+.2f}%")

    st.write("**Popular Stocks**")
    popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META']
    stock_cols = st.columns(3)
    for i, symbol in enumerate(popular_stocks):
        with stock_cols[i % 3]:
            data = get_stock_data(symbol, '1d')
            if data: st.metric(label=symbol, value=f"${data['current_price']:,.2f}", delta=f"{data['change_percent']:+.2f}%")

def show_crypto_assets():
    st.subheader("₿ Cryptocurrencies")
    crypto_data = get_crypto_prices()
    cols = st.columns(len(crypto_data))
    for i, crypto in enumerate(crypto_data):
        with cols[i]: st.metric(label=crypto['symbol'], value=f"${crypto['current_price']:,.2f}", delta=f"{crypto['change_percent']:+.2f}%")

def show_bonds_treasuries():
    st.subheader("📋 Government Bonds & Fixed Income")
    treasury_data = get_treasury_yields()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Fixed Income Overview\nGovernment bonds provide stable income with varying levels of risk and return profiles across different maturities.")
        st.subheader("Current Government Yields")
        if treasury_data:
            t1, t2, t3 = st.columns(3)
            with t1: st.metric("1-Month Treasury", f"{treasury_data['1_month']:.2f}%")
            with t2: st.metric("2-Year Treasury", f"{treasury_data['2_year']:.2f}%")
            with t3: st.metric("10-Year Treasury", f"{treasury_data['10_year']:.2f}%")
    with col2:
        st.markdown("### Quick Access\n**Explore More:**\n- **Treasury Bonds**\n- **Municipal Bonds**\n- **Corporate Bonds**")

def show_treasury_bonds():
    st.subheader("🇺🇸 U.S. Treasury Bonds")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### About Treasury Bonds\nU.S. Treasury bonds are debt securities issued by the federal government to finance government spending. They are considered among the safest investments.")
        st.subheader("Current Treasury Rates")
        treasury_data = get_treasury_yields()
        if treasury_data:
            t1, t2, t3 = st.columns(3)
            with t1: st.metric("4-Week Bill", f"{treasury_data.get('1_month', 5.25):.2f}%")
            with t2: st.metric("2-Year Note", f"{treasury_data.get('2_year', 4.89):.2f}%")
            with t3: st.metric("10-Year Bond", f"{treasury_data.get('10_year', 4.45):.2f}%")
    with col2:
        st.info("**TreasuryDirect.gov**\n- Direct purchase from U.S. Treasury\n- No fees or commissions\n- Minimum investment: $100")
        if st.button("🪙 Visit TreasuryDirect", use_container_width=True): st.markdown("[Open TreasuryDirect](https://www.treasurydirect.gov/)")

def show_precious_metals():
    st.subheader("🥇 Precious Metals Investing")
    metals_data = get_metals_prices()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Why Invest in Precious Metals?\nPrecious metals can provide portfolio diversification and act as a hedge against inflation and economic uncertainty.")
        st.subheader("Current Spot Prices")
        if metals_data:
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Gold", f"${metals_data['gold']['price']:,.2f}/oz")
            with m2: st.metric("Silver", f"${metals_data['silver']['price']:,.2f}/oz")
            with m3: st.metric("Platinum", f"${metals_data['platinum']['price']:,.2f}/oz")
    with col2:
        st.info("**APMEX** - Largest online precious metals dealer\n- Huge selection\n- Secure storage")
        if st.button("🪙 Visit APMEX", use_
