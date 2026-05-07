import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import yfinance as yf

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

# Override the browser tab title (safe, static content)
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
    rounded = round(amount, 2)
    if rounded >= 0:
        return f"${rounded:,.2f}"
    else:
        return f"-${abs(rounded):,.2f}"

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
    st.session_state.setdefault(key, default)

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
    
    # Prevent floating point drift
    amount = round(amount, 2)
    sender["balance"] = round(sender["balance"] - amount, 2)
    recipient["balance"] = round(recipient["balance"] + amount, 2)
    
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
    user["balance"] = round(user["balance"] + 2000.0, 2)
    return True, "Paycheck deposited"

def toast_success(message):
    st.toast(f"✅ {message}")

def toast_info(message):
    st.toast(f"ℹ️ {message}")

# ----------------------------
# Investment Vehicle Functions (with caching)
# ----------------------------
@st.cache_data(ttl=60, show_spinner=False)
def get_stock_data(symbol, period="1mo"):
    """Fetch stock data from Yahoo Finance. Returns None on failure."""
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
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def get_major_indices():
    indices = {'^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^DJI': 'Dow Jones'}
    results = []
    for symbol, name in indices.items():
        data = get_stock_data(symbol, '1d')
        if data:
            results.append({
                'name': name, 'symbol': symbol, 'price': data['current_price'],
                'change': data['change'], 'change_percent': data['change_percent'],
                'source': data['source']
            })
        else:
            # Demo fallback with constant seeds for consistency while cached
            base_prices = {
                'S&P 500': 5000, 
                'NASDAQ': 16000, 
                'Dow Jones': 38000
            }
            results.append({
                'name': name, 'symbol': symbol, 
                'price': base_prices.get(name, 5000) + random.randint(-100, 100),
                'change': random.uniform(-50, 50), 
                'change_percent': random.uniform(-2, 2),
                'source': 'Demo'
            })
    return results

@st.cache_data(ttl=60, show_spinner=False)
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
            # Demo fallback
            current_price = 50000 if coin_id == 'bitcoin' else 3000
            change_percent = random.uniform(-5, 5)
            hist = None
        return {
            'symbol': coin_id.upper(), 'current_price': current_price,
            'change_percent': change_percent, 'historical': hist, 'source': 'Yahoo Finance'
        }
    except:
        return get_crypto_demo_data(coin_id, days)

def get_crypto_demo_data(coin_id="bitcoin", days=30):
    base_prices = {'bitcoin': 51234.56, 'ethereum': 2890.12}
    return {
        'symbol': coin_id.upper(), 
        'current_price': base_prices.get(coin_id, 1000),
        'change_percent': random.uniform(-5, 5), 
        'historical': None, 
        'source': 'Demo Data'
    }

@st.cache_data(ttl=60, show_spinner=False)
def get_crypto_prices():
    coins = ['bitcoin', 'ethereum']
    results = []
    for coin in coins:
        data = get_crypto_data(coin, 1)
        if data:
            # Normalize symbol to standard ticker format
            data['symbol'] = {'bitcoin': 'BTC-USD', 'ethereum': 'ETH-USD'}.get(coin, coin.upper())
            results.append(data)
    return results

@st.cache_data(ttl=300, show_spinner=False)
def get_treasury_yields():
    return {
        '1_month': 5.32, 
        '2_year': 4.89, 
        '10_year': 4.45, 
        'source': 'Demo', 
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    }

@st.cache_data(ttl=300, show_spinner=False)
def get_metals_prices():
    return {
        'gold': {'price': 1987.65, 'source': 'Demo'},
        'silver': {'price': 23.45, 'source': 'Demo'},
        'platinum': {'price': 987.32, 'source': 'Demo'}
    }

