def suggest_renewal(tenant, market_rate):
    # Suggest based on payment history and loyalty
    if tenant.get("months_on_time", 0) > 10:
        return market_rate  # keep same
    return market_rate * 1.05  # slight increase
