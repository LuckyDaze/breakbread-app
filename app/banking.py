from datetime import datetime
import json, os, uuid

# --- persistence setup ---
USER_FILE = "users.json"
USERS = {}
TRANSACTIONS = []

# --- persistence helpers ---
def load_users():
    """Load users from JSON file into USERS dict."""
    global USERS
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            try:
                USERS = json.load(f)
            except json.JSONDecodeError:
                USERS = {}
    else:
        USERS = {}

def save_users():
    """Save USERS dict to JSON file."""
    with open(USER_FILE, "w") as f:
        json.dump(USERS, f, indent=2)

# --- demo users bootstrap ---
def ensure_demo_users():
    """Populate demo users if USERS is empty."""
    global USERS
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
        "ts": datetime.now(),
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
        "ts": datetime.now(),
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
        "ts": datetime.now(),
        "sender_id": "employer",
        "recipient_id": user_id,
        "amount": amount,
        "fee": 0,
        "note": "Simulated paycheck"
    })
    save_users()
    return True, f"Paycheck of ${amount:.2f} deposited."