def create_price_chart(historical_data, title, chart_type="line"):
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
    st.write("**Major Indices**")
    indices = get_major_indices()
    cols = st.columns(len(indices))
    for i, index in enumerate(indices):
        with cols[i]:
            st.metric(
                label=index['name'], 
                value=f"${index['price']:,.2f}", 
                delta=f"{index['change_percent']:+.2f}%"
            )

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
        st.markdown("### Fixed Income Overview\nGovernment bonds provide stable income.")
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
        st.markdown("### About Treasury Bonds\nConsidered among the safest investments.")
        st.subheader("Current Treasury Rates")
        treasury_data = get_treasury_yields()
        if treasury_data:
            t1, t2, t3 = st.columns(3)
            with t1: st.metric("4-Week Bill", f"{treasury_data.get('1_month', 5.25):.2f}%")
            with t2: st.metric("2-Year Note", f"{treasury_data.get('2_year', 4.89):.2f}%")
            with t3: st.metric("10-Year Bond", f"{treasury_data.get('10_year', 4.45):.2f}%")
    with col2:
        st.info("**TreasuryDirect.gov**\n- Direct purchase\n- No fees\n- Min investment: $100")
        if st.button("🪙 Visit TreasuryDirect", use_container_width=True): 
            st.markdown("[Open TreasuryDirect](https://www.treasurydirect.gov/)")

def show_precious_metals():
    st.subheader("🥇 Precious Metals Investing")
    metals_data = get_metals_prices()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Why Invest in Precious Metals?\nHedge against inflation.")
        st.subheader("Current Spot Prices")
        if metals_data:
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Gold", f"${metals_data['gold']['price']:,.2f}/oz")
            with m2: st.metric("Silver", f"${metals_data['silver']['price']:,.2f}/oz")
            with m3: st.metric("Platinum", f"${metals_data['platinum']['price']:,.2f}/oz")
    with col2:
        st.info("**APMEX** - Largest online precious metals dealer\n- Secure storage")
        if st.button("🪙 Visit APMEX", use_container_width=True): 
            st.markdown("[Open APMEX](https://www.apmex.com/)")

def show_startup_investing():
    st.subheader("🚀 Startup & Equity Crowdfunding")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Invest in Innovation\nBuy shares in startups.")
        st.warning("**High Risk Warning:** Startup investing is speculative.")
    with col2:
        st.markdown("### Leading Platforms")
        platforms = [
            ("Wefunder", "https://wefunder.com/"), 
            ("StartEngine", "https://startengine.com/"), 
            ("Republic", "https://republic.com/")
        ]
        for name, url in platforms:
            if st.button(f"Visit {name}", key=f"btn_{name}", use_container_width=True): 
                st.markdown(f"[Open {name}]({url})")

def show_business_marketplace():
    st.subheader("🏢 Business Acquisition Marketplace")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Buy an Established Business\nAcquire proven business models.")
    with col2:
        st.info("**BizBuySell** - Largest marketplace\n- 45,000+ businesses")
        if st.button("🏢 Browse Businesses", use_container_width=True): 
            st.markdown("[Open BizBuySell](https://www.bizbuysell.com/)")

def show_royalty_investing():
    st.subheader("🎵 Royalty & Intellectual Property Investing")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Invest in Royalties\nEarn income from intellectual property.")
    with col2:
        st.info("**Royalty Exchange** - Leading marketplace\n- Vetted offerings")
        if st.button("🎵 Browse Royalties", use_container_width=True): 
            st.markdown("[Open Royalty Exchange](https://www.royaltyexchange.com/)")

def show_municipal_bonds():
    st.subheader("🏛️ Municipal Bonds")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Invest in Local Communities\nTax-free interest.")
    with col2:
        st.info("**MunicipalBonds.com** - Comprehensive muni platform")
        if st.button("🏛️ Browse Muni Bonds", use_container_width=True): 
            st.markdown("[Open MunicipalBonds](https://www.municipalbonds.com/)")

def show_universal_research():
    st.subheader("🔍 Universal Research Tool")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: 
        symbol = st.text_input("Research Asset", value="AAPL", key="uni_res")
    with col2: 
        period = st.selectbox("Period", ["1d", "1wk", "1mo", "3mo", "1y"], key="res_per")
    with col3:
        st.write("")
        if st.button("Research Asset", type="primary"):
            st.session_state.research_symbol = symbol
            st.rerun()
    
    # Safer check for the research symbol in session state
    if "research_symbol" in st.session_state:
        data = get_stock_data(st.session_state.research_symbol, period)
        if data:
            c1, c2, c3, _ = st.columns(4)
            with c1: st.metric("Price", f"${data['current_price']:,.2f}")
            with c2: st.metric("Change", f"${data['change']:+.2f}")
            with c3: st.metric("Change %", f"{data['change_percent']:+.2f}%")
            if not data['historical'].empty:
                fig = create_price_chart(data['historical'], f"{st.session_state.research_symbol} History")
                if fig: 
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Could not fetch data.")

