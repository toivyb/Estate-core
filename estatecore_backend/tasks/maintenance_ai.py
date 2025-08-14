def compute_ai_risk_score(description):
    # Placeholder for AI prediction
    # Could use keywords (e.g., "water leak" = high risk)
    if "leak" in description.lower():
        return 0.8
    if "urgent" in description.lower():
        return 0.9
    return 0.2
