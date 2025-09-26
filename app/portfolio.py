# app/portfolio.py
from __future__ import annotations

def diversification_score(alloc: dict[str, float]) -> int:
    """Very simple score vs an 'ideal' policy."""
    ideal = {
        "stocks": 40,
        "bonds": 20,
        "crypto": 10,
        "precious_metals": 10,
        "startups": 10,
        "royalties": 5,
        "real_estate": 5
    }
    score = 100
    for k, ideal_pct in ideal.items():
        actual = alloc.get(k, 0.0)
        score -= abs(ideal_pct - actual) * 0.5
    return max(0, min(100, round(score)))
