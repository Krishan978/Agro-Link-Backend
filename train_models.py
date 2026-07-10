import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os
from app.config import settings
from app.feature_engineering import build_training_matrix, WINDOW_SIZE

CINNAMON_COLUMNS = {
    "alba": "Alba (Average Price)",
    "c5": "C-5 (Average Price)",
    "c4": "C-4 (Average Price)",
    "m5": "M-5 (Average Price)"
}

# Below this many rows, a model's evaluation metrics are close to meaningless
# and RandomForest/GBM will just overfit noise. Skip training rather than
# silently ship a model nobody should trust.
MIN_SAMPLES = 30

# Model hyperparameters. Kept fixed (not grid-searched) since most district/grade
# groups are small enough that a search would overfit the search itself.
# Tune these manually if you see systematic under/overfitting in the printed metrics.
MODEL_PARAMS = dict(
    n_estimators=200,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.8,
    random_state=42
)


def load_data(csv_url):
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()
    df['District'] = df['District'].str.strip()
    df['District'] = df['District'].replace({'atnapura': 'Ratnapura', 'Rathnapura': 'Ratnapura'})
    df['Date'] = pd.to_datetime(df['Date'])
    return df


def evaluate_with_time_series_cv(X, y_delta, y_level, n_splits=3):
    """
    Honest evaluation on small time-series data: walk forward through the data
    instead of a single fixed split, so the reported R²/MAE isn't just luck
    from wherever the 80/20 cut happened to land.
    """
    n_splits = min(n_splits, max(2, len(X) // 15))  # don't ask for more folds than the data supports
    tscv = TimeSeriesSplit(n_splits=n_splits)

    fold_r2, fold_mae = [], []
    for train_idx, test_idx in tscv.split(X):
        model = GradientBoostingRegressor(**MODEL_PARAMS)
        model.fit(X[train_idx], y_delta[train_idx])

        pred_delta = model.predict(X[test_idx])
        # Reconstruct predicted price level for a real-world-meaningful MAE/R²:
        # last known price in each test window + predicted delta.
        last_prices_in_window = X[test_idx][:, WINDOW_SIZE - 1]
        pred_level = last_prices_in_window + pred_delta

        fold_r2.append(r2_score(y_level[test_idx], pred_level))
        fold_mae.append(mean_absolute_error(y_level[test_idx], pred_level))

    return float(np.mean(fold_r2)), float(np.mean(fold_mae))


def train_all_models():
    url = "https://docs.google.com/spreadsheets/d/1k8QWX6YR1XO3_zWfszGXGMqJgsVnJtqHnfWfWrGINLo/export?format=csv"
    print("Connecting to Google Sheets...")
    df = load_data(url)
    master_payload = {}

    for district in df['District'].unique():
        print(f"\n--- Training for District: {district} ---")
        district_df = df[df['District'] == district]

        for grade, col in CINNAMON_COLUMNS.items():
            if col not in district_df.columns:
                continue

            temp_df = district_df[['Date', col]].dropna().sort_values('Date')
            prices = pd.to_numeric(temp_df[col].astype(str).str.replace(',', ''), errors='coerce')
            temp_df = temp_df.assign(price=prices).dropna(subset=['price'])

            prices_values = temp_df['price'].values
            dates_values = temp_df['Date'].values

            if len(prices_values) < MIN_SAMPLES:
                print(f"  Grade {grade}: skipped ({len(prices_values)} rows, need {MIN_SAMPLES}+)")
                continue

            X, y_delta, y_level = build_training_matrix(prices_values, dates_values)

            r2, mae = evaluate_with_time_series_cv(X, y_delta, y_level)
            print(f"  Grade: {grade} | R²: {r2:.2f} | MAE: {mae:.2f} LKR (time-series CV, {len(X)} windows)")

            # Final production model: trained on ALL available data, since we've
            # already gotten an honest performance read from CV above. Holding
            # back a test set here would only make the deployed model worse.
            final_model = GradientBoostingRegressor(**MODEL_PARAMS)
            final_model.fit(X, y_delta)

            master_payload[f"{district.lower().strip()}_{grade}"] = {
                "district": district.lower().strip(),
                "grade": grade,
                "model": final_model,
                "predicts_delta": True,  # marks this as a delta-predicting model for forecast.py
                "last_known_window": prices_values[-WINDOW_SIZE:].tolist(),
                "last_date": pd.to_datetime(dates_values[-1]).isoformat(),
                "historical_prices": prices_values[-3:].tolist(),
                "r2": r2,
                "mae": mae
            }

    os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
    tmp_path = settings.MODEL_PATH + ".tmp"
    joblib.dump(master_payload, tmp_path)
    os.replace(tmp_path, settings.MODEL_PATH)
    print(f"\n🚀 Training complete! {len(master_payload)} models saved to {settings.MODEL_PATH}")


if __name__ == "__main__":
    train_all_models()