# ----------------------------
# UI Components
# ----------------------------
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        display_logo(use_container_width=True) 
        st.markdown(
            "<h3 style='text-align: center; color: #FFFFFF; margin-bottom: 3rem;'>Build Wealth Together</h3>", 
            unsafe_allow_html=True
        )
    
    st.header("Welcome to Break Bread")
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        username = st.text_input("Username", placeholder="janedoe", key="login_user")
        password = st.text_input("Password", type="password", value="demo123", key="login_pass")
        if st.button("Login", type="primary"):
            result = fake_login(username, password)
            if result["status"] == "SUCCESS":
                st.session_state.auth_user = result["user_id"]
                st.rerun()
            else:
                st.error(result["message"])
        st.info("Demo accounts: **janedoe** or **johndoe** with password **demo123**")
    
    with tab_signup:
        st.info("This is a demo app. Use the existing accounts above to login.")

def show_main_app():
    user = get_user(st.session_state.auth_user)
    if not user:
        logout()
        return
    
    with st.sidebar:
        display_logo(width=150)
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FE8B00 0%, #FF9A2D 100%); padding: 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; text-align: center;'>
            <h3 style='color: #000000; margin: 0;'>{user['app_id']}</h3>
            <p style='color: #000000; margin: 0; opacity: 0.8;'>Break Bread Member</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: #1A1A1A; padding: 1.25rem; border-radius: 16px; border: 1px solid #333; margin-bottom: 1.5rem;'>
            <p style='color: #888; margin: 0;'>Available Cash</p>
            <h3 style='color: #FE8B00; margin: 0.5rem 0;'>{format_money(user["balance"])}</h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='color: #FFFFFF; margin-bottom: 1rem;'>Navigation</h4>", unsafe_allow_html=True)
        nav_options = [
            ("🏠 Dashboard", "Dashboard"), 
            ("💸 Banking", "Banking"), 
            ("📈 Markets", "Markets"), 
            ("⚙️ Settings", "Settings")
        ]
        
        for icon_label, value in nav_options:
            is_primary = "primary" if st.session_state.get("app_nav_radio") == value else "secondary"
            if st.button(
                f"**{icon_label}**", 
                key=f"nav_{value}", 
                use_container_width=True, 
                type=is_primary
            ):
                st.session_state.app_nav_radio = value
                st.rerun()

        st.markdown("---")
        st.markdown("<h4 style='color: #FFFFFF; margin-bottom: 1rem;'>Market Overview</h4>", unsafe_allow_html=True)
        for index in mini_indices()[:3]:
            color = "#00D54B" if index["chg_pct"] >= 0 else "#FF4444"
            st.markdown(f"""
            <div style='background-color: #1A1A1A; padding: 1rem; border-radius: 12px; border: 1px solid #333; margin-bottom: 0.5rem; display: flex; justify-content: space-between;'>
                <span style='color: #FFFFFF;'>{index['name']}</span>
                <div style='text-align: right;'><div style='color: #FFFFFF;'>{format_money(index['price'])}</div><div style='color: {color}; font-size: 0.8rem;'>{index['chg_pct']:+.2f}%</div></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("**🚪 Logout**", use_container_width=True, type="secondary"): 
            logout()

    nav = st.session_state.get("app_nav_radio")
    if nav == "Banking": show_banking(user)
    elif nav == "Markets": show_markets(user)
    elif nav == "Settings": show_settings(user)
    else: show_dashboard(user)

def show_dashboard(user):
    st.header("🏠 Dashboard")
    st.subheader(f"Welcome back, {user['app_id']}!")
    
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.metric("Cash Balance", format_money(user["balance"]))
    with col2: 
        st.metric("Portfolio Value", "$0.00")
    with col3: 
        st.metric("Net Worth", format_money(user["balance"]))
    
    st.subheader("Quick Actions")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💸 Send Money", use_container_width=True):
            st.session_state.app_nav_radio = "Banking"
            st.rerun()
    with c2:
        if st.button("📈 Invest", use_container_width=True):
            st.session_state.app_nav_radio = "Markets"
            st.rerun()
    with c3:
        if st.button("💰 Deposit", use_container_width=True, type="primary"):
            success, msg = simulate_paycheck(user["user_id"])
            if success:
                toast_success(f"💰 {msg}")
            else:
                st.error(msg)
            st.rerun()
    with c4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.app_nav_radio = "Settings"
            st.rerun()

    st.subheader("Featured Investment Vehicles")
    i1, i2, i3 = st.columns(3)
    features = [
        ("🏢 Business Marketplace", "Buy established businesses"),
        ("🏛️ Municipal Bonds", "Tax-free local investments"),
        ("🎵 Royalty Investing", "Earn from music & patents")
    ]
    for col, (title, desc) in zip([i1, i2, i3], features):
        with col:
            st.markdown(
                f"<div style='background-color: #1A1A1A; padding: 1.5rem; border-radius: 12px; border: 1px solid #333;'><h4 style='color: #FE8B00;'>{title}</h4><p style='color: #888;'>{desc}</p></div>", 
                unsafe_allow_html=True
            )

def show_banking(user):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("💸 Banking")
    with col2:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Home", key="home_btn_banking", use_container_width=True):
            st.session_state.app_nav_radio = "Dashboard"
            st.rerun()
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%); padding: 2rem; border-radius: 20px; margin-bottom: 2rem; border: 1px solid #333;'>
        <h3 style='color: #FFFFFF; margin: 0 0 0.5rem 0;'>Available Balance</h3>
        <h1 style='color: #FE8B00; margin: 0; font-size: 2.8rem;'>{format_money(user["balance"])}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("**+ Add Cash**", use_container_width=True, type="primary"):
        success, msg = simulate_paycheck(user["user_id"])
        if success:
            toast_success(f"💰 {msg}")
        else:
            st.error(msg)
        st.rerun()

    tab1, tab2 = st.tabs(["💸 Send Money", "📊 Transaction History"])
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Send Payment")
            recipient = st.text_input("Recipient", key="send_rec")
            amount = st.number_input("Amount", min_value=0.01, value=10.0, key="send_amt")
            if st.button("Send", type="primary"):
                ok, msg = send_money(user["user_id"], recipient, amount)
                if ok: 
                    toast_success(msg)
                    st.rerun()
                else: 
                    st.error(msg)
        with c2:
            st.subheader("Quick Send")
            for demo_user in [u for u in st.session_state.users.values() if u["user_id"] != user["user_id"]][:2]:
                if st.button(f"Send $10 to {demo_user['app_id']}", key=f"quick_{demo_user['user_id']}"):
                    if send_money(user["user_id"], demo_user["app_id"], 10.0)[0]: 
                        st.rerun()
    
    with tab2:
        txs = [t for t in st.session_state.transactions if user["user_id"] in [t["sender_id"], t["recipient_id"]]]
        if txs:
            data = []
            for tx in txs:
                if tx["sender_id"] == user["user_id"]:
                    ttype = "Sent"
                else:
                    ttype = "Received"
                
                data.append({
                    "Date": tx["ts"].strftime("%Y-%m-%d"), 
                    "Type": ttype, 
                    "Amount": format_money(tx['amount'])
                })
                
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No transactions yet.")

def show_markets(user):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("📈 Multi-Asset Markets")
    with col2:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Home", key="home_btn_markets", use_container_width=True):
            st.session_state.app_nav_radio = "Dashboard"
            st.rerun()
    
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
    
    with asset_tabs[0]: show_stocks_etfs()
    with asset_tabs[1]: show_crypto_assets()
    with asset_tabs[2]: show_bonds_treasuries()
    with asset_tabs[3]: show_treasury_bonds()
    with asset_tabs[4]: show_precious_metals()
    with asset_tabs[5]: show_startup_investing()
    with asset_tabs[6]: show_business_marketplace()
    with asset_tabs[7]: show_royalty_investing()
    with asset_tabs[8]: show_municipal_bonds()
    
    st.markdown("---")
    show_universal_research()

def show_settings(user):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("⚙️ Settings")
    with col2:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Home", key="home_btn_settings", use_container_width=True):
            st.session_state.app_nav_radio = "Dashboard"
            st.rerun()
    
    st.write(f"**Username:** {user['app_id']}\n**Email:** {user['email']}")
    dark_mode = st.toggle("Dark Mode", value=True)
    if st.button("Save Preferences"): 
        st.success("Saved!")
    st.divider()
    if st.button("Logout", type="secondary"): 
        logout()

# ----------------------------
# Main App
# ----------------------------
def main():
    ensure_demo_users()
    if not st.session_state.get("auth_user"):
        show_login()
        return
    show_main_app()

if __name__ == "__main__":
    main()
