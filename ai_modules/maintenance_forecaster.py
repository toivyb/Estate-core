def forecast_maintenance(equipment):
    # Predict based on usage or age
    if equipment.get("age_months", 0) > 24:
        return "High Risk"
    return "Low Risk"
