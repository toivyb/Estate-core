import pickle
import numpy as np

with open("models/revenue_model.pkl", "rb") as f:
    model = pickle.load(f)

def detect_leakage(info):
    X = np.array([[info["units"], info["expected_rent"], info["actual_collected"]]])
    score = model.predict(X)[0]
    return "Leakage Detected" if score > 0.1 else "No Leakage"
