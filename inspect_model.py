"""
Standalone Model Inspector Script.
Run: python inspect_model.py
Displays model architecture, hyperparameters, classes, and sample predictions.
"""
from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path("models") / "spread_model.pkl"

def inspect():
    if not MODEL_PATH.exists():
        print(f"Model file not found at {MODEL_PATH}. Run python train_models/train_spread_model.py first.")
        return

    bundle = joblib.load(MODEL_PATH)
    print("=" * 65)
    print(" HAZARD SPREAD PREDICTION MODEL INSPECTOR")
    print("=" * 65)
    print(f"Artifact Path : {MODEL_PATH.resolve()}")
    print("\n[1] INPUT FEATURES")
    print(f"  - Numerical   : {bundle['feature_cols_num']}")
    print(f"  - Categorical : {bundle['feature_cols_cat']}")

    print("\n[2] COMPONENT MODELS")
    reg = bundle["reg_zones"]
    clf_d = bundle["clf_dir"]
    clf_r = bundle["clf_resp"]
    print(f"  - Plume Zone Regressor        : {type(reg).__name__} (Trees: {reg.n_estimators})")
    print(f"    Targets                     : ['red_zone_m', 'orange_zone_m', 'yellow_zone_m']")
    print(f"  - Spread Direction Classifier : {type(clf_d).__name__} (Trees: {clf_d.n_estimators})")
    print(f"    Classes                     : {list(clf_d.classes_)}")
    print(f"  - Response Policy Classifier  : {type(clf_r).__name__} (Trees: {clf_r.n_estimators})")
    print(f"    Classes                     : {list(clf_r.classes_)}")

    print("\n[3] SAMPLE INFERENCE TEST")
    sample_input = pd.DataFrame([{
        "release_amount_kg": 350.0,
        "release_duration_min": 8.0,
        "wind_speed_kmh": 16.0,
        "temperature_c": 30.0,
        "source_height_m": 0,
        "chemical": "Chlorine",
        "wind_direction": "NW",
        "atmospheric_stability": "D"
    }])
    X_trans = bundle["preprocessor"].transform(sample_input)
    zones = reg.predict(X_trans)[0]
    direction = clf_d.predict(X_trans)[0]
    response = clf_r.predict(X_trans)[0]

    print(f"  Scenario: Chlorine 350kg leak, wind 16km/h from NW")
    print(f"  -> Predicted Red Zone    : {zones[0]:.1f} meters")
    print(f"  -> Predicted Orange Zone : {zones[1]:.1f} meters")
    print(f"  -> Predicted Yellow Zone : {zones[2]:.1f} meters")
    print(f"  -> Plume Spread Direction: {direction}")
    print(f"  -> Recommended Response  : {response}")
    print("=" * 65)

if __name__ == "__main__":
    inspect()
