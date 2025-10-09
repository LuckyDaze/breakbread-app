import uuid
import random
from datetime import datetime, timedelta

def uid():
    """Generate a unique ID."""
    return str(uuid.uuid4())[:8]

def format_money(amount):
    """Format money with dollar sign and 2 decimal places."""
    if amount >= 0:
        return f"${amount:,.2f}"
    else:
        return f"-${abs(amount):,.2f}"

def seed_price_path(base_value, days, volatility=0.02):
    """Generate simulated price path for charts."""
    prices = [base_value]
    for _ in range(days - 1):
        change = random.uniform(-volatility, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    return prices
