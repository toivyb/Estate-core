import pickle
import numpy as np

with open("models/utility_model.pkl", "rb") as f:
    model = pickle.load(f)

def forecast_utility(inputs):
    X = np.array([[inputs["avg_temp"], inputs["occupants"], inputs["unit_size_sqft"]]])
    usage = model.predict(X)[0]
    return f"Estimated usage: {usage:.2f} kWh"
