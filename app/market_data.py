import yfinance as yf
import plotly.graph_objects as go
import streamlit as st

class MarketData:
    def get(self, symbol: str, period: str = "1y"):
        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        info = getattr(t, "info", {}) or {}
        cp = info.get("currentPrice", float(hist["Close"][-1]) if not hist.empty else 0.0)
        prev = info.get("previousClose", cp)
        return {
            "historical": hist,
            "current_price": cp,
            "change": cp - prev,
            "change_percent": ((cp - prev) / prev * 100.0) if prev else 0.0,
            "52w_high": info.get("fiftyTwoWeekHigh", 0.0),
            "52w_low": info.get("fiftyTwoWeekLow", 0.0),
        }

    def chart(self, hist, symbol: str, chart_type: str = "line"):
        if hist is None or hist.empty:
            return None
        if chart_type == "candlestick":
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index, open=hist["Open"], high=hist["High"],
                low=hist["Low"], close=hist["Close"], name=symbol)])
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name=f"{symbol} Close"))
        fig.update_layout(title=f"{symbol} Price", xaxis_title="Date", yaxis_title="USD", height=400)
        return fig

market_data = MarketData()

@st.cache_data(ttl=300)
def cached(symbol: str, period: str = "1y"):
    return market_data.get(symbol, period)
