import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

def train_rent_delay_model():
    df = pd.read_csv("training_data/rent_history.csv")
    X = df[["late_payments", "average_days_late", "months_paid_on_time"]]
    y = df["likely_to_be_late"]
    model = RandomForestClassifier()
    model.fit(X, y)
    with open("models/rent_delay_model.pkl", "wb") as f:
        pickle.dump(model, f)
