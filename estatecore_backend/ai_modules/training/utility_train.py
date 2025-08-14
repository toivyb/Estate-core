import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle

def train_utility_model():
    df = pd.read_csv("training_data/utility_data.csv")
    X = df[["avg_temp", "occupants", "unit_size_sqft"]]
    y = df["monthly_usage"]
    model = LinearRegression()
    model.fit(X, y)
    with open("models/utility_model.pkl", "wb") as f:
        pickle.dump(model, f)
