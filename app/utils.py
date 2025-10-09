import uuid
import random
import pandas as pd

def uid():
    """Generate a short unique ID"""
    return str(uuid.uuid4())[:8]

def format_money(amount):
    """Format currency as $X,XXX.XX"""
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"

def seed_price_path(base, days=30):
    """Generate fake daily portfolio values"""
    values = [base]
    for _ in range(days - 1):
        change = random.uniform(-0.02, 0.02)
        values.append(values[-1] * (1 + change))
    return pd.Series(values)
