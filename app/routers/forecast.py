from fastapi import APIRouter, HTTPException, Query
import joblib
import numpy as np
from datetime import datetime, timedelta
from app.feature_engineering import build_feature_vector, WINDOW_SIZE

router = APIRouter(prefix="/api/forecast", tags=["Forecasting"])


@router.get("/cinnamon")
async def get_forecast(type: str = Query(...), district: str = Query("national")):
    # 1. Load models
    master_payload = joblib.load("app/ml_models/cinnamon_model.pkl")
    key = f"{district.lower().strip()}_{type.lower().strip()}"

    if key not in master_payload:
        raise HTTPException(status_code=404, detail=f"Model for {key} not found.")

    data = master_payload[key]
    model = data["model"]
    window = np.array(data["last_known_window"])

    historical_prices = data["historical_prices"]
    current_price = historical_prices[-1]

    # 2. Date the forecast is actually for: last known data date + 1 week,
    # if available (new models). Falls back to server "now" for any older
    # model file that predates this field, so a stale .pkl doesn't 500.
    last_date_str = data.get("last_date")
    if last_date_str:
        target_date = datetime.fromisoformat(last_date_str) + timedelta(weeks=1)
    else:
        target_date = datetime.now() + timedelta(weeks=1)
    predicted_until = target_date.strftime("%Y-%m-%d")

    # 3. Predict. Supports both the new delta-predicting models and any
    # older raw-level models still sitting in a not-yet-retrained .pkl.
    if data.get("predicts_delta"):
        features = build_feature_vector(window, target_date).reshape(1, -1)
        predicted_delta = float(model.predict(features)[0])
        predicted_price = current_price + predicted_delta
    else:
        # legacy path: old model predicted the raw price level directly
        predicted_price = float(model.predict(window.reshape(1, -1))[0])

    return {
        "commodity": f"Cinnamon {type.upper()}",
        "current_price": round(float(current_price), 2),
        "predicted_price": round(predicted_price, 2),
        "recommendation": "Hold Stock" if predicted_price > current_price else "Liquidate",
        "historical_prices": historical_prices,
        "predicted_until": predicted_until
    }