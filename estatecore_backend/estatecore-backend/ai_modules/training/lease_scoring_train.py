import pandas as pd
from sklearn.linear_model import LogisticRegression
import pickle

def train_lease_model():
    df = pd.read_csv("training_data/lease_history.csv")
    X = df[["late_payments", "on_time_months", "complaints"]]
    y = df["defaulted"]
    model = LogisticRegression()
    model.fit(X, y)
    with open("models/lease_model.pkl", "wb") as f:
        pickle.dump(model, f)
