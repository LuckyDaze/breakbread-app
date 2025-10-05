import os
from datetime import datetime

import pandas as pd
import streamlit as st

# Import app modules
from app.banking import ensure_demo_users, send_money, request_money, get_user, find_user, simulate_paycheck
from app.market_data import get_cached_data, chart, mini_indices
from app.investing import place_order, portfolio_value, unrealized_gains, allocation_breakdown
from app.security import fake_login, logout, fraud_check
from app.notifications import (
    toast_success,
    toast_info,
    toast_warn,
    price_alerts_tick,
    add_notification,
    get_notifications,
)
from app.utils import uid, format_money, seed_price_path
from app.analytics import diversification_score
from app.banking import ensure_demo_users, send_money, request_money, get_user, find_user, simulate_paycheck
# Page configuration
st.set_page_config(
    page_title="Break Bread",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "users" not in st.session_state:
    st.session_state.users = {}
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "orders" not in st.session_state:
    st.session_state.orders = []
if "requests" not in st.session_state:
    st.session_state.requests = []
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if "login_2fa_code" not in st.session_state:
    st.session_state.login_2fa_code = None
if "notifications" not in st.session_state:
    st.session_state.notifications = []

# Ensure demo users exist
ensure_demo_users()


def _clean_symbol(text: str) -> str:
    """Normalize ticker inputs."""
    return (text or "").strip().upper()


def main():
    # Header with logo fallback
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = "assets/BB_logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("<h2 style='text-align:center'>🍞 Break Bread</h2>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='text-align: center; font-size:36px;'><b><i>Break Bread. Build Wealth.</i></b></h3>",
            unsafe_allow_html=True,
        )

    # Authentication
    if not st.session_state.auth_user:
        show_login()
        return

    # Main app for authenticated users
    show_main_app()


def show_login():
    st.header("Welcome to Break Bread")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Login")
        app_id = st.text_input("App ID", placeholder="janedoe or johndoe")
        password = st.text_input("Password", type="password", value="demo123")

        if st.button("Login", type="primary"):
            result = fake_login(app_id)
            if result["status"] == "2FA_REQUIRED":
                st.info("2FA code sent (simulated). Enter any 6-digit code on the right.")
            else:
                st.error(result.get("message", "Login failed"))

    with col2:
        st.subheader("Enter 2FA Code")
        code = st.text_input("6-digit code", placeholder="123456")
        if st.button("Verify Code"):
            result = fake_login(None, code)  # second step
            if result["status"] == "SUCCESS":
                st.session_state.auth_user = result["user_id"]

                # Add starter watchlist for first-time users
                user = get_user(result["user_id"])
                if not user["watchlist"] and len(user["portfolio"]) <= 1:
                    user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                    add_notification("🎯 Starter watchlist added! Check out popular stocks and crypto.")

                toast_success("Login successful!")
                st.rerun()
            else:
                st.error(result.get("message", "Invalid code"))


