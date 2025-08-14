import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle

def train_revenue_model():
    df = pd.read_csv("training_data/revenue_data.csv")
    X = df[["units", "expected_rent", "actual_collected"]]
    y = df["leakage_flag"]
    model = LinearRegression()
    model.fit(X, y)
    with open("models/revenue_model.pkl", "wb") as f:
        pickle.dump(model, f)
