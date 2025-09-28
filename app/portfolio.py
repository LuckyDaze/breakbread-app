def diversification_score(allocation: dict[str, float]) -> int:
    target = {"stocks":40,"bonds":20,"crypto":10,"startups":10,"royalties":5,"precious_metals":10}
    score = 100
    for k, tgt in target.items():
        actual = allocation.get(k, 0)
        score -= abs(tgt - actual) * 0.5
    return max(0, min(100, int(round(score))))
