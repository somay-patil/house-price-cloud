"""Train the house price model and save it to model/model.joblib.

Uses data/house_prices.csv if it exists (replace it with YOUR ML-project data),
otherwise generates a synthetic dataset so the project runs out of the box.

Expected columns: area_sqft, bedrooms, bathrooms, age_years, location, price
"""
import json
import os
import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATA_PATH = "data/house_prices.csv"
NUM = ["area_sqft", "bedrooms", "bathrooms", "age_years"]
CAT = ["location"]


def make_synthetic(n=3000, seed=42):
    rng = np.random.default_rng(seed)
    loc_factor = {"Downtown": 1.5, "Suburb": 1.1, "Rural": 0.75, "Waterfront": 1.9}
    locs = rng.choice(list(loc_factor), n)
    area = rng.normal(1800, 600, n).clip(500, 5000)
    beds = rng.integers(1, 6, n)
    baths = rng.integers(1, 5, n)
    age = rng.integers(0, 60, n)
    price = (area * 120 + beds * 8000 + baths * 12000 - age * 900) * \
        np.array([loc_factor[l] for l in locs]) + rng.normal(0, 15000, n)
    return pd.DataFrame({"area_sqft": area.round(), "bedrooms": beds, "bathrooms": baths,
                         "age_years": age, "location": locs, "price": price.round()})


def main():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        print(f"Loaded {len(df)} rows from {DATA_PATH}")
    else:
        df = make_synthetic()
        os.makedirs("data", exist_ok=True)
        df.to_csv(DATA_PATH, index=False)
        print(f"No dataset found, generated synthetic data -> {DATA_PATH}")

    X, y = df[NUM + CAT], df["price"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CAT)],
                            remainder="passthrough")
    model = Pipeline([("pre", pre),
                      ("rf", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1))])
    model.fit(X_tr, y_tr)

    pred = model.predict(X_te)
    metrics = {"r2": round(r2_score(y_te, pred), 4),
               "mae": round(mean_absolute_error(y_te, pred), 2),
               "locations": sorted(df["location"].unique().tolist())}
    print("Metrics:", metrics)

    os.makedirs("model", exist_ok=True)
    joblib.dump(model, "model/model.joblib")
    with open("model/metrics.json", "w") as f:
        json.dump(metrics, f)
    print("Saved model/model.joblib")


if __name__ == "__main__":
    main()
