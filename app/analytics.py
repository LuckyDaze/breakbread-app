def track_event(event_name, metadata=None):
    return {"event": event_name, "metadata": metadata or {}}

def user_activity_summary(user_id):
    return {"user_id": user_id, "logins": 5, "transactions": 12}
