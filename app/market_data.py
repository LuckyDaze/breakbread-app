import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=300)
def cached(symbol: str, period: str):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        info = getattr(t, "info", {}) or {}
        current = info.get("currentPrice", float(hist["Close"][-1]) if not hist.empty else 0)
        prev = info.get("previousClose", current)
        return {
            "historical": hist,
            "current_price": float(current),
            "change": float(current - prev) if prev else 0.0,
            "change_percent": float((current - prev) / prev * 100) if prev else 0.0,
            "52w_high": float(info.get("fiftyTwoWeekHigh", 0) or 0),
            "52w_low": float(info.get("fiftyTwoWeekLow", 0) or 0),
        }
    except Exception as e:
        st.error(f"Market data error for {symbol}: {e}")
        return None

class market_data:
    @staticmethod
    def chart(historical, symbol, chart_type="line"):
        if historical is None or historical.empty:
            return None
        if chart_type == "candlestick":
            fig = go.Figure(data=[go.Candlestick(
                x=historical.index,
                open=historical["Open"],
                high=historical["High"],
                low=historical["Low"],
                close=historical["Close"],
                name=symbol,
            )])
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=historical.index, y=historical["Close"], mode="lines", name=f"{symbol}"))
        fig.update_layout(title=f"{symbol} Price", xaxis_title="Date", yaxis_title="Price ($)", height=400)
        return fig
