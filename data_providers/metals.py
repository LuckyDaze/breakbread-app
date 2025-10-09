import streamlit as st
from datetime import datetime

def get_metals_prices():
    """Get precious metals prices."""
    try:
        # Metals-API (requires key) or fallback to demo
        api_key = st.secrets.get("METALS_API_KEY", "")
        
        if api_key:
            import requests
            url = f"https://metals-api.com/api/latest"
            params = {
                'access_key': api_key,
                'base': 'USD',
                'symbols': 'XAU,XAG,XPT'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'rates' in data:
                return {
                    'gold': 1 / data['rates']['XAU'],  # Convert from USD per ounce
                    'silver': 1 / data['rates']['XAG'],
                    'platinum': 1 / data['rates']['XPT'],
                    'source': 'Metals-API',
                    'last_updated': datetime.now()
                }
        
        # Fallback to demo data
        return get_metals_demo_data()
        
    except Exception as e:
        st.error(f"Error fetching metals data: {str(e)}")
        return get_metals_demo_data()

def get_metals_demo_data():
    """Demo data for precious metals."""
    return {
        'gold': 1987.65,
        'silver': 23.45,
        'platinum': 987.32,
        'source': 'Demo Data (Live: Metals-API)',
        'last_updated': datetime.now()
    }
