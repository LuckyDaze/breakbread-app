import uuid
import hashlib
from datetime import datetime, timedelta

# ----------------------------
# Database Simulation (Using dictionaries)
# ----------------------------
users_db = {}
transactions_db = []
investment_assets = {
    "gold": {"price_per_ounce": 1950.00, "fee_percent": 0.02},
    "silver": {"price_per_ounce": 24.50, "fee_percent": 0.02},
    "treasury_bonds": {"price_per_unit": 1000.00, "fee_percent": 0.01}
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
    """Hash a password for storing."""
    salt = "breakbread_salt_2023"  # In production, use a unique salt per user
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

def p2p_transaction(sender_id):
    """Algorithm for peer-to-peer money transfer."""
    print("=== Break Bread P2P Transaction ===")
    
    recipient_identifier = input("Enter recipient's phone, email, or App ID: ")
    
    recipient = None
    for user in users_db.values():
        if (user.phone == recipient_identifier or 
            user.email == recipient_identifier or 
            user.app_id == recipient_identifier):
            recipient = user
            break
    
    if not recipient:
        print("Recipient not found. Please check the identifier and try again.")
        return False
    
    try:
        amount = float(input("Enter amount to send: "))
        note = input("Add an optional note: ")
    except ValueError:
        print("Invalid amount. Please enter a valid number.")
        return False
    
    sender = users_db[sender_id]
    fee = round(amount * 0.015, 2)
    
    # ✅ Fix: include fee in balance check
    if sender.balance < amount + fee:
        print("Insufficient balance. Would you like to add funds from your linked account?")
        return False
    
    print(f"Transaction fee: ${fee}. Total amount: ${amount + fee}")
    
    auth_method = input("Authenticate with (1) PIN, (2) Biometrics, or (3) 2FA: ")
    
    transaction = Transaction(sender_id, recipient.user_id, amount, fee, note)
    
    if not security_check(transaction):
        transaction.status = "flagged"
        transactions_db.append(transaction)
        print("Transaction flagged for security review. Please wait for verification.")
        return False
    
    sender.balance -= (amount + fee)
    recipient.balance += amount
    transaction.status = "completed"
    
    global break_bread_fund
    break_bread_fund += fee
    
    transactions_db.append(transaction)
    
    print(f"Transaction completed! ${amount} sent to {recipient.app_id}.")
    print(f"New balance: ${sender.balance}")
    
    return True

def investment_portfolio(user_id):
    """Algorithm for investment features."""
    print("=== Break Bread Investment Portal ===")
    print("1. Gold Bullion\n2. Silver Bullion\n3. Treasury Bonds")
    
    try:
        choice = int(input("Select an option (1-3): "))
        asset_types = ["gold", "silver", "treasury_bonds"]
        if choice not in [1, 2, 3]:
            print("Invalid selection.")
            return False
        
        asset_type = asset_types[choice-1]
        asset = investment_assets[asset_type]
        
        if asset_type in ["gold", "silver"]:
            print(f"Current price: ${asset['price_per_ounce']} per ounce")
        else:
            print(f"Current price: ${asset['price_per_unit']} per unit")
        
        print(f"Fee: {asset['fee_percent'] * 100}%")
        
        investment_amount = float(input("Enter amount to invest: $"))
        
        units = investment_amount / (
            asset['price_per_ounce'] if asset_type in ["gold", "silver"] else asset['price_per_unit']
        )
        
        # ✅ Fix: round commission
        commission = round(investment_amount * asset['fee_percent'], 2)
        
        print(f"You will receive: {units:.4f} units")
        print(f"Commission: ${commission:.2f}")
        print(f"Total cost: ${investment_amount + commission:.2f}")
        
        user = users_db[user_id]
        if user.balance < investment_amount + commission:
            print("Insufficient balance.")
            return False
        
        password = input("Enter your password to confirm: ")
        if not verify_password(user.password_hash, password):
            print("Authentication failed.")
            return False
        
        user.balance -= (investment_amount + commission)
        
        if user_id not in user_portfolios:
            user_portfolios[user_id] = {}
        
        user_portfolios[user_id][asset_type] = user_portfolios[user_id].get(asset_type, 0.0) + units
        
        global break_bread_fund
        break_bread_fund += commission
        
        print("Investment successful!")
        print(f"New balance: ${user.balance}")
        print(f"Portfolio: {user_portfolios[user_id]}")
        return True
        
    except ValueError:
        print("Invalid input.")
        return False

# ----------------------------
# Demo Execution
# ----------------------------
def run_demo():
    print("🚀 Break Bread App Simulation")
    print("=" * 40)
    
    # Demo users
    test_user1 = User("test_user_1", phone="+1234567890", app_id="johndoe", password_hash=hash_password("password123"))
    test_user1.balance = 1000.00
    test_user1.verified = True
    users_db[test_user1.user_id] = test_user1
    
    test_user2 = User("test_user_2", email="jane@example.com", app_id="janedoe", password_hash=hash_password("password123"))
    test_user2.balance = 500.00
    test_user2.verified = True
    users_db[test_user2.user_id] = test_user2
    
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

# ⚠️ Note: For Streamlit deployment, do NOT auto-run.
# Uncomment below ONLY if running in terminal:
# if __name__ == "__main__":
#     run_demo()
    run_demo()
