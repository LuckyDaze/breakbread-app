import requests
import streamlit as st
from datetime import datetime

def get_crypto_prices(symbols=['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD']):
    """Get cryptocurrency prices from Yahoo Finance fallback."""
    try:
        # Try CoinGecko first (free tier)
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum,cardano,solana',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            mapping = {
                'bitcoin': 'BTC-USD',
                'ethereum': 'ETH-USD', 
                'cardano': 'ADA-USD',
                'solana': 'SOL-USD'
            }
            
            for coin_id, symbol in mapping.items():
                if coin_id in data:
                    results.append({
                        'symbol': symbol,
                        'price': data[coin_id]['usd'],
                        'change_percent': data[coin_id].get('usd_24h_change', 0),
                        'source': 'CoinGecko API',
                        'last_updated': datetime.now()
                    })
            
            return results
        else:
            # Fallback to Yahoo Finance
            return get_crypto_demo_data()
            
    except Exception as e:
        st.error(f"Error fetching crypto data: {str(e)}")
        return get_crypto_demo_data()

def get_crypto_demo_data():
    """Demo data for cryptocurrencies."""
    return [
        {'symbol': 'BTC-USD', 'price': 51234.56, 'change_percent': 2.34, 'source': 'Demo Data', 'last_updated': datetime.now()},
        {'symbol': 'ETH-USD', 'price': 2890.12, 'change_percent': 1.78, 'source': 'Demo Data', 'last_updated': datetime.now()},
        {'symbol': 'ADA-USD', 'price': 0.4567, 'change_percent': -0.23, 'source': 'Demo Data', 'last_updated': datetime.now()},
        {'symbol': 'SOL-USD', 'price': 123.45, 'change_percent': 5.67, 'source': 'Demo Data', 'last_updated': datetime.now()}
    ]
