import streamlit as st
from app.common import get_user, find_user  # Changed import
from app.utils import uid, format_money

def ensure_demo_users():
    """Ensure demo users exist in session state."""
    if "users" not in st.session_state:
        st.session_state.users = {}
    
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
        if user["app_id"] not in [u["app_id"] for u in st.session_state.users.values()]:
            st.session_state.users[user["user_id"]] = user

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
        "ts": st.datetime.now()
    }
    st.session_state.transactions.append(transaction)
    
    return True, "Payment sent successfully"

# ... rest of your banking functions
