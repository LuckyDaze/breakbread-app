import yfinance as yf
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# -------------------------------
# Yahoo Finance (via yfinance) - Stocks & Indices
# -------------------------------
def get_stock_data(symbol, period="1mo"):
    """Fetch stock/ETF data with historical prices."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
            
        info = ticker.info
        current_price = hist['Close'].iloc[-1]
        
        # Calculate change from previous close
        if len(hist) > 1:
            prev_price = hist['Close'].iloc[-2]
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100
        else:
            change = 0
            change_percent = 0
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent,
            'historical': hist,
            '52w_high': info.get('fiftyTwoWeekHigh', current_price * 1.2),
            '52w_low': info.get('fiftyTwoWeekLow', current_price * 0.8),
            'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0,
            'source': 'Yahoo Finance',
            'last_updated': datetime.now()
        }
    except Exception as e:
        st.error(f"Error fetching {symbol}: {str(e)}")
        return None

def get_sp500():
    """Fetch latest S&P 500 data with history."""
    return get_stock_data("^GSPC", "1d")

def get_nasdaq():
    """Fetch latest NASDAQ data with history."""
    return get_stock_data("^IXIC", "1d")

def get_dow_jones():
    """Fetch latest Dow Jones data with history."""
    return get_stock_data("^DJI", "1d")

def get_major_indices():
    """Get all major indices in one call."""
    indices = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ', 
        '^DJI': 'Dow Jones',
        '^RUT': 'Russell 2000'
    }
    
    results = []
    for symbol, name in indices.items():
        data = get_stock_data(symbol, '1d')
        if data:
            results.append({
                'name': name,
                'symbol': symbol,
                'price': data['current_price'],
                'change': data['change'],
                'change_percent': data['change_percent'],
                'source': data['source']
            })
    
    return results

# -------------------------------
# TreasuryDirect (Fiscal Data API)
# -------------------------------
def get_treasury_yields():
    """Fetch latest Treasury yields with historical context."""
    try:
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"
        params = {
            'filter': 'security_desc:eq:Treasury Notes',
            'sort': '-record_date',
            'page[size]': '30'  # Get last 30 days for historical view
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'data' in data and data['data']:
            latest = data['data'][0]
            historical_data = data['data'][:30]  # Last 30 records
            
            return {
                '1_month': float(latest.get('avg_interest_rate_amt', 0)),
                '2_year': float(latest.get('avg_interest_rate_amt', 0)) + 0.5,  # Demo spread
                '10_year': float(latest.get('avg_interest_rate_amt', 0)) + 1.2,  # Demo spread
                'historical': historical_data,
                'source': 'U.S. Treasury FiscalData API',
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
        else:
            return get_treasury_demo_data()
            
    except Exception as e:
        st.error(f"Treasury data unavailable: {e}")
        return get_treasury_demo_data()

def get_treasury_demo_data():
    """Fallback demo data for Treasury yields."""
    # Generate some realistic demo historical data
    historical = []
    base_rate = 4.5
    for i in range(30):
        date = datetime.now() - timedelta(days=29-i)
        rate = base_rate + random.uniform(-0.1, 0.1)
        historical.append({
            'record_date': date.strftime('%Y-%m-%d'),
            'avg_interest_rate_amt': f"{rate:.2f}"
        })
    
    return {
        '1_month': 5.32,
        '2_year': 4.89,
        '10_year': 4.45,
        'historical': historical,
        'source': 'U.S. Treasury (Demo Data)',
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    }

# -------------------------------
# CoinGecko (Crypto) with Historical Data
# -------------------------------
def get_crypto_data(coin_id="bitcoin", days=30):
    """Fetch cryptocurrency data with historical prices."""
    try:
        # Current price and market data
        price_url = "https://api.coingecko.com/api/v3/simple/price"
        price_params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        
        # Historical data
        history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        history_params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily"
        }
        
        price_response = requests.get(price_url, params=price_params, timeout=10)
        history_response = requests.get(history_url, params=history_params, timeout=10)
        
        if price_response.status_code == 200 and history_response.status_code == 200:
            price_data = price_response.json()[coin_id]
            history_data = history_response.json()
            
            # Convert to DataFrame for consistency
            prices = history_data['prices']
            timestamps = [pd.to_datetime(price[0], unit='ms') for price in prices]
            values = [price[1] for price in prices]
            
            historical_df = pd.DataFrame({
                'Date': timestamps,
                'Close': values
            }).set_index('Date')
            
            return {
                'symbol': coin_id.upper(),
                'current_price': price_data['usd'],
                'change_percent': price_data.get('usd_24h_change', 0),
                'market_cap': price_data.get('usd_market_cap', 0),
                'historical': historical_df,
                'source': 'CoinGecko API',
                'last_updated': datetime.now()
            }
        else:
            return get_crypto_demo_data(coin_id, days)
            
    except Exception as e:
        st.error(f"Crypto data unavailable for {coin_id}: {e}")
        return get_crypto_demo_data(coin_id, days)

def get_bitcoin_data(days=30):
    """Get Bitcoin data with history."""
    return get_crypto_data("bitcoin", days)

def get_ethereum_data(days=30):
    """Get Ethereum data with history."""
    return get_crypto_data("ethereum", days)

def get_crypto_prices(symbols=['bitcoin', 'ethereum', 'cardano', 'solana']):
    """Get multiple cryptocurrency prices quickly."""
    results = []
    for coin_id in symbols:
        data = get_crypto_data(coin_id, 1)  # Just current prices
        if data:
            symbol_map = {
                'bitcoin': 'BTC-USD',
                'ethereum': 'ETH-USD',
                'cardano': 'ADA-USD', 
                'solana': 'SOL-USD'
            }
            data['symbol'] = symbol_map.get(coin_id, coin_id.upper())
            results.append(data)
    
    return results

def get_crypto_demo_data(coin_id="bitcoin", days=30):
    """Fallback demo data for cryptocurrencies."""
    # Generate realistic demo data
    base_prices = {
        'bitcoin': 51234.56,
        'ethereum': 2890.12,
        'cardano': 0.4567,
        'solana': 123.45
    }
    
    base_price = base_prices.get(coin_id, 1000)
    
    # Generate historical data
    dates = pd.date_range(end=datetime.now(), periods=days)
    prices = []
    current_price = base_price
    
    for _ in range(days):
        change = random.uniform(-0.05, 0.05)  # ±5% daily change
        current_price = current_price * (1 + change)
        prices.append(current_price)
    
    historical_df = pd.DataFrame({
        'Date': dates,
        'Close': prices
    }).set_index('Date')
    
    symbol_map = {
        'bitcoin': 'BTC-USD',
        'ethereum': 'ETH-USD',
        'cardano': 'ADA-USD',
        'solana': 'SOL-USD'
    }
    
    return {
        'symbol': symbol_map.get(coin_id, coin_id.upper()),
        'current_price': prices[-1],
        'change_percent': ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) > 1 else 0,
        'market_cap': base_price * 1_000_000,  # Rough estimate
        'historical': historical_df,
        'source': 'CoinGecko (Demo Data)',
        'last_updated': datetime.now()
    }

# -------------------------------
# Metals API (Precious Metals) with Historical
# -------------------------------
def get_metals_data(metal="gold", days=30):
    """Fetch precious metals data with historical prices."""
    try:
        api_key = st.secrets.get("METALS_API_KEY", "")
        
        if api_key:
            # For historical data, you'd need a paid Metals-API plan
            # This is a simplified version
            url = f"https://metals-api.com/api/latest"
            params = {
                'access_key': api_key,
                'base': 'USD',
                'symbols': 'XAU,XAG,XPT'  # Gold, Silver, Platinum
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'rates' in data:
                metal_symbols = {
                    'gold': 'XAU',
                    'silver': 'XAG', 
                    'platinum': 'XPT'
                }
                
                symbol = metal_symbols.get(metal, 'XAU')
                price_per_ounce = 1 / data['rates'][symbol]  # Convert from USD per ounce
                
                # Generate demo historical data (real historical requires paid plan)
                historical_df = generate_metals_historical(price_per_ounce, days)
                
                return {
                    'metal': metal,
                    'price_per_ounce': price_per_ounce,
                    'historical': historical_df,
                    'source': 'Metals-API',
                    'last_updated': datetime.now()
                }
        
        # Fallback to demo data
        return get_metals_demo_data(metal, days)
        
    except Exception as e:
        st.error(f"Metals data unavailable: {e}")
        return get_metals_demo_data(metal, days)

def get_gold_data(days=30):
    """Get gold data with history."""
    return get_metals_data("gold", days)

def get_silver_data(days=30):
    """Get silver data with history."""
    return get_metals_data("silver", days)

def get_metals_prices():
    """Get all major metals prices."""
    metals = ['gold', 'silver', 'platinum']
    results = {}
    
    for metal in metals:
        data = get_metals_data(metal, 1)
        if data:
            results[metal] = data
    
    return results

def generate_metals_historical(current_price, days):
    """Generate realistic historical data for metals."""
    dates = pd.date_range(end=datetime.now(), periods=days)
    prices = []
    price = current_price
    
    for _ in range(days):
        change = random.uniform(-0.02, 0.02)  # ±2% daily change for metals
        price = price * (1 + change)
        prices.append(price)
    
    return pd.DataFrame({
        'Date': dates,
        'Close': prices
    }).set_index('Date')

def get_metals_demo_data(metal="gold", days=30):
    """Fallback demo data for precious metals."""
    base_prices = {
        'gold': 1987.65,
        'silver': 23.45,
        'platinum': 987.32
    }
    
    base_price = base_prices.get(metal, 1000)
    historical_df = generate_metals_historical(base_price, days)
    
    return {
        'metal': metal,
        'price_per_ounce': historical_df['Close'].iloc[-1],
        'historical': historical_df,
        'source': 'Metals-API (Demo Data)',
        'last_updated': datetime.now()
    }

# -------------------------------
# Charting Utilities
# -------------------------------
def create_price_chart(historical_data, title, chart_type="line"):
    """Create a Plotly chart from historical data."""
    fig = go.Figure()
    
    if chart_type == "candlestick" and all(col in historical_data.columns for col in ['Open', 'High', 'Low', 'Close']):
        fig.add_trace(go.Candlestick(
            x=historical_data.index,
            open=historical_data['Open'],
            high=historical_data['High'],
            low=historical_data['Low'],
            close=historical_data['Close'],
            name=title
        ))
    else:
        # Line chart for simple close prices
        fig.add_trace(go.Scatter(
            x=historical_data.index,
            y=historical_data['Close'],
            mode='lines',
            name=title,
            line=dict(color='#1f77b4')
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400,
        template="plotly_white",
        showlegend=False
    )
    
    return fig

def create_performance_chart(historical_data, title):
    """Create a percentage performance chart."""
    if historical_data.empty or len(historical_data) < 2:
        return None
        
    # Calculate percentage change from first value
    first_price = historical_data['Close'].iloc[0]
    performance = ((historical_data['Close'] - first_price) / first_price) * 100
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=performance.index,
        y=performance.values,
        mode='lines',
        name=title,
        line=dict(color='green' if performance.iloc[-1] >= 0 else 'red')
    ))
    
    fig.update_layout(
        title=f"{title} Performance (%)",
        xaxis_title="Date",
        yaxis_title="Percentage Change (%)",
        height=400,
        template="plotly_white",
        showlegend=False
    )
    
    return fig

# -------------------------------
# Quick Data Summary for Dashboard
# -------------------------------
def get_market_overview():
    """Get a quick overview of all major markets."""
    overview = {
        'indices': get_major_indices(),
        'crypto': get_crypto_prices(),
        'treasuries': get_treasury_yields(),
        'metals': get_metals_prices()
    }
    return overview

# For random number generation in demo data
import randomimport streamlit as st
try:
    import plotly.graph_objects as go
except Exception:
    go = None
import yfinance as yf
import pandas as pd

class MarketData:
    def chart(self, historical_data, symbol, chart_type="line"):
        if go is None:
            st.warning("Plotly is not installed. Install it by adding `plotly>=5.18.0` to requirements.txt.")
            return None
        if historical_data is None or historical_data.empty:
            return None

        if chart_type == "candlestick":
            fig = go.Figure(data=[go.Candlestick(
                x=historical_data.index,
                open=historical_data['Open'],
                high=historical_data['High'],
                low=historical_data['Low'],
                close=historical_data['Close'],
                name=symbol
            )])
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=historical_data.index,
                y=historical_data['Close'],
                mode='lines',
                name=f'{symbol} Price'
            ))
        fig.update_layout(title=f'{symbol} Stock Price', xaxis_title='Date', yaxis_title='Price ($)', height=400)
        return fig

market_data = MarketData()

@st.cache_data(ttl=300)
def cached(symbol, period):
    t = yf.Ticker(symbol)
    hist = t.history(period=period)
    if hist.empty:
        return None
    current = hist["Close"].iloc[-1]
    return {
        "historical": hist,
        "current_price": float(current),
        "change": float(current - hist["Close"].iloc[-2]) if len(hist) > 1 else 0.0,
        "change_percent": float(((current - hist["Close"].iloc[-2]) / hist["Close"].iloc[-2]) * 100) if len(hist) > 1 else 0.0,
        "52w_high": float(hist["High"].max()),
        "52w_low": float(hist["Low"].min()),
    }
# 👇 add these at the bottom of app/market_data.py

def get_cached_data(symbol, period="1mo"):
    """Wrapper around the cached() function so streamlit_app.py can import it."""
    return cached(symbol, period)

def chart(historical_data, symbol, chart_type="line"):
    """Convenience wrapper so you can call chart() directly."""
    return market_data.chart(historical_data, symbol, chart_type)

def mini_indices():
    """Return a small set of example indices with current prices."""
    indices = {}
    for symbol in ["^DJI", "^IXIC", "^GSPC"]:  # Dow, Nasdaq, S&P 500
        data = get_cached_data(symbol, "5d")
        if data:
            indices[symbol] = {
                "price": data["current_price"],
                "change": data["change"],
                "change_percent": data["change_percent"],
            }
    return indices
