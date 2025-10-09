import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import yfinance as yf

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

def seed_price_path(base_value, days, volatility=0.02):
    """Generate simulated price path for charts."""
    prices = [base_value]
    for _ in range(days - 1):
        change = random.uniform(-volatility, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    return prices

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
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return None
            
        info = ticker.info
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent,
            'historical': hist,
            '52w_high': info.get('fiftyTwoWeekHigh', current_price * 1.2),
            '52w_low': info.get('fiftyTwoWeekLow', current_price * 0.8)
        }
    except:
        return None

def mini_indices():
    """Get major indices data."""
    indices = [
        {"symbol": "^GSPC", "name": "S&P 500"},
        {"symbol": "^DJI", "name": "Dow Jones"},
        {"symbol": "^IXIC", "name": "NASDAQ"},
        {"symbol": "BTC-USD", "name": "Bitcoin"}
    ]
    
    results = []
    for index in indices:
        data = get_cached_data(index["symbol"], "1d")
        if data:
            results.append({
                "name": index["name"],
                "price": data["current_price"],
                "chg_pct": data["change_percent"]
            })
        else:
            # Fallback data
            results.append({
                "name": index["name"],
                "price": 5000 + random.randint(-100, 100),
                "chg_pct": random.uniform(-1, 1)
            })
    
    return results

def chart(historical_data, symbol, chart_type="line"):
    """Create a chart from historical data."""
    fig = go.Figure()
    
    if chart_type == "candlestick":
        fig.add_trace(go.Candlestick(
            x=historical_data.index,
            open=historical_data['Open'],
            high=historical_data['High'],
            low=historical_data['Low'],
            close=historical_data['Close'],
            name=symbol
        ))
    else:
        fig.add_trace(go.Scatter(
            x=historical_data.index,
            y=historical_data['Close'],
            mode='lines',
            name=symbol
        ))
    
    fig.update_layout(
        title=f"{symbol} Price",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400
    )
    return fig

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
        st.header(f"Welcome, {user['app_id']}!")
        st.metric("Cash Balance", format_money(user["balance"]))

        st.subheader("Market Overview")
        for index in mini_indices():
            st.metric(index["name"], format_money(index["price"]), f"{index['chg_pct']:.2f}%")

        st.divider()
        nav = st.radio(
            "Navigation",
            ["Dashboard", "Banking", "Markets", "Portfolio", "Settings"],
            key="app_nav_radio",
        )

        if st.button("Logout", key="logout_btn"):
            logout()
            st.rerun()

    with st.sidebar:
        st.divider()
        with st.expander("🔔 Notifications", expanded=False):
            notifications = get_notifications()
            if notifications:
                for notif in notifications[-10:]:
                    st.caption(f"{notif['timestamp'].strftime('%H:%M')} - {notif['message']}")
                if st.button("Clear All", key="clear_notifications"):
                    st.session_state.notifications = []
                    st.rerun()
            else:
                st.info("No notifications")

    if nav == "Dashboard":
        show_dashboard(user)
    elif nav == "Banking":
        show_banking(user)
    elif nav == "Markets":
        show_markets(user)
    elif nav == "Portfolio":
        show_portfolio(user)
    elif nav == "Settings":
        show_settings(user)

