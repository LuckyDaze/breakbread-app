
import streamlit as st
from app.utils import uid
from datetime import datetime

def hash_password(password):
    """Consistent password hashing - MUST match security.py"""
    import hashlib
    return hashlib.sha256(f"breakbread_{password}_salt".encode()).hexdigest()

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

# --- demo users bootstrap ---
def ensure_demo_users():
    """Populate demo users if USERS is empty."""
    global USERS
    load_users()
    if USERS:
        return
    USERS = {
        "u1": {"user_id": "u1", "app_id": "johndoe", "email": "john@x.com",
               "password": "secret123", "balance": 1500.00},
        "u2": {"user_id": "u2", "app_id": "janedoe", "email": "jane@x.com",
               "password": "pass456", "balance": 900.00},
    }
    save_users()

# --- user management ---
def register_user(app_id, email, password):
    """Register a new user and persist to JSON."""
    load_users()
    for u in USERS.values():
        if u["app_id"] == app_id or u["email"] == email:
            return False, "User already exists."

    user_id = str(uuid.uuid4())[:8]
    USERS[user_id] = {
        "user_id": user_id,
        "app_id": app_id,
        "email": email,
        "password": password,   # ⚠️ plain text for demo only
        "balance": 0.0,
    }
    save_users()
    return True, f"User {app_id} registered successfully!"

def _find_user(identifier):
    """Find a user by username, email, or phone."""
    for u in USERS.values():
        if identifier in (u["app_id"], u.get("email"), u.get("phone")):
            return u
    return None

def find_user(identifier):
    return _find_user(identifier)

def get_user(identifier):
    return _find_user(identifier)

# --- banking operations ---
def send_money(sender_id, recipient_identifier, amount, note=""):
    sender = USERS.get(sender_id)
    recipient = _find_user(recipient_identifier)
    if not sender or not recipient:
        return False, "User not found."

    fee = round(amount * 0.015, 2)
    total = amount + fee
    if sender["balance"] < total:
        return False, "Insufficient funds."

    sender["balance"] -= total
    recipient["balance"] += amount
    TRANSACTIONS.append({
        "ts": datetime.now().isoformat(),
        "sender_id": sender_id,
        "recipient_id": recipient["user_id"],
        "amount": amount,
        "fee": fee,
        "note": note
    })
    save_users()
    return True, f"Sent ${amount:.2f} to {recipient['app_id']} (fee ${fee:.2f})."

def request_money(requester_id, sender_identifier, amount, note=""):
    sender = _find_user(sender_identifier)
    requester = USERS.get(requester_id)
    if not sender or not requester:
        return False, "User not found."
    if sender["balance"] < amount:
        return False, "Insufficient funds."

    sender["balance"] -= amount
    requester["balance"] += amount
    TRANSACTIONS.append({
        "ts": datetime.now().isoformat(),
        "sender_id": sender["user_id"],
        "recipient_id": requester_id,
        "amount": amount,
        "fee": 0,
        "note": note
    })
    save_users()
    return True, f"Requested ${amount:.2f} from {sender['app_id']}."

def simulate_paycheck(user_id, amount=1000.00):
    user = USERS.get(user_id)
    if not user:
        return False, "User not found."

    user["balance"] += amount
    TRANSACTIONS.append({
        "ts": datetime.now().isoformat(),
        "sender_id": "employer",
        "recipient_id": user_id,
        "amount": amount,
        "fee": 0,
        "note": "Simulated paycheck"
    })
    save_users()
    return True, f"Paycheck of ${amount:.2f} deposited."
