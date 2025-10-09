import streamlit as st
import random
from datetime import datetime
from app.banking import find_user, get_user

def hash_password(password):
    """Consistent password hashing - MUST match banking.py"""
    import hashlib
    return hashlib.sha256(f"breakbread_{password}_salt".encode()).hexdigest()

def fake_login(username, password=None):
    """Enhanced to handle both login patterns with proper password checking"""
    if password is None:
        # This is a 2FA verification attempt
        if isinstance(username, str) and len(username) == 6 and username.isdigit():
            # username is actually the 2FA code in this case
            code = username
            return _verify_2fa(code)
        else:
            return {"status": "FAILED", "message": "Invalid 2FA code format"}
    
    # Regular username/password login
    user = find_user(username)
    if not user:
        return {"status": "FAILED", "message": "User not found"}
    
    # Check if this is a demo user (has no password_hash) or registered user
    if "password_hash" not in user:
        # Demo user - check against demo password
        if password == "demo123":
            # For demo users, sometimes require 2FA for realism
            if random.random() > 0.3:  # 70% chance of requiring 2FA
                st.session_state["_pending_2fa_user"] = username
                st.session_state["_pending_2fa_code"] = str(random.randint(100000, 999999))
                return {"status": "2FA_REQUIRED", "message": "2FA code sent to your device"}
            else:
                return {"status": "SUCCESS", "user_id": user["user_id"]}
        else:
            return {"status": "FAILED", "message": "Invalid credentials"}
    else:
        # Registered user - check against stored hash
        input_hash = hash_password(password)
        if input_hash == user["password_hash"]:
            # For registered users, sometimes require 2FA for realism
            if random.random() > 0.3:  # 70% chance of requiring 2FA
                st.session_state["_pending_2fa_user"] = username
                st.session_state["_pending_2fa_code"] = str(random.randint(100000, 999999))
                return {"status": "2FA_REQUIRED", "message": "2FA code sent to your device"}
            else:
                return {"status": "SUCCESS", "user_id": user["user_id"]}
        else:
            return {"status": "FAILED", "message": "Invalid credentials"}

def _verify_2fa(code):
    """Verify 2FA code"""
    username = st.session_state.get("_pending_2fa_user")
    expected_code = st.session_state.get("_pending_2fa_code")
    
    if not username or not expected_code:
        return {"status": "FAILED", "message": "No pending verification"}
    
    # In demo, accept any 6-digit code
    if len(code) == 6 and code.isdigit():
        user = find_user(username)
        if user:
            # Clear pending state
            if "_pending_2fa_user" in st.session_state:
                del st.session_state["_pending_2fa_user"]
            if "_pending_2fa_code" in st.session_state:
                del st.session_state["_pending_2fa_code"]
            
            return {"status": "SUCCESS", "user_id": user["user_id"]}
    
    return {"status": "FAILED", "message": "Invalid verification code"}

def logout():
    """Enhanced logout"""
    st.session_state.auth_user = None
    # Clear any pending auth state
    for key in list(st.session_state.keys()):
        if key.startswith('_pending_'):
            del st.session_state[key]

def fraud_check(transaction_data):
    """Enhanced fraud detection with more rules"""
    warnings = []
    amt = transaction_data.get("amount", 0) or 0
    
    # Rule-based detection
    if amt > 1000:
        warnings.append("Large transaction amount detected")
    
    # Velocity check
    recent_tx = [
        t for t in st.session_state.get("transactions", [])
        if t["sender_id"] == transaction_data.get("sender_id")
        and (datetime.now() - t["ts"]).total_seconds() < 300  # 5 minutes
    ]
    if len(recent_tx) >= 3:
        warnings.append("Multiple rapid transactions detected")
    
    # New recipient check for larger amounts
    if amt > 500:
        sender_id = transaction_data.get("sender_id")
        recipient_id = transaction_data.get("recipient_id")
        
        if sender_id and recipient_id:
            # Check if this recipient is new to the sender
            previous_to_recipient = any(
                t for t in st.session_state.get("transactions", [])
                if t["sender_id"] == sender_id and t["recipient_id"] == recipient_id
            )
            if not previous_to_recipient:
                warnings.append("First time sending to this recipient")
    
    return warnings
