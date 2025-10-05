# app/investing.py

def place_order(user_id, symbol, shares, price):
    """Simulate placing a stock order."""
    return {"status": "success", "message": f"Placed order for {shares} shares of {symbol} at ${price:.2f}"}

def portfolio_value(user_id):
    """Return a dummy portfolio value."""
    return 10000.00

def unrealized_gains(user_id):
    """Return placeholder unrealized gains."""
    return {"AAPL": 250.00, "MSFT": -100.00}

def allocation_breakdown(user_id):
    """Return a simple allocation breakdown."""
    return {"Stocks": 0.7, "Bonds": 0.2, "Cash": 0.1}