def show_dashboard(user):
    st.header("Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_value = portfolio_value(user["user_id"]) + user["balance"]
        st.metric("Total Portfolio", format_money(total_value))
    with col2:
        unrealized = unrealized_gains(user["user_id"])
        st.metric("Unrealized P/L", format_money(unrealized))
    with col3:
        div_score = diversification_score(user["user_id"])
        st.metric("Diversification Score", f"{div_score}/100")
    with col4:
        recent_tx = len([t for t in st.session_state.transactions if t["sender_id"] == user["user_id"] and (datetime.now() - t["ts"]).days <= 7])
        st.metric("Weekly Transactions", recent_tx)

    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💰 Simulate Paycheck", use_container_width=True, key="qa_paycheck"):
            ok, _ = simulate_paycheck(user["user_id"])
            if ok:
                toast_success("Paycheck deposited!")
                add_notification("💰 Paycheck deposited: $2,000.00")
                st.rerun()
    with c2:
        if st.button("📈 Add Starter Watchlist", use_container_width=True, key="qa_watchlist"):
            if not user["watchlist"]:
                user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                toast_success("Starter watchlist added!")
                add_notification("🎯 Starter watchlist added with popular stocks & crypto")
                st.rerun()
            else:
                toast_info("You already have a watchlist!")
    with c3:
        if st.button("🔄 Refresh Data", use_container_width=True, key="qa_refresh"):
            st.rerun()

    st.subheader("Portfolio Value (Last 30 Days)")
    base_value = total_value * 0.9
    historical_values = seed_price_path(base_value, 30)
    chart_data = pd.DataFrame({"Date": pd.date_range(end=datetime.now(), periods=30), "Portfolio Value": historical_values})
    st.line_chart(chart_data.set_index("Date"))

    st.subheader("Recent Activity")
    user_activities = []
    for tx in st.session_state.transactions[-10:]:
        if tx["sender_id"] == user["user_id"] or tx["recipient_id"] == user["user_id"]:
            status_icon = "🔄" if tx["status"] == "pending" else "✅" if tx["status"] == "completed" else "❌"
            user_activities.append({
                "Type": f"{status_icon} Payment",
                "Amount": f"-{format_money(tx['amount'])}" if tx["sender_id"] == user["user_id"] else f"+{format_money(tx['amount'])}",
                "Description": tx["note"],
                "Date": tx["ts"].strftime("%Y-%m-%d"),
                "Status": tx["status"].title(),
            })

    for order in st.session_state.orders[-5:]:
        if order["user_id"] == user["user_id"]:
            user_activities.append({
                "Type": f"📊 {order['side'].title()} {order['symbol']}",
                "Amount": format_money(order["value"]),
                "Description": f"{order['units']:.4f} units @ {format_money(order['fill_price'])}",
                "Date": order["ts"].strftime("%Y-%m-%d"),
                "Status": order["status"].title(),
            })

    if user_activities:
        st.dataframe(pd.DataFrame(user_activities), use_container_width=True)
    else:
        st.info("No recent activity. Start by sending money or making investments!")

def show_banking(user):
    st.header("Banking")

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("💰 Simulate Paycheck", use_container_width=True, type="secondary", key="bank_paycheck"):
            ok, _ = simulate_paycheck(user["user_id"])
            if ok:
                toast_success("Paycheck deposited!")
                add_notification("💰 Paycheck deposited: $2,000.00")
                st.rerun()

    tab1, tab2, tab3 = st.tabs(["Send Money", "Request Money", "Transaction History"])

    with tab1:
        st.subheader("Send Money")
        recipient_id = st.text_input("Recipient App ID or Email")
        amount = st.number_input("Amount", min_value=0.01, step=1.0)
        note = st.text_input("Note (optional)")

        if st.button("Send Payment", type="primary"):
            if amount > user["balance"]:
                st.error("Insufficient funds")
            else:
                fake_tx = {"sender_id": user["user_id"], "recipient_id": recipient_id, "amount": amount}
                warnings = fraud_check(fake_tx)
                if warnings:
                    for warning in warnings:
                        toast_warn(warning)
                        add_notification(f"⚠️ {warning}")

                ok, msg = send_money(user["user_id"], recipient_id, amount, note)
                if ok:
                    toast_success(f"Sent {format_money(amount)} to {recipient_id}")
                    add_notification(f"💸 Sent {format_money(amount)} to {recipient_id}")
                    st.rerun()
                else:
                    st.error(msg)

    with tab2:
        st.subheader("Request Money")
        from_id = st.text_input("From App ID or Email")
        req_amount = st.number_input("Amount to Request", min_value=0.01, step=1.0)
        req_note = st.text_input("Request Note")

        if st.button("Send Request"):
            ok, msg = request_money(user["user_id"], from_id, req_amount, req_note)
            if ok:
                toast_success("Money request sent")
                add_notification(f"📥 Money request sent: {format_money(req_amount)} to {from_id}")
            else:
                st.error(msg)

        st.subheader("Pending Requests")
        user_requests = [r for r in st.session_state.requests if r["recipient_id"] == user["user_id"]]
        if user_requests:
            for req in user_requests:
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                with c1:
                    st.write(f"**{format_money(req['amount'])}** from {req['requestor_id']}")
                    st.caption(req["note"])
                with c2:
                    if st.button("Pay", key=f"pay_{req['request_id']}"):
                        ok, _ = send_money(user["user_id"], req["requestor_id"], req["amount"], "Request payment")
                        if ok:
                            st.session_state.requests = [r for r in st.session_state.requests if r["request_id"] != req["request_id"]]
                            add_notification(f"✅ Paid request: {format_money(req['amount'])} to {req['requestor_id']}")
                            st.rerun()
                with c3:
                    if st.button("Decline", key=f"decline_{req['request_id']}"):
                        st.session_state.requests = [r for r in st.session_state.requests if r["request_id"] != req["request_id"]]
                        add_notification(f"❌ Declined request: {format_money(req['amount'])} from {req['requestor_id']}")
                        st.rerun()
                with c4:
                    st.caption("Pending")
        else:
            st.info("No pending requests")

    with tab3:
        st.subheader("Transaction History")
        user_tx = [t for t in st.session_state.transactions if t["sender_id"] == user["user_id"] or t["recipient_id"] == user["user_id"]]

        if user_tx:
            tx_data = []
            for tx in sorted(user_tx, key=lambda x: x["ts"], reverse=True):
                tx_type = "Sent" if tx["sender_id"] == user["user_id"] else "Received"
                amount = -tx["amount"] if tx_type == "Sent" else tx["amount"]
                status_icon = "🔄" if tx["status"] == "pending" else "✅" if tx["status"] == "completed" else "❌"
                tx_data.append({
                    "Date": tx["ts"].strftime("%Y-%m-%d %H:%M"),
                    "Type": f"{status_icon} {tx_type}",
                    "Amount": format_money(amount),
                    "Fee": format_money(tx["fee"]),
                    "Note": tx["note"],
                    "Status": tx["status"].title(),
                })
            st.dataframe(pd.DataFrame(tx_data), use_container_width=True)
        else:
            st.info("No transactions yet. Send or request money to get started!")

def show_markets(user):
    st.header("Markets")

    if not user["watchlist"]:
        c1, c2 = st.columns([3, 1])
        with c2:
            if st.button("🎯 Add Starter Watchlist", use_container_width=True, key="mk_add_watchlist"):
                user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                toast_success("Starter watchlist added!")
                add_notification("🎯 Starter watchlist added with popular stocks & crypto")
                st.rerun()

    st.subheader("Major Indices")
    indices = mini_indices()
    cols = st.columns(len(indices))
    for i, index in enumerate(indices):
        with cols[i]:
            st.metric(index["name"], format_money(index["price"]), f"{index['chg_pct']:.2f}%")

    st.subheader("Market Research")
    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        symbol = _clean_symbol(st.text_input("Symbol", value="AAPL", key="mk_symbol"))
    with c2:
        period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"], key="mk_period")
    with c3:
        chart_type = st.selectbox("Chart Type", ["Line", "Candlestick"], key="mk_chart_type")

    if symbol:
        data = get_cached_data(symbol, period)
        if data is None:
            st.error(f"No data found for {symbol}. Try a different symbol or period.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Current Price", format_money(data["current_price"]))
            with c2:
                st.metric("Change", f"{data['change']:.2f}")
            with c3:
                st.metric("Change %", f"{data['change_percent']:.2f}%")
            with c4:
                st.metric("52W Range", f"{data['52w_low']:.0f}-{data['52w_high']:.0f}")

            fig = chart(data["historical"], symbol, chart_type.lower())
            st.plotly_chart(fig, use_container_width=True)

            c5, c6 = st.columns(2)
            with c5:
                if symbol not in user["watchlist"]:
                    if st.button("Add to Watchlist", key=f"add_{symbol}"):
                        user["watchlist"].append(symbol)
                        toast_success(f"Added {symbol} to watchlist")
                        add_notification(f"📈 Added {symbol} to watchlist")
                        st.rerun()
                else:
                    if st.button("Remove from Watchlist", key=f"rm_{symbol}"):
                        user["watchlist"].remove(symbol)
                        toast_info(f"Removed {symbol} from watchlist")
                        add_notification(f"📉 Removed {symbol} from watchlist")
                        st.rerun()
            with c6:
                st.write("")

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
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center'>assets/BB_logo.png</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; font-size:108px;'><b><i>Break Bread. Build Wealth.</i></b></h3>", unsafe_allow_html=True)

    # Auth gate
    if not st.session_state.get("auth_user"):
        show_login()
        return

    show_main_app()

if __name__ == "__main__":
    main()

from market_data import *

# Quick market overview
st.header("Market Overview")
overview = get_market_overview()

for index in overview['indices']:
    st.metric(index['name'], f"${index['price']:,.2f}", f"{index['change_percent']:+.2f}%")

# Historical charts
st.header("Historical Charts")

# Bitcoin 7-day chart
btc_data = get_bitcoin_data(days=7)
if btc_data:
    fig = create_price_chart(btc_data['historical'], "Bitcoin (7 Days)")
    st.plotly_chart(fig, use_container_width=True)

# S&P 500 1-month chart
sp500_data = get_stock_data("^GSPC", "1mo")
if sp500_data:
    fig = create_performance_chart(sp500_data['historical'], "S&P 500 Performance")
    st.plotly_chart(fig, use_container_width=True)

# Treasury yields
treasury_data = get_treasury_yields()
st.write("Latest Treasury Yields:", treasury_data)
