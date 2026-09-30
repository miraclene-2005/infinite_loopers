"""
Training script for Hazard Spread Prediction Model.
Predicts:
- red_zone_m, orange_zone_m, yellow_zone_m
- spread_direction (downwind_direction)
- recommended_response
Saves artifacts to models/spread_model.pkl
"""
import os
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "chemical_spread_aloha_informed_synthetic.csv"
MODEL_PATH = BASE_DIR / "models" / "spread_model.pkl"

def train():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    feature_cols_cat = ["chemical", "wind_direction", "atmospheric_stability"]
    feature_cols_num = [
        "release_amount_kg",
        "release_duration_min",
        "wind_speed_kmh",
        "temperature_c",
        "source_height_m"
    ]

    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), feature_cols_num),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), feature_cols_cat),
        ]
    )

    X = df[feature_cols_num + feature_cols_cat]
    X_trans = preprocessor.fit_transform(X)

    # 1. Zone Distance Regressor (red, orange, yellow)
    y_zones = df[["red_zone_m", "orange_zone_m", "yellow_zone_m"]]
    reg_zones = RandomForestRegressor(n_estimators=100, random_state=42)
    reg_zones.fit(X_trans, y_zones)
    print("Zone regressor trained successfully.")

    # 2. Spread Direction Classifier
    y_dir = df["downwind_direction"]
    clf_dir = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_dir.fit(X_trans, y_dir)
    print("Spread direction classifier trained successfully.")

    # 3. Recommended Response Classifier
    y_resp = df["recommended_response"]
    clf_resp = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_resp.fit(X_trans, y_resp)
    print("Recommended response classifier trained successfully.")

    bundle = {
        "preprocessor": preprocessor,
        "feature_cols_num": feature_cols_num,
        "feature_cols_cat": feature_cols_cat,
        "reg_zones": reg_zones,
        "clf_dir": clf_dir,
        "clf_resp": clf_resp
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
