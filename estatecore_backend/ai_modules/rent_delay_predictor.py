def predict_delay(tenant):
    # Naive model
    score = tenant.get("late_payments", 0) * 5
    if score > 15:
        return "Likely Late"
    return "Likely On Time"
