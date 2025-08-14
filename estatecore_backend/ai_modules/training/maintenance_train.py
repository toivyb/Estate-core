import pandas as pd
from sklearn.linear_model import LogisticRegression
import pickle

def train_maintenance_model():
    df = pd.read_csv("training_data/maintenance_data.csv")
    X = df[["age_months", "last_service_months_ago", "incident_reports"]]
    y = df["likely_failure"]
    model = LogisticRegression()
    model.fit(X, y)
    with open("models/maintenance_model.pkl", "wb") as f:
        pickle.dump(model, f)