def show_main_app():
    user = get_user(st.session_state.auth_user)

    # Run price alerts check
    price_alerts_tick(user)

    # Sidebar
    with st.sidebar:
        st.header(f"Welcome, {user['app_id']}!")
        st.metric("Cash Balance", format_money(user["balance"]))

        # Market overview
        st.subheader("Market Overview")
        indices = mini_indices()
        for index in indices:
            st.metric(index["name"], format_money(index["price"]), f"{index['chg_pct']:.2f}%")

        # Navigation
        st.divider()
        nav = st.radio("Navigation", ["Dashboard", "Banking", "Markets", "Portfolio", "Settings"])

        if st.button("Logout"):
            logout()
            st.rerun()

    # Notifications tray (right sidebar)
    with st.sidebar:
        st.divider()
        with st.expander("🔔 Notifications", expanded=False):
            notifications = get_notifications()
            if notifications:
                for i, notif in enumerate(notifications[-10:]):  # Show last 10
                    st.caption(f"{notif['timestamp'].strftime('%H:%M')} - {notif['message']}")
                if st.button("Clear All", key="clear_notifications"):
                    st.session_state.notifications = []
                    st.rerun()
            else:
                st.info("No notifications")

    # Main content
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

    # Key metrics
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
        recent_tx = len(
            [
                t
                for t in st.session_state.transactions
                if t["sender_id"] == user["user_id"] and (datetime.now() - t["ts"]).days <= 7
            ]
        )
        st.metric("Weekly Transactions", recent_tx)

    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💰 Simulate Paycheck", use_container_width=True):
            success, message = simulate_paycheck(user["user_id"])
            if success:
                toast_success("Paycheck deposited!")
                add_notification("💰 Paycheck deposited: $2,000.00")
                st.rerun()

    with col2:
        if st.button("📈 Add Starter Watchlist", use_container_width=True):
            if not user["watchlist"]:
                user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                toast_success("Starter watchlist added!")
                add_notification("🎯 Starter watchlist added with popular stocks & crypto")
                st.rerun()
            else:
                toast_info("You already have a watchlist!")

    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # Portfolio chart (simulated)
    st.subheader("Portfolio Value (Last 30 Days)")
    base_value = total_value * 0.9  # Start slightly lower
    historical_values = seed_price_path(base_value, 30)
    chart_data = pd.DataFrame(
        {"Date": pd.date_range(end=datetime.now(), periods=30), "Portfolio Value": historical_values}
    )
    st.line_chart(chart_data.set_index("Date"))

    # Recent activity
    st.subheader("Recent Activity")
    user_activities = []
    for tx in st.session_state.transactions[-10:]:
        if tx["sender_id"] == user["user_id"] or tx["recipient_id"] == user["user_id"]:
            status_icon = "🔄" if tx["status"] == "pending" else "✅" if tx["status"] == "completed" else "❌"
            user_activities.append(
                {
                    "Type": f"{status_icon} Payment",
                    "Amount": f"-{format_money(tx['amount'])}"
                    if tx["sender_id"] == user["user_id"]
                    else f"+{format_money(tx['amount'])}",
                    "Description": tx["note"],
                    "Date": tx["ts"].strftime("%Y-%m-%d"),
                    "Status": tx["status"].title(),
                }
            )

    for order in st.session_state.orders[-5:]:
        if order["user_id"] == user["user_id"]:
            user_activities.append(
                {
                    "Type": f"📊 {order['side'].title()} {order['symbol']}",
                    "Amount": format_money(order["value"]),
                    "Description": f"{order['units']:.4f} units @ {format_money(order['fill_price'])}",
                    "Date": order["ts"].strftime("%Y-%m-%d"),
                    "Status": order["status"].title(),
                }
            )

    if user_activities:
        st.dataframe(pd.DataFrame(user_activities), use_container_width=True)
    else:
        st.info("No recent activity. Start by sending money or making investments!")


