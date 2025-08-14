import pickle
import numpy as np

with open("models/lease_model.pkl", "rb") as f:
    model = pickle.load(f)

def score_lease(tenant):
    X = np.array([[tenant["late_payments"], tenant["on_time_months"], tenant["complaints"]]])
    prediction = model.predict(X)
    return "High Risk" if prediction[0] == 1 else "Low Risk"
