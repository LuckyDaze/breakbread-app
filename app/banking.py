from datetime import datetime

USERS = {}
TRANSACTIONS = []

def ensure_demo_users():
    global USERS
    if USERS:
        return
    USERS = {
        "u1": {"user_id":"u1","app_id":"johndoe","email":"john@x.com","balance":1500.00},
        "u2": {"user_id":"u2","app_id":"janedoe","email":"jane@x.com","balance":900.00},
    }

def _find_user(identifier):
    for u in USERS.values():
        if identifier in (u["app_id"], u.get("email"), u.get("phone")):
            return u
    return None

def send_money(sender_id, recipient_identifier, amount, note=""):
    sender = USERS.get(sender_id)
    recipient = _find_user(recipient_identifier)
    if not sender or not recipient:
        return False, "User not found."
    fee = round(amount * 0.015, 2)

def find_user(identifier):
    return _find_user(identifier)

def get_user(identifier):
    return _find_user(identifier)

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
    return True, f"Paycheck of ${amount:.2f} deposited."
    
    # 👇 this is the “new code” continuation
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
    return True, f"Sent ${amount:.2f} to {recipient['app_id']} (fee ${fee:.2f})."
