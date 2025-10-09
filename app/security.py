import streamlit as st
from app.common import get_user, find_user

def fake_login(username=None, code=None):
    """Demo login with optional 2FA simulation."""
    if code and len(code) == 6 and code.isdigit():
        # 2FA verification - accept any 6-digit code in demo
        return {"status": "SUCCESS", "user_id": "user_1"}  # Default to first user
    
    user = find_user(username)
    if user and user.get("password") == "demo123":  # Simple demo auth
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
