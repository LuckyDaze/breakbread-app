"""Common functions to avoid circular imports."""
import streamlit as st

def get_user(user_id):
    """Get user by ID directly from session state."""
    return st.session_state.users.get(user_id)

def find_user(identifier):
    """Find user by app_id or email."""
    identifier = (identifier or "").strip().lower()
    for user in st.session_state.users.values():
        if user["app_id"].lower() == identifier or user["email"].lower() == identifier:
            return user
    return None
