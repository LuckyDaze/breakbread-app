def format_currency(amount):
    return f"${amount:,.2f}"

def safe_get(d, key, default=None):
    return d[key] if key in d else default
