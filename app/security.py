# app/security.py

# Demo users (for testing only)
USERS = {
    "johndoe": {"password": "secret123", "locked": False},
    "janedoe": {"password": "pass456", "locked": False},
}

def fake_login(username, password):
    """Simulate a login check."""
    user = USERS.get(username)
    if not user:
        return False, "User not found."
    if user["locked"]:
        return False, "Account locked."
    if user["password"] != password:
        return False, "Invalid password."
    return True, f"Welcome {username}!"

def logout(username):
    """Simulate logging out a user."""
    if username in USERS:
        return True, f"{username} logged out."
    return False, "User not found."

def fraud_check(user_id, transaction):
    """Very simple fraud check stub."""
    amount = transaction.get("amount", 0)
    if amount > 5000:  # arbitrary threshold
        return False, "Transaction flagged as suspicious."
    return True, "Transaction approved."

class SecurityManager:
    def __init__(self, secret_key=None):
        self.secret_key = secret_key or st.secrets.get("JWT_SECRET", "breakbread-secret-key-2024")
        ...
