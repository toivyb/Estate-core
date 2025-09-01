import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

def train_health_model():
    df = pd.read_csv("training_data/asset_health.csv")
    X = df[["open_issues", "net_profit", "vacancy_rate"]]
    y = df["health_flag"]
    model = RandomForestClassifier()
    model.fit(X, y)
    with open("models/health_model.pkl", "wb") as f:
        pickle.dump(model, f)
