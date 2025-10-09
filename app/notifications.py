import streamlit as st
import random
from datetime import datetime
from app.market_data import get_cached_data

def add_notification(message, user_id="system"):
    """Store a notification in session state."""
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    st.session_state.notifications.append({
        'timestamp': datetime.now(),
        'user_id': user_id,
        'message': message
    })
    # keep only the last 50
    if len(st.session_state.notifications) > 50:
        st.session_state.notifications = st.session_state.notifications[-50:]

def get_notifications(user_id=None):
    """Retrieve notifications, optionally filtered by user_id."""
    notes = st.session_state.get('notifications', [])
    if user_id:
        return [n for n in notes if n['user_id'] == user_id]
    return notes

def toast_success(message):
    st.toast(f"✅ {message}")
    add_notification(message)

def toast_info(message):
    st.toast(f"ℹ️ {message}")
    add_notification(message)

def toast_warn(message):
    st.toast(f"⚠️ {message}")
    add_notification(message)

def price_alerts_tick(user):
    """Occasionally trigger price alerts for a user's watchlist."""
    if 'price_alerts' not in user.get('settings', {}):
        return
    # 10% chance per render to avoid spamming
    if random.random() > 0.1:
        return
    for symbol, threshold in user['settings']['price_alerts'].items():
        data = get_cached_data(symbol, "1d")
        if data and data['current_price'] >= threshold:
            msg = f"🚨 Price alert: {symbol} reached ${threshold:,.2f}!"
            st.toast(msg)
            add_notification(msg, user_id=user["user_id"])
