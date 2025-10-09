import streamlit as st
from datetime import datetime

def send_notification(user_id, message):
    """Store a notification in session state."""
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    st.session_state.notifications.append({
        'timestamp': datetime.now(),
        'user_id': user_id,
        'message': message
    })
    if len(st.session_state.notifications) > 50:
        st.session_state.notifications = st.session_state.notifications[-50:]
    return True

def get_notifications(user_id=None):
    """Get all notifications, or filter by user_id."""
    notes = st.session_state.get('notifications', [])
    if user_id:
        return [n for n in notes if n['user_id'] == user_id]
    return notes

def toast_success(message):
    st.toast(f"✅ {message}")
    send_notification("system", message)

def toast_info(message):
    st.toast(f"ℹ️ {message}")
    send_notification("system", message)

def toast_warn(message):
    st.toast(f"⚠️ {message}")
    send_notification("system", message)
