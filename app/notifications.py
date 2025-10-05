import streamlit as st
import random
from datetime import datetime
from app.market_data import get_cached_data

def send_notification(user_id, message):
    return f"Notification to {user_id}: {message}"

def get_notifications(user_id):
    return [f"Welcome back, {user_id}!", "Your balance has been updated."]

def toast_success(message):
    st.toast(f"✅ {message}")
    add_notification(message)

def toast_info(message):
    st.toast(f"ℹ️ {message}")
    add_notification(message)

def toast_warn(message):
    st.toast(f"⚠️ {message}")
    add_notification(message)

def add_notification(message):
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    st.session_state.notifications.append({
        'timestamp': datetime.now(),
        'message': message
    })
    if len(st.session_state.notifications) > 50:
        st.session_state.notifications = st.session_state.notifications[-50:]

def get_notifications():
    return st.session_state.get('notifications', [])

def price_alerts_tick(user):
    if 'price_alerts' not in user.get('settings', {}):
        return
    # 10% chance per render to avoid spam
    if random.random() > 0.1:
        return
    for symbol, threshold in user['settings']['price_alerts'].items():
        data = get_cached_data(symbol, "1d")
        if data and data['current_price'] >= threshold:
            msg = f"🚨 Price alert: {symbol} reached ${threshold:,.2f}!"
            st.toast(msg)
            add_notification(msg)
