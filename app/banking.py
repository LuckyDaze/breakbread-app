import streamlit as st
from app.utils import uid
from datetime import datetime

def hash_password(password):
    """Consistent password hashing - MUST match security.py"""
    import hashlib
    return hashlib.sha256(f"breakbread_{password}_salt".encode()).hexdigest()

def ensure_demo_users():
    """Populate demo users with consistent data structure"""
    if "users" not in st.session_state:
        st.session_state.users = {}
    
    # Demo users with password_hash field for compatibility
    demo_users = {
        "user_1": {
            "user_id": "user_1", 
            "app_id": "johndoe", 
            "email": "john@example.com",
            "password_hash": hash_password("demo123"),  # Consistent hashing
            "balance": 1500.00,
            "watchlist": ["AAPL", "TSLA"],
            "portfolio": {},
            "settings": {
                "dark_mode": False,
                "price_alerts": {},
                "notification_preferences": {"email": True, "push": True}
            },
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "verified": True
        },
        "user_2": {
            "user_id": "user_2", 
            "app_id": "janedoe", 
            "email": "jane@example.com",
            "password_hash": hash_password("demo123"),  # Consistent hashing
            "balance": 2500.00,
            "watchlist": ["BTC-USD", "ETH-USD"],
            "portfolio": {
                "AAPL": {"units": 3.0, "avg_cost": 175.50},
                "BTC-USD": {"units": 0.02, "avg_cost": 42000.00}
            },
            "settings": {
                "dark_mode": True,
                "price_alerts": {"BTC-USD": 70000},
                "notification_preferences": {"email": True, "push": True}
            },
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "verified": True
        }
    }
    
    # Only add demo users if they don't exist
    for user_id, user_data in demo_users.items():
        if user_id not in st.session_state.users:
            st.session_state.users[user_id] = user_data

def register_user(app_id, email, password, personal=None, banking=None, initial_deposit=0.0):
    """Register a new user with enhanced profile data"""
    # Check if user already exists
    if any(user.get('app_id') == app_id for user in st.session_state.users.values()):
        return False, "Username already exists", None
    
    if any(user.get('email') == email for user in st.session_state.users.values()):
        return False, "Email already registered", None
    
    # Create new user
    user_id = uid()
    new_user = {
        "user_id": user_id,
        "app_id": app_id,
        "email": email,
        "password_hash": hash_password(password),  # Use the same hash function
        "balance": float(initial_deposit),
        "watchlist": [],
        "portfolio": {},
        "personal_info": personal or {},
        "banking_info": banking or {},
        "settings": {
            "dark_mode": False,
            "price_alerts": {},
            "notification_preferences": {"email": True, "push": True}
        },
        "created_at": datetime.now(),
        "last_login": datetime.now(),
        "verified": False
    }
    
    # Add to users database
    st.session_state.users[user_id] = new_user
    
    # Add welcome notification
    from app.notifications import add_notification
    add_notification(f"👋 Welcome to Break Bread, {app_id}!")
    
    return True, f"Account created successfully for {app_id}", user_id

def get_user(user_id):
    """Get user by ID"""
    return st.session_state.users.get(user_id)

def find_user(identifier):
    """Find user by app_id, email, or phone"""
    for user in st.session_state.users.values():
        if (user['app_id'] == identifier or 
            user.get('email') == identifier or 
            user.get('personal_info', {}).get('phone') == identifier):
            return user
    return None

def send_money(sender_id, recipient_identifier, amount, note=""):
    """Send money to another user"""
    if amount <= 0:
        return False, "Amount must be positive"
    
    sender = get_user(sender_id)
    if not sender:
        return False, "Sender not found"
    
    recipient = find_user(recipient_identifier)
    if not recipient:
        return False, "Recipient not found"
    
    if sender_id == recipient['user_id']:
        return False, "Cannot send money to yourself"
    
    fee = amount * 0.015  # 1.5% fee
    total_debit = amount + fee
    
    if sender['balance'] < total_debit:
        return False, "Insufficient funds"
    
    # Create transaction
    transaction = {
        "tx_id": uid(),
        "sender_id": sender_id,
        "recipient_id": recipient['user_id'],
        "amount": amount,
        "fee": fee,
        "note": note,
        "status": "pending",
        "ts": datetime.now()
    }
    
    # Record transaction
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    st.session_state.transactions.append(transaction)
    
    # Simulate processing
    import time
    time.sleep(0.5)
    
    # Update balances
    transaction["status"] = "completed"
    sender['balance'] -= total_debit
    recipient['balance'] += amount
    
    return True, f"Sent ${amount:.2f} to {recipient['app_id']} (fee ${fee:.2f})"

def request_money(requestor_id, from_identifier, amount, note=""):
    """Request money from another user"""
    if amount <= 0:
        return False, "Amount must be positive"
    
    requestor = get_user(requestor_id)
    if not requestor:
        return False, "Requestor not found"
    
    from_user = find_user(from_identifier)
    if not from_user:
        return False, "User not found"
    
    # Create request
    request = {
        "request_id": uid(),
        "requestor_id": requestor_id,
        "recipient_id": from_user['user_id'],
        "amount": amount,
        "note": note,
        "ts": datetime.now(),
        "status": "pending"
    }
    
    # Record request
    if "requests" not in st.session_state:
        st.session_state.requests = []
    st.session_state.requests.append(request)
    
    return True, "Money request sent successfully"

def simulate_paycheck(user_id, amount=2000.00):
    """Simulate a paycheck deposit"""
    user = get_user(user_id)
    if not user:
        return False, "User not found"
    
    # Create paycheck transaction
    transaction = {
        "tx_id": uid(),
        "sender_id": "employer_system",
        "recipient_id": user_id,
        "amount": amount,
        "fee": 0.00,
        "note": "Monthly salary deposit",
        "status": "completed",
        "ts": datetime.now()
    }
    
    # Record transaction
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    st.session_state.transactions.append(transaction)
    
    # Update balance
    user['balance'] += amount
    
    return True, f"Paycheck of ${amount:.2f} deposited successfully"
