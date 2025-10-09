"""Common functions used across multiple modules to avoid circular imports."""

def get_user(user_id):
    """Get user by ID from session state."""
    from streamlit import session_state as st_session
    return st_session.users.get(user_id)

def find_user(identifier):
    """Find user by app_id or email."""
    from streamlit import session_state as st_session
    for user in st_session.users.values():
        if user["app_id"] == identifier or user["email"] == identifier:
            return user
    return None