def show_banking(user):
    st.header("Banking")

    # Quick paycheck simulation at top
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("💰 Simulate Paycheck", use_container_width=True, type="secondary"):
            success, message = simulate_paycheck(user["user_id"])
            if success:
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
                # Fraud check
                fake_tx = {"sender_id": user["user_id"], "recipient_id": recipient_id, "amount": amount}
                warnings = fraud_check(fake_tx)

                if warnings:
                    for warning in warnings:
                        toast_warn(warning)
                        add_notification(f"⚠️ {warning}")

                success, message = send_money(user["user_id"], recipient_id, amount, note)
                if success:
                    toast_success(f"Sent {format_money(amount)} to {recipient_id}")
                    add_notification(f"💸 Sent {format_money(amount)} to {recipient_id}")
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        st.subheader("Request Money")
        from_id = st.text_input("From App ID or Email")
        req_amount = st.number_input("Amount to Request", min_value=0.01, step=1.0)
        req_note = st.text_input("Request Note")

        if st.button("Send Request"):
            success, message = request_money(user["user_id"], from_id, req_amount, req_note)
            if success:
                toast_success("Money request sent")
                add_notification(f"📥 Money request sent: {format_money(req_amount)} to {from_id}")
            else:
                st.error(message)

        # Show pending requests
        st.subheader("Pending Requests")
        user_requests = [r for r in st.session_state.requests if r["recipient_id"] == user["user_id"]]
        if user_requests:
            for req in user_requests:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{format_money(req['amount'])}** from {req['requestor_id']}")
                    st.caption(req["note"])
                with col2:
                    if st.button("Pay", key=f"pay_{req['request_id']}"):
                        success, _ = send_money(
                            user["user_id"], req["requestor_id"], req["amount"], "Request payment"
                        )
                        if success:
                            st.session_state.requests = [
                                r for r in st.session_state.requests if r["request_id"] != req["request_id"]
                            ]
                            add_notification(
                                f"✅ Paid request: {format_money(req['amount'])} to {req['requestor_id']}"
                            )
                            st.rerun()
                with col3:
                    if st.button("Decline", key=f"decline_{req['request_id']}"):
                        st.session_state.requests = [
                            r for r in st.session_state.requests if r["request_id"] != req["request_id"]
                        ]
                        add_notification(
                            f"❌ Declined request: {format_money(req['amount'])} from {req['requestor_id']}"
                        )
                        st.rerun()
                with col4:
                    st.caption("Pending")
        else:
            st.info("No pending requests")

    with tab3:
        st.subheader("Transaction History")
        user_tx = [
            t
            for t in st.session_state.transactions
            if t["sender_id"] == user["user_id"] or t["recipient_id"] == user["user_id"]
        ]

        if user_tx:
            tx_data = []
            for tx in sorted(user_tx, key=lambda x: x["ts"], reverse=True):
                tx_type = "Sent" if tx["sender_id"] == user["user_id"] else "Received"
                amount = -tx["amount"] if tx_type == "Sent" else tx["amount"]
                status_icon = "🔄" if tx["status"] == "pending" else "✅" if tx["status"] == "completed" else "❌"
                tx_data.append(
                    {
                        "Date": tx["ts"].strftime("%Y-%m-%d %H:%M"),
                        "Type": f"{status_icon} {tx_type}",
                        "Amount": format_money(amount),
                        "Fee": format_money(tx["fee"]),
                        "Note": tx["note"],
                        "Status": tx["status"].title(),
                    }
                )
            st.dataframe(pd.DataFrame(tx_data), use_container_width=True)
        else:
            st.info("No transactions yet. Send or request money to get started!")


def show_markets(user):
    st.header("Markets")

    # Quick watchlist action
    if not user["watchlist"]:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🎯 Add Starter Watchlist", use_container_width=True):
                user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                toast_success("Starter watchlist added!")
                add_notification("🎯 Starter watchlist added with popular stocks & crypto")
                st.rerun()

    # Market indices at top
    st.subheader("Major Indices")
    indices = mini_indices()
    cols = st.columns(len(indices))
    for i, index in enumerate(indices):
        with cols[i]:
            st.metric(index["name"], format_money(index["price"]), f"{index['chg_pct']:.2f}%")

    # Symbol search and chart
    st.subheader("Market Research")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        symbol = _clean_symbol(st.text_input("Symbol", value="AAPL"))
    with col2:
        period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"])
    with col3:
        chart_type = st.selectbox("Chart Type", ["Line", "Candlestick"])

    if symbol:
        data = get_cached_data(symbol, period)
        if data is None:
            st.error(f"No data found for {symbol}. Try a different symbol or period.")
        else:
            # Current price info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", format_money(data["current_price"]))
            with col2:
                st.metric("Change", f"{data['change']:.2f}")
            with col3:
                st.metric("Change %", f"{data['change_percent']:.2f}%")
            with col4:
                st.metric("52W Range", f"{data['52w_low']:.0f}-{data['52w_high']:.0f}")

            # Chart
            fig = chart(data["historical"], symbol, chart_type.lower())
            st.plotly_chart(fig, use_container_width=True)

            # Quick actions
            col1, col2 = st.columns(2)
            with col1:
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

            with col2:
                st.write("")  # Spacer


