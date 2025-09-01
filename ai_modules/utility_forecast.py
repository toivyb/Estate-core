def forecast_utility(current_month, weather):
    # Use historical + weather input
    if weather.lower() in ("cold", "very cold"):
        return "Expect Higher Heating Bill"
    return "Normal Usage Expected"
