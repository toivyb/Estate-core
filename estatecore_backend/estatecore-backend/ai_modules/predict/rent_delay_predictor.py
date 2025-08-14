import pickle
import numpy as np

with open("models/rent_delay_model.pkl", "rb") as f:
    model = pickle.load(f)

def predict_rent_delay(tenant):
    X = np.array([[tenant["late_payments"], tenant["average_days_late"], tenant["months_paid_on_time"]]])
    prediction = model.predict(X)
    return "Likely Late" if prediction[0] == 1 else "On Time"
