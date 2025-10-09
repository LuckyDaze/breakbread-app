import streamlit as st
from app.utils import uid, format_money
from datetime import datetime, timedelta   # ← add timedelta
import hashlib

# ... keep your PaymentProcessor, ensure_demo_users, get_user, find_user, send_money, request_money, simulate_paycheck, etc ...

def get_transaction_history(user_id, limit=50):
    # unchanged
    ...

def get_account_summary(user_id):
    # unchanged
    ...

# --- NEW: basic demo registration (persists in session_state) ---
def _app_id_taken(app_id: str) -> bool:
    for u in st.session_state.get("users", {}).values():
        if u.get("app_id") == app_id:
            return True
    return False

def register_user(app_id: str, email: str, password: str, personal: dict, banking: dict, initial_deposit: float = 0.0):
    if not app_id or not email or not password:
        return False, "Username, email and password are required.", None
    if _app_id_taken(app_id):
        return False, "That username is already taken.", None

    user_id = uid()
    st.session_state.setdefault("users", {})
    st.session_state.users[user_id] = {
        "user_id": user_id,
        "app_id": app_id,
        "email": email,
        "password": password,  # DEMO ONLY (don’t do this in prod)
        "balance": float(initial_deposit or 0.0),
        "watchlist": [],
        "portfolio": {},
        "settings": {"dark_mode": True, "price_alerts": {}, "risk_profile": "moderate"},
        "profile": {"personal": personal, "banking": banking},
        "created_at": datetime.now(),
        "last_login": datetime.now(),
    }

    if initial_deposit and initial_deposit > 0:
        st.session_state.setdefault("transactions", [])
        st.session_state.transactions.append({
            "tx_id": uid(),
            "sender_id": "initial_deposit",
            "recipient_id": user_id,
            "amount": float(initial_deposit),
            "fee": 0.0,
            "note": "Initial deposit at sign-up",
            "status": "completed",
            "created_at": datetime.now(),
            "ts": datetime.now(),
            "completed_at": datetime.now(),
        })

    return True, "Account created! You can log in now.", user_id
