import pickle
import numpy as np

with open("models/maintenance_model.pkl", "rb") as f:
    model = pickle.load(f)

def forecast_maintenance(equipment):
    X = np.array([[equipment["age_months"], equipment["last_service_months_ago"], equipment["incident_reports"]]])
    prediction = model.predict(X)
    return "High Risk" if prediction[0] == 1 else "Low Risk"
