def score_lease(tenant):
    # Basic scoring example
    if tenant.get("late_payments", 0) > 2:
        return "High Risk"
    return "Low Risk"
