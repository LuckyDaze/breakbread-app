# core.py
import uuid
import hashlib
from datetime import datetime, timedelta

# ----------------------------
# Database Simulation (Using dictionaries)
# ----------------------------
users_db = {}
transactions_db = []
investment_assets = {
    "gold": {"price_per_ounce": 1925.00, "fee_percent": 0.02},
    "silver": {"price_per_ounce": 23.75, "fee_percent": 0.02},
    "platinum": {"price_per_ounce": 890.00, "fee_percent": 0.025},
    "treasury_bonds": {"price_per_unit": 1000.00, "fee_percent": 0.01},
}
user_portfolios = {}
break_bread_fund = 0.0
security_logs = []

# ----------------------------
# Core Models
# ----------------------------
class User:
    def __init__(self, user_id, phone=None, email=None, app_id=None, password_hash=None):
        self.user_id = user_id
        self.phone = phone
        self.email = email
        self.app_id = app_id
        self.password_hash = password_hash
        self.balance = 0.0
        self.verified = False
        self.linked_bank_accounts = []
        self.linked_crypto_wallets = []
        self.transaction_limit = 1000.00  # Initial limit
        self.created_at = datetime.now()
        
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "phone": self.phone,
            "email": self.email,
            "app_id": self.app_id,
            "balance": self.balance,
            "verified": self.verified,
            "transaction_limit": self.transaction_limit
        }

class Transaction:
    def __init__(self, sender_id, recipient_id, amount, fee, note=""):
        self.transaction_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount
        self.fee = fee
        self.note = note
        self.status = "pending"
        self.timestamp = datetime.now()
        self.security_check_passed = False
        
    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "amount": self.amount,
            "fee": self.fee,
            "note": self.note,
            "status": self.status,
            "timestamp": self.timestamp.isoformat()
        }

class Investment:
    def __init__(self, user_id, asset_type, amount, units, fee):
        self.investment_id = str(uuid.uuid4())
        self.user_id = user_id
        self.asset_type =_
