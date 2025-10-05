from app.banking import TRANSACTIONS

def track_event(event_name, metadata=None):
    """Return a simple event record (could be extended to log)."""
    return {"event": event_name, "metadata": metadata or {}}

def user_activity_summary(user_id):
    """Summarize a user's transactions."""
    txs = [t for t in TRANSACTIONS if t["sender_id"] == user_id or t["recipient_id"] == user_id]
    total_sent = sum(t["amount"] for t in txs if t["sender_id"] == user_id)
    total_received = sum(t["amount"] for t in txs if t["recipient_id"] == user_id)
    return {
        "transactions": len(txs),
        "total_sent": total_sent,
        "total_received": total_received
    }
