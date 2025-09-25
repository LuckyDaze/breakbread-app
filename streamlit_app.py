import uuid
import hashlib
from datetime import datetime, timedelta

# ----------------------------
# Database Simulation (Using dictionaries)
# ----------------------------
users_db = {}
transactions_db = []

# Prices updated Sep 24, 2025 (see sources in PR)
investment_assets = {
    "gold":           {"price_per_ounce": 3734.04,  "fee_percent": 0.02},  # Reuters
    "silver":         {"price_per_ounce": 44.13,    "fee_percent": 0.02},  # APMEX
    "platinum":       {"price_per_ounce": 1489.00,  "fee_percent": 0.02},  # APMEX
    "treasury_bonds": {"price_per_unit":  101.753345, "fee_percent": 0.01} # TreasuryDirect (per $100 face)
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
        self.transaction_limit = 1000.00  # Initial limit (USD)
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
        self.status = "pending"  # pending, completed, failed, flagged
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
        self.asset_type = asset_type
        self.amount = amount
        self.units = units
        self.fee = fee
        self.timestamp = datetime.now()
        
    def to_dict(self):
        return {
            "investment_id": self.investment_id,
            "user_id": self.user_id,
            "asset_type": self.asset_type,
            "amount": self.amount,
            "units": self.units,
            "fee": self.fee,
            "timestamp": self.timestamp.isoformat()
        }

# ----------------------------
# Utility Functions
# ----------------------------
def hash_password(password):
    """Hash a password for storing. (MVP demo only: static salt)"""
    salt = "breakbread_salt_2023"  # In production, use a UNIQUE per-user salt + Argon2/Bcrypt
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """Verify a stored password against one provided by user."""
    salt = "breakbread_salt_2023"
    return stored_hash == hashlib.sha256(salt.encode() + password.encode()).hexdigest()

def send_otp(contact_info):
    """Simulate sending OTP to phone or email."""
    otp = "123456"  # In production, generate a random 6-digit code
    print(f"OTP sent to {contact_info}: {otp}")
    return otp

def verify_otp(input_otp, sent_otp):
    """Verify OTP code."""
    return input_otp == sent_otp

def encrypt_data(data):
    """Simulate data encryption (in production, use proper encryption)."""
    return hashlib.sha256(data.encode()).hexdigest()

# ----------------------------
# Core Algorithms Implementation
# ----------------------------
def link_funding_source(user_id):
    """Prompt user to link a bank account or crypto wallet."""
    print("To start using Break Bread, please link a funding source.")
    choice = input("Link (1) Bank Account or (2) Crypto Wallet? ")
    if choice == "1":
        bank_account = input("Enter your bank account number: ")
        users_db[user_id].linked_bank_accounts.append(bank_account)
        print("Bank account linked successfully.")
    elif choice == "2":
        wallet_address = input("Enter your crypto wallet address: ")
        users_db[user_id].linked_crypto_wallets.append(wallet_address)
        print("Crypto wallet linked successfully.")
    else:
        print("Invalid selection. Please choose 1 (Bank) or 2 (Crypto).")

def security_check(transaction):
    """Perform security and fraud detection checks."""
    sender = users_db[transaction.sender_id]

    # Check 1: Transaction amount within limits
    if transaction.amount > sender.transaction_limit:
        security_logs.append({
            "timestamp": datetime.now(),
            "event": "transaction_over_limit",
            "transaction_id": transaction.transaction_id,
            "details": f"Amount: {transaction.amount}, Limit: {sender.transaction_limit}"
        })
        return False
    
    # Check 2: Unusual transaction pattern (simplified)
    recent_transactions = [
        t for t in transactions_db 
        if t.sender_id == transaction.sender_id and 
           t.timestamp > datetime.now() - timedelta(hours=24)
    ]
    if len(recent_transactions) > 10:
        security_logs.append({
            "timestamp": datetime.now(),
            "event": "unusual_activity",
            "transaction_id": transaction.transaction_id,
            "details": f"High frequency: {len(recent_transactions)} transactions in 24h"
        })
        return False
    
    # Check 3: Large amount to new recipient
    previous_to_recipient = any(
        t.recipient_id == transaction.recipient_id 
        for t in transactions_db 
        if t.sender_id == transaction.sender_id
    )
    if transaction.amount > 500 and not previous_to_recipient:
        security_logs.append({
            "timestamp": datetime.now(),
            "event": "large_amount_new_recipient",
            "transaction_id": transaction.transaction_id,
            "details": f"Amount: {transaction.amount}, New recipient: {transaction.recipient_id}"
        })
        additional_auth = input("Large transfer to new recipient. Confirm with 2FA code: ")
        if additional_auth != "123456":  # Simulated 2FA verification
            return False
    
    return True

def p2p_transaction(sender_id):
    """Algorithm for peer-to-peer money transfer."""
    print("=== Break Bread P2P Transaction ===")
    recipient_identifier = input("Enter recipient's phone, email, or App ID: ")

    # Lookup recipient
    recipient = next((
        u for u in users_db.values()
        if u.phone == recipient_identifier or 
           u.email == recipient_identifier or 
           u.app_id == recipient_identifier
    ), None)

    if not recipient:
        print("Recipient not found. Please check the identifier and try again.")
        return False

    # Amount & note
    try:
        amount = float(input("Enter amount to send: "))
        if amount <= 0:
            print("Amount must be greater than 0.")
            return False
        note = input("Add an optional note: ")
    except ValueError:
        print("Invalid amount. Please enter a valid number.")
        return False

    # Fee and balance check (include fee)
    sender = users_db[sender_id]
    fee = round(amount * 0.015, 2)
    if sender.balance < amount + fee:
        print("Insufficient balance. Would you like to add funds from your linked account?")
        return False

    print(f"Transaction fee: ${fee:.2f}. Total debit: ${amount + fee:.2f}")
    input("Authenticate (press Enter to simulate)... ")

    # Build and run security checks
    t = Transaction(sender_id, recipient.user_id, amount, fee, note)
    if not security_check(t):
        t.status = "flagged"
        transactions_db.append(t)
        print("Transaction flagged for security review.")
        return False

    # Execute
    sender.balance -= (amount + fee)
    recipient.balance += amount
    t.status = "completed"

    global break_bread_fund
    break_bread_fund += fee
    transactions_db.append(t)

    print(f"Transaction completed! ${amount:.2f} sent to {recipient.app_id}.")
    print(f"New balance: ${sender.balance:.2f}")
    return True

def investment_portfolio(user_id):
    """Algorithm for investment features."""
    print("=== Break Bread Investment Portal ===")
    print("1. Gold Bullion\n2. Silver Bullion\n3. Platinum Bullion\n4. Treasury Bonds")
    try:
        choice = int(input("Select an option (1-4): "))
        asset_types = ["gold", "silver", "platinum", "treasury_bonds"]
        if choice not in [1, 2, 3, 4]:
            print("Invalid selection.")
            return False

        asset_type = asset_types[choice-1]
        asset = investment_assets[asset_type]

        # Price & fee display
        if asset_type in ["gold", "silver", "platinum"]:
            price_key = "price_per_ounce"
        else:
            price_key = "price_per_unit"  # per $100 face for treasuries

        print(f"Current price: ${asset[price_key]:,.6f}")
        print(f"Fee: {asset['fee_percent'] * 100:.2f}%")

        # Amount input
        investment_amount = float(input("Enter amount to invest (USD): $"))
        if investment_amount <= 0:
            print("Amount must be greater than 0.")
            return False

        # Units calculation
        units = investment_amount / asset[price_key]

        # Commission calculation
        commission = round(investment_amount * asset['fee_percent'], 2)

        print(f"You will receive: {units:.6f} units")
        print(f"Commission: ${commission:.2f}")
        print(f"Total debit: ${investment_amount + commission:.2f}")

        # Check balance and password auth
        user = users_db[user_id]
        if user.balance < investment_amount + commission:
            print("Insufficient balance.")
            return False

        password = input("Enter your password to confirm: ")
        if not verify_password(user.password_hash, password):
            print("Authentication failed.")
            return False

        # Execute
        user.balance -= (investment_amount + commission)
        if user_id not in user_portfolios:
            user_portfolios[user_id] = {}
        user_portfolios[user_id][asset_type] = user_portfolios[user_id].get(asset_type, 0.0) + units

        global break_bread_fund
        break_bread_fund += commission

        print("Investment successful!")
        print(f"New balance: ${user.balance:.2f}")
        print(f"Portfolio: {user_portfolios[user_id]}")
        return True

    except ValueError:
        print("Invalid input.")
        return False

def run_demo():
    print("🚀 Break Bread App Simulation")
    print("=" * 40)
    # Demo users
    u1 = User("test_user_1", phone="+1234567890", app_id="johndoe", password_hash=hash_password("password123"))
    u1.balance = 20000.00  # bumped so you can try larger investments at current prices
    u1.verified = True
    users_db[u1.user_id] = u1

    u2 = User("test_user_2", email="jane@example.com", app_id="janedoe", password_hash=hash_password("password123"))
    u2.balance = 15000.00
    u2.verified = True
    users_db[u2.user_id] = u2

    while True:
        print("\nBreak Bread Main Menu:")
        print("1. P2P Transaction\n2. Investment Portfolio\n3. Exit")
        choice = input("Select an option: ")
        if choice == "1":
            uid = input("Enter your user ID: ")
            if uid in users_db:
                p2p_transaction(uid)
            else:
                print("User not found.")
        elif choice == "2":
            uid = input("Enter your user ID: ")
            if uid in users_db:
                investment_portfolio(uid)
            else:
                print("User not found.")
        elif choice == "3":
            print("Thank you for using Break Bread!")
            break
        else:
            print("Invalid option. Please try again.")

# NOTE (for Streamlit): Do NOT auto-run in web apps. Keep this commented out.
# if __name__ == "__main__":
#     run_demo()

