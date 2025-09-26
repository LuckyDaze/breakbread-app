# app/market_data.py
import yfinance as yf

class MarketData:
    def get_stock_data(self, symbol: str, period: str = "1y"):
        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        info = getattr(t, "info", {}) or {}
        price = info.get("currentPrice", float(hist["Close"][-1]) if not hist.empty else 0.0)
        prev = info.get("previousClose", price)
        change = price - prev
        pct = (change / prev * 100) if prev else 0.0
        return {
            "historical_data": hist,
            "current_price": price,
            "change": change,
            "change_percent": pct,
            "company_name": info.get("longName", symbol),
            "market_cap": info.get("marketCap", 0),
            "volume": info.get("volume", 0),
            "52_week_high": info.get("fiftyTwoWeekHigh", 0),
            "52_week_low": info.get("fiftyTwoWeekLow", 0),
        }

market_data = MarketData()