def show_portfolio(user):
    st.header("Portfolio")

    # Quick actions
    if not user["watchlist"]:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🎯 Add Starter Watchlist", use_container_width=True):
                user["watchlist"] = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
                toast_success("Starter watchlist added!")
                add_notification("🎯 Starter watchlist added with popular stocks & crypto")
                st.rerun()

    # Portfolio summary
    col1, col2, col3 = st.columns(3)

    with col1:
        total_value = portfolio_value(user["user_id"])
        st.metric("Portfolio Value", format_money(total_value))

    with col2:
        unrealized = unrealized_gains(user["user_id"])
        st.metric("Unrealized P/L", format_money(unrealized))

    with col3:
        div_score = diversification_score(user["user_id"])
        st.metric("Diversification Score", f"{div_score}/100")

    # Trading interface
    st.subheader("Trade")
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        symbol = _clean_symbol(st.text_input("Symbol", value="AAPL", key="trade_symbol"))
    with col2:
        side = st.selectbox("Side", ["buy", "sell"])
    with col3:
        if side == "buy":
            cash_amount = st.number_input("Amount ($)", min_value=1.0, value=100.0)
            units = None
        else:
            # Safe unit input for selling
            available_units = float(user["portfolio"].get(symbol, {}).get("units", 0))
            if available_units > 0:
                units = st.number_input(
                    "Units",
                    min_value=0.01,
                    max_value=available_units,
                    value=min(1.0, available_units),
                    step=0.1,
                    help=f"Available: {available_units:.4f} units",
                )
            else:
                st.info("No units available to sell for this symbol.")
                units = None
            cash_amount = None
    with col4:
        st.write("")  # Spacer
        if st.button("Place Order", type="primary"):
            success, message, order = place_order(user["user_id"], symbol, side, cash_amount, units)
            if success:
                action = "bought" if side == "buy" else "sold"
                toast_success(f"Order filled: {action} {order['units']:.4f} {symbol}")
                add_notification(f"📊 {action.title()} {order['units']:.4f} {symbol} for {format_money(order['value'])}")
                st.rerun()
            else:
                st.error(message)

    # Positions table
    st.subheader("Positions")
    if user["portfolio"]:
        positions_data = []
        for sym, position in user["portfolio"].items():
            data = get_cached_data(sym, "1d")
            if data:
                current_price = data["current_price"]
                value = position["units"] * current_price
                cost_basis = position["units"] * position["avg_cost"]
                unrealized_pl = value - cost_basis
                unrealized_pct = (unrealized_pl / cost_basis) * 100 if cost_basis > 0 else 0

                positions_data.append(
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

        if positions_data:
            st.dataframe(pd.DataFrame(positions_data), use_container_width=True)
        else:
            st.info("Position data temporarily unavailable")
    else:
        st.info("No positions yet. Buy stocks or crypto to build your portfolio!")

    # Watchlist
    st.subheader("Watchlist")
    if user["watchlist"]:
        for sym in list(user["watchlist"]):
            data = get_cached_data(sym, "1d")
            if data:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.write(f"**{sym}**")
                with col2:
                    st.metric("Price", format_money(data["current_price"]), f"{data['change_percent']:.2f}%")
                with col3:
                    if st.button("View", key=f"view_{sym}"):
                        st.info(f"View {sym} in Markets tab")
                with col4:
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

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Preferences")
        dark_mode = st.toggle("Dark Mode", value=user["settings"]["dark_mode"])
        if dark_mode != user["settings"]["dark_mode"]:
            user["settings"]["dark_mode"] = dark_mode
            toast_success("Preferences updated")
            add_notification("⚙️ Preferences updated")

    with col2:
        st.subheader("Price Alerts")
        symbol = _clean_symbol(st.text_input("Symbol for Alert", value="BTC-USD"))
        threshold = st.number_input("Alert Threshold ($)", min_value=0.01, value=50000.0)

        if st.button("Set Alert"):
            if symbol:
                user["settings"]["price_alerts"][symbol] = threshold
                toast_success(f"Alert set for {symbol} at {format_money(threshold)}")
                add_notification(f"🔔 Price alert set: {symbol} at {format_money(threshold)}")
            else:
                st.warning("Enter a valid symbol before setting an alert.")

        # Show current alerts
        if user["settings"]["price_alerts"]:
            st.write("Current Alerts:")
            for alert_symbol, alert_threshold in list(user["settings"]["price_alerts"].items()):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{alert_symbol}: {format_money(alert_threshold)}")
                with col2:
                    if st.button("Remove", key=f"remove_alert_{alert_symbol}"):
                        del user["settings"]["price_alerts"][alert_symbol]
                        add_notification(f"🔕 Price alert removed: {alert_symbol}")
                        st.rerun()


if __name__ == "__main__":
    main()
