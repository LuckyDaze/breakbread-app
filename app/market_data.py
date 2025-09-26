# app/market_data.py
from __future__ import annotations
import yfinance as yf
import plotly.graph_objects as go
import streamlit as st

class MarketData:
    def get_stock_data(self, symbol: str, period: str = "1y"):
        """Fast Yahoo Finance pull + safe info access."""
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        info = getattr(ticker, "info", {}) or {}

        current = info.get("currentPrice", float(hist["Close"][-1]) if not hist.empty else 0.0)
        prev = info.get("previousClose", current)
        change = current - prev
        change_pct = (change / prev * 100.0) if prev else 0.0

        return {
            "historical": hist,
            "current_price": float(current or 0.0),
            "change": float(change or 0.0),
            "change_percent": float(change_pct or 0.0),
            "company_name": info.get("longName", symbol),
            "market_cap": info.get("marketCap", 0),
            "volume": info.get("volume", 0),
            "52w_high": info.get("fiftyTwoWeekHigh", 0),
            "52w_low": info.get("fiftyTwoWeekLow", 0),
        }

    def chart(self, historical, symbol: str, chart_type: str = "line"):
        if historical is None or historical.empty:
            return None

        if chart_type == "candlestick":
            fig = go.Figure(data=[go.Candlestick(
                x=historical.index,
                open=historical["Open"],
                high=historical["High"],
                low=historical["Low"],
                close=historical["Close"],
                name=symbol
            )])
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=historical.index,
                y=historical["Close"],
                mode="lines",
                name=f"{symbol} Close"
            ))

        fig.update_layout(
            title=f"{symbol} Price",
            xaxis_title="Date",
            yaxis_title="USD",
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        return fig

market_data = MarketData()

@st.cache_data(ttl=300)
def cached(symbol: str, period: str = "1y"):
    return market_data.get_stock_data(symbol, period)
