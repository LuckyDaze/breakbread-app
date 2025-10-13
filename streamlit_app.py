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
    page_icon="assets/favicon.png",
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
    """Get multiple cryptocurrency prices."""
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

def get_treasury_yields():
    """Get Treasury yields data."""
    try:
        return {
            '1_month': 5.32,
            '2_year': 4.89,
            '10_year': 4.45,
            'source': 'U.S. Treasury',
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
    except:
        return {
            '1_month': 5.32,
            '2_year': 4.89,
            '10_year': 4.45,
            'source': 'U.S. Treasury (Demo)',
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }

def get_metals_prices():
    """Get precious metals prices."""
    try:
        return {
            'gold': {'price': 1987.65, 'source': 'Demo Data', 'last_updated': datetime.now()},
            'silver': {'price': 23.45, 'source': 'Demo Data', 'last_updated': datetime.now()},
            'platinum': {'price': 987.32, 'source': 'Demo Data', 'last_updated': datetime.now()}
        }
    except:
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

def mini_indices():
    """Get major indices data for sidebar."""
    indices_data = get_major_indices()
    return [
        {
            "name": idx["name"],
            "price": idx["price"],
            "chg_pct": idx["change_percent"]
        }
        for idx in indices_data
    ]

# ----------------------------
# Investment Vehicle Display Functions
# ----------------------------
def show_stocks_etfs():
    st.subheader("📊 Stocks & ETFs")
    
    # Major indices
    st.write("**Major Indices**")
    indices = get_major_indices()
    cols = st.columns(len(indices))
    
    for i, index in enumerate(indices):
        with cols[i]:
            delta_color = "normal"
            st.metric(
                label=index['name'],
                value=f"${index['price']:,.2f}",
                delta=f"{index['change_percent']:+.2f}%",
                delta_color=delta_color
            )

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
        
        st.subheader("Current Government Yields")
        if treasury_data:
            t1, t2, t3 = st.columns(3)
            with t1:
                st.metric("1-Month Treasury", f"{treasury_data['1_month']:.2f}%")
            with t2:
                st.metric("2-Year Treasury", f"{treasury_data['2_year']:.2f}%")
            with t3:
                st.metric("10-Year Treasury", f"{treasury_data['10_year']:.2f}%")
    
    with col2:
        st.markdown("### Quick Access")
        st.write("""
        **Explore More:**
        - **Treasury Bonds** → Full government bond access
        - **Municipal Bonds** → Tax-advantaged local bonds
        - **Corporate Bonds** → Higher yields (coming soon)
        """)

def show_treasury_bonds():
    st.subheader("🇺🇸 U.S. Treasury Bonds")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### About Treasury Bonds
        U.S. Treasury bonds are debt securities issued by the federal government 
        to finance government spending. They are considered among the safest investments.
        
        **Key Features:**
        - Backed by U.S. government
        - Tax advantages (exempt from state/local taxes)
        - Various maturities (4 weeks to 30 years)
        - Regular interest payments
        """)
        
        st.subheader("Current Treasury Rates")
        treasury_data = get_treasury_yields()
        if treasury_data:
            t1, t2, t3 = st.columns(3)
            with t1:
                st.metric("4-Week Bill", f"{treasury_data.get('1_month', 5.25):.2f}%")
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

def show_precious_metals():
    st.subheader("🥇 Precious Metals Investing")
    
    metals_data = get_metals_prices()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Why Invest in Precious Metals?
        Precious metals can provide portfolio diversification and act as a hedge 
        against inflation and economic uncertainty.
        """)
        
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
        substantial risk of loss. Most startups fail.
        """)
    
    with col2:
        st.markdown("### Leading Platforms")
        
        platforms = [
            ("Wefunder", "https://wefunder.com/", "Community-focused, diverse startups"),
            ("StartEngine", "https://www.startengine.com/explore", "Tech and innovation focus"),
            ("Republic", "https://republic.com/", "Curated selection, various sectors"),
        ]
        
        for name, url, description in platforms:
            st.info(f"**{name}**\n\n{description}")
            if st.button(f"Visit {name}", key=f"btn_{name}"):
                st.markdown(f"[Open {name}]({url})")

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
        st.write("")
        if st.button("Research Asset", type="primary"):
            st.session_state.research_symbol = symbol
            st.rerun()
    
    if hasattr(st.session_state, 'research_symbol'):
        symbol = st.session_state.research_symbol
        data = get_stock_data(symbol, period)
        
        if data:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"${data['current_price']:,.2f}")
            with col2:
                st.metric("Change", f"${data['change']:+.2f}")
            with col3:
                st.metric("Change %", f"{data['change_percent']:+.2f}%")
            
            if not data['historical'].empty:
                fig = create_price_chart(data['historical'], f"{symbol} Price History")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Could not fetch data for {symbol}. Try a different symbol.")

# ----------------------------
# UI Components
# ----------------------------
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #FE8B00; font-size: 3.5rem; font-weight: 700;'>Break Bread</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #FFFFFF; margin-bottom: 3rem;'>Build Wealth Together</h3>", unsafe_allow_html=True)
    
    st.header("Welcome to Break Bread")

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        st.subheader("Login to Your Account")
        username = st.text_input("Username", placeholder="janedoe or johndoe", key="login_user")
        password = st.text_input("Password", type="password", value="demo123", key="login_pass")
        
        if st.button("Login", type="primary"):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                result = fake_login(username, password)
                if result["status"] == "SUCCESS":
                    st.session_state.auth_user = result["user_id"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result["message"])
        
        st.info("Demo accounts: **janedoe** or **johndoe** with password **demo123**")
    
    with tab_signup:
        st.subheader("Create Demo Account")
        st.info("This is a demo app. Use the existing accounts above to login.")

def show_main_app():
    user = get_user(st.session_state.auth_user)
    if not user:
        logout()
        return
    
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

    # Main content area based on navigation
    if st.session_state.get("app_nav_radio") == "Dashboard":
        show_dashboard(user)
    elif st.session_state.get("app_nav_radio") == "Banking":
        show_banking(user)
    elif st.session_state.get("app_nav_radio") == "Markets":
        show_markets(user)
    elif st.session_state.get("app_nav_radio") == "Settings":
        show_settings(user)
    else:
        show_dashboard(user)

def show_dashboard(user):
    st.header("🏠 Dashboard")
    
    # Welcome message
    st.subheader(f"Welcome back, {user['app_id']}!")
    
    # Balance cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cash Balance", format_money(user["balance"]))
    
    with col2:
        portfolio_val = 0  # Simplified for demo
        st.metric("Portfolio Value", format_money(portfolio_val))
    
    with col3:
        total = user["balance"] + portfolio_val
        st.metric("Net Worth", format_money(total))
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💸 Send Money", use_container_width=True):
            st.session_state.app_nav_radio = "Banking"
            st.rerun()
    
    with col2:
        if st.button("📈 Invest", use_container_width=True):
            st.session_state.app_nav_radio = "Markets"
            st.rerun()
    
    with col3:
        if st.button("💰 Deposit", use_container_width=True, type="primary"):
            ok, _ = simulate_paycheck(user["user_id"])
            if ok:
                toast_success("💰 $2,000 added to your balance!")
                st.rerun()
    
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.app_nav_radio = "Settings"
            st.rerun()

    # Investment Opportunities
    st.subheader("Featured Investment Vehicles")
    
    investment_cols = st.columns(3)
    
    with investment_cols[0]:
        st.markdown("""
        <div style='background-color: #1A1A1A; padding: 1.5rem; border-radius: 12px; border: 1px solid #333;'>
            <h4 style='color: #FE8B00; margin-bottom: 1rem;'>🏢 Business Marketplace</h4>
            <p style='color: #888; font-size: 0.9rem;'>Buy established businesses with proven cash flow</p>
        </div>
        """, unsafe_allow_html=True)
    
    with investment_cols[1]:
        st.markdown("""
        <div style='background-color: #1A1A1A; padding: 1.5rem; border-radius: 12px; border: 1px solid #333;'>
            <h4 style='color: #FE8B00; margin-bottom: 1rem;'>🏛️ Municipal Bonds</h4>
            <p style='color: #888; font-size: 0.9rem;'>Tax-free investments supporting local communities</p>
        </div>
        """, unsafe_allow_html=True)
    
    with investment_cols[2]:
        st.markdown("""
        <div style='background-color: #1A1A1A; padding: 1.5rem; border-radius: 12px; border: 1px solid #333;'>
            <h4 style='color: #FE8B00; margin-bottom: 1rem;'>🎵 Royalty Investing</h4>
            <p style='color: #888; font-size: 0.9rem;'>Earn from music, patents, and intellectual property</p>
        </div>
        """, unsafe_allow_html=True)

def show_banking(user):
    st.header("💸 Banking")
    
    # Balance display
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
        if st.button("**+ Add Cash**", use_container_width=True, type="primary"):
            ok, _ = simulate_paycheck(user["user_id"])
            if ok:
                toast_success("💰 $2,000 added to your balance!")
                st.rerun()

    # Banking tabs
    tab1, tab2 = st.tabs(["💸 **Send Money**", "📊 **Transaction History**"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Send Money")
            recipient = st.text_input("Recipient (Username)", key="send_recipient")
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
        st.subheader("Transaction History")
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

def show_markets(user):
    st.header("📈 Multi-Asset Markets")
    
    # Expanded investment categories
    asset_tabs = st.tabs([
        "Stocks & ETFs", 
        "Crypto", 
        "Bonds & Treasuries",
        "Treasury Bonds",
        "Precious Metals",
        "Startup Investing",
        "Business Marketplace",
        "Royalty Investing",
        "Municipal Bonds"
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

def show_settings(user):
    st.header("⚙️ Settings")
    
    st.subheader("Account Information")
    st.write(f"**Username:** {user['app_id']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Member since:** Demo version")
    
    st.subheader("Preferences")
    dark_mode = st.toggle("Dark Mode", value=True)
    notifications = st.toggle("Email Notifications", value=True)
    
    if st.button("Save Preferences"):
        st.success("Preferences saved!")
    
    st.divider()
    
    if st.button("Logout", type="secondary"):
        logout()

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
