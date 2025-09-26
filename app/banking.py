# app/banking.py
from __future__ import annotations
from datetime import datetime
import uuid

# Simple in-memory stores (swap for DB later)
USERS = {}
TRANSACTIONS = []

def ensure_demo_users():
    """Seed two demo users if empty."""
    if USERS:
        return
    USERS["test_user_1"] = {"user_id":"test_user_1","app_id":"johndoe","email":"john@example.com","balance":10000.0}
    USERS["test_user_2"] = {"user_id":"test_user_2","app_id":"janedoe","email":"jane@example.com","balance":7500.0}

def find_user(identifier: str):
    for u in USERS.values():
        if identifier in (u["user_id"], u.get("app_id"), u.get("email")):
            return u
    return None

def send_money(sender_id: str, recipient_identifier: str, amount: float, note: str = ""):
    sender = USERS.get(sender_id)
    recipient = find_user(recipient_identifier)
    if not sender or not recipient:
        return False, "User not found"

    fee = round(amount * 0.015, 2)
    total = amount + fee
    if sender["balance"] < total:
        return False, "Insufficient funds"

    sender["balance"] -= total
    recipient["balance"] += amount

    TRANSACTIONS.append({
        "id": str(uuid.uuid4()),
        "ts": datetime.utcnow(),
        "sender_id": sender["user_id"],
        "recipient_id": recipient["user_id"],
        "amount": amount,
        "fee": fee,
        "note": note,
        "status": "completed"
    })
    return True, f"Sent ${amount:.2f} to {recipient['app_id']} (fee ${fee:.2f})"
