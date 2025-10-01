import streamlit as st

try:
    import plotly.graph_objects as go
except Exception:
    go = None  # Plotly not available yet

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
