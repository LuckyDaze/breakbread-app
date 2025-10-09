import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

def get_stock_data(symbol, period="1mo"):
    """Get stock data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
            
        info = ticker.info
        current_price = hist['Close'].iloc[-1]
        
        # Calculate change
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
        st.error(f"Error fetching Yahoo data for {symbol}: {str(e)}")
        return None

def get_major_indices():
    """Get major market indices."""
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
                'change_percent': data['change_percent'],
                'source': data['source']
            })
    
    return results
