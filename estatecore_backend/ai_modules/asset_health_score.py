def compute_health_score(property_data):
    # Score based on financial + maintenance
    issues = property_data.get("open_issues", 0)
    profit = property_data.get("net_profit", 0)
    if issues > 5 or profit < 0:
        return "Low"
    return "High"
