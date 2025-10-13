import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import yfinance as yf

# Simple CSS that won't break the app
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FE8B00 !important;
    }
    .stButton button {
        background-color: #FE8B00 !important;
        color: black !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="Break Bread",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Utility Functions
def uid():
    return str(uuid.uuid4())[:8]

def format_money(amount):
    return f"${amount:,.2f}"

# Initialize session state
if "users" not in st.session_state:
    st.session_state.users = {}
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "app_nav_radio" not in st.session_state:
    st.session_state.app_nav_radio = "Dashboard"

# Demo data setup
def ensure_demo_users():
    if not st.session_state.users:
        st.session_state.users = {
            "user_1": {
                "user_id": "user_1",
                "app_id": "janedoe", 
                "email": "jane@example.com",
                "password": "demo123",
                "balance": 5000.0,
                "portfolio": {"AAPL": {"units": 10, "avg_cost": 150.0}},
                "watchlist": ["AAPL", "GOOGL", "BTC-USD"]
            },
            "user_2": {
                "user_id": "user_2", 
                "app_id": "johndoe",
                "email": "john@example.com", 
                "password": "demo123",
                "balance": 3000.0,
                "portfolio": {},
                "watchlist": ["MSFT", "TSLA"]
            }
        }

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

# Simple UI Components
def show_login():
    st.title("🍞 Break Bread")
    st.subheader("Build Wealth Together")
    
    st.header("Welcome to Break Bread")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
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
    
    with tab2:
        st.subheader("Create Demo Account")
        st.info("This is a demo app. Use the existing accounts above to login.")

def show_dashboard(user):
    st.header("🏠 Dashboard")
    
    # Welcome message
    st.subheader(f"Welcome back, {user['app_id']}!")
    
    # Balance cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cash Balance", format_money(user["balance"]))
    
    with col2:
        portfolio_val = sum([pos["units"] * 150 for pos in user["portfolio"].values()])  # Simplified
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
        if st.button("📊 Portfolio", use_container_width=True):
            st.session_state.app_nav_radio = "Portfolio"
            st.rerun()
    
    # Recent activity
    st.subheader("Recent Activity")
    if st.session_state.transactions:
        for tx in st.session_state.transactions[-5:]:
            st.write(f"• {tx['type']}: {format_money(tx['amount'])} - {tx['date']}")
    else:
        st.info("No recent activity")

def show_banking(user):
    st.header("💸 Banking")
    
    tab1, tab2 = st.tabs(["Send Money", "Transactions"])
    
    with tab1:
        st.subheader("Send Money")
        
        recipient = st.text_input("Recipient Username", placeholder="janedoe or johndoe")
        amount = st.number_input("Amount", min_value=1.0, value=50.0, step=10.0)
        note = st.text_input("Note (optional)", placeholder="Lunch money")
        
        if st.button("Send Payment", type="primary"):
            if not recipient:
                st.error("Please enter recipient username")
            elif amount > user["balance"]:
                st.error("Insufficient funds")
            else:
                recipient_user = find_user(recipient)
                if recipient_user:
                    # Transfer money
                    user["balance"] -= amount
                    recipient_user["balance"] += amount
                    
                    # Record transaction
                    st.session_state.transactions.append({
                        "id": uid(),
                        "type": "Payment Sent",
                        "amount": amount,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "note": note
                    })
                    
                    st.success(f"Successfully sent {format_money(amount)} to {recipient}")
                    st.rerun()
                else:
                    st.error("Recipient not found")
        
        st.info("Demo users: janedoe, johndoe")
    
    with tab2:
        st.subheader("Transaction History")
        if st.session_state.transactions:
            for tx in reversed(st.session_state.transactions[-10:]):
                st.write(f"**{tx['type']}** - {format_money(tx['amount'])} - {tx['date']}")
                if tx.get('note'):
                    st.write(f"*{tx['note']}*")
                st.divider()
        else:
            st.info("No transactions yet")

def show_markets(user):
    st.header("📈 Markets")
    
    # Simple market data
    stocks = {
        "AAPL": 185.00,
        "GOOGL": 138.50,
        "MSFT": 378.85,
        "TSLA": 248.50,
        "NVDA": 475.00
    }
    
    st.subheader("Popular Stocks")
    for symbol, price in stocks.items():
        change = random.uniform(-5, 5)
        change_color = "green" if change >= 0 else "red"
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{symbol}**")
        with col2:
            st.write(format_money(price))
        with col3:
            st.write(f":{change_color}[{change:+.2f}%]")
        
        st.divider()
    
    # Simple trading
    st.subheader("Trade")
    symbol = st.selectbox("Select Stock", list(stocks.keys()))
    action = st.radio("Action", ["Buy", "Sell"])
    amount = st.number_input("Amount ($)", min_value=1.0, value=100.0)
    
    if st.button("Execute Trade", type="primary"):
        if action == "Buy" and amount > user["balance"]:
            st.error("Insufficient funds")
        else:
            st.success(f"{action} order for {format_money(amount)} of {symbol} placed!")

def show_portfolio(user):
    st.header("💼 Portfolio")
    
    if user["portfolio"]:
        st.subheader("Your Holdings")
        for symbol, position in user["portfolio"].items():
            current_price = 150.00  # Simplified
            current_value = position["units"] * current_price
            cost_basis = position["units"] * position["avg_cost"]
            pnl = current_value - cost_basis
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"**{symbol}**")
                st.write(f"{position['units']} shares")
            with col2:
                st.write("Avg Cost")
                st.write(format_money(position["avg_cost"]))
            with col3:
                st.write("Current Value")
                st.write(format_money(current_value))
            with col4:
                pnl_color = "green" if pnl >= 0 else "red"
                st.write("P/L")
                st.write(f":{pnl_color}[{format_money(pnl)}]")
            
            st.divider()
    else:
        st.info("You don't have any investments yet.")
    
    # Watchlist
    st.subheader("Watchlist")
    for symbol in user.get("watchlist", []):
        st.write(f"📈 {symbol}")

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

def show_main_app():
    user = get_user(st.session_state.auth_user)
    if not user:
        logout()
        return
    
    # Sidebar
    with st.sidebar:
        st.title("🍞 Break Bread")
        st.write(f"Welcome, **{user['app_id']}**")
        st.write(f"Cash: **{format_money(user['balance'])}**")
        st.divider()
        
        # Navigation
        nav_options = ["Dashboard", "Banking", "Markets", "Portfolio", "Settings"]
        selected_nav = st.radio("Navigation", nav_options, 
                               index=nav_options.index(st.session_state.app_nav_radio) 
                               if st.session_state.app_nav_radio in nav_options else 0)
        
        # Update the navigation state
        if selected_nav != st.session_state.app_nav_radio:
            st.session_state.app_nav_radio = selected_nav
            st.rerun()
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            logout()
    
    # Main content
    if st.session_state.app_nav_radio == "Dashboard":
        show_dashboard(user)
    elif st.session_state.app_nav_radio == "Banking":
        show_banking(user)
    elif st.session_state.app_nav_radio == "Markets":
        show_markets(user)
    elif st.session_state.app_nav_radio == "Portfolio":
        show_portfolio(user)
    elif st.session_state.app_nav_radio == "Settings":
        show_settings(user)

# Main app
def main():
    ensure_demo_users()
    
    if st.session_state.auth_user is None:
        show_login()
    else:
        show_main_app()

if __name__ == "__main__":
    main()
