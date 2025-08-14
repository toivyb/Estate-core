import pickle
import numpy as np

with open("models/health_model.pkl", "rb") as f:
    model = pickle.load(f)

def compute_health_score(data):
    X = np.array([[data["open_issues"], data["net_profit"], data["vacancy_rate"]]])
    score = model.predict(X)[0]
    return "High" if score == 1 else "Low"
