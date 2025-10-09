def ensure_demo_users():
    """Populate demo users with consistent data structure"""
    if "users" not in st.session_state:
        st.session_state.users = {}
    
    # Demo users with password_hash field for compatibility
    demo_users = {
        "user_1": {
            "user_id": "user_1", 
            "app_id": "janedoe", 
            "email": "jane@example.com",
            "password_hash": hash_password("demo123"),  # Consistent hashing
            "balance": 2500.00,
            "watchlist": ["AAPL", "BTC-USD"],
            "portfolio": {
                "AAPL": {"units": 3.0, "avg_cost": 175.50},
                "BTC-USD": {"units": 0.02, "avg_cost": 42000.00}
            },
            "settings": {
                "dark_mode": True,
                "price_alerts": {"BTC-USD": 70000},
                "notification_preferences": {"email": True, "push": True}
            },
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "verified": True
        },
        "user_2": {
            "user_id": "user_2", 
            "app_id": "johndoe", 
            "email": "john@example.com",
            "password_hash": hash_password("demo123"),  # Consistent hashing
            "balance": 1500.00,
            "watchlist": ["TSLA", "ETH-USD"],
            "portfolio": {
                "TSLA": {"units": 2.0, "avg_cost": 220.00}
            },
            "settings": {
                "dark_mode": False,
                "price_alerts": {},
                "notification_preferences": {"email": True, "push": False}
            },
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "verified": True
        }
    }
    
    # Only add demo users if they don't exist
    for user_id, user_data in demo_users.items():
        if user_id not in st.session_state.users:
            st.session_state.users[user_id] = user_data
