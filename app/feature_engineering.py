"""
Shared feature engineering for the cinnamon price model.

CRITICAL: this module is imported by BOTH train_models.py and forecast.py.
Training and inference must build features the exact same way, or the model
receives inputs at prediction time that don't match what it learned from.
Never duplicate this logic inline in either file — always import from here.
"""

import numpy as np
import pandas as pd

WINDOW_SIZE = 8


def build_feature_vector(window_prices, reference_date):
    """
    Turn a raw price window into an engineered feature vector.

    window_prices: array-like of WINDOW_SIZE prices, oldest -> newest.
    reference_date: the date of the value being predicted (the *target* date,
        not the last date in the window). At training time this is the actual
        date of that historical row. At inference time this is "last known
        date + 1 week", since that's what we're forecasting.

    Returns a 1D numpy array: [raw window..., moving_avg, volatility,
    momentum, pct_change, trend_slope, week_of_year]
    """
    window = np.asarray(window_prices, dtype=float)

    moving_avg = window.mean()
    volatility = window.std()
    momentum = window[-1] - window[0]                     # net move across the window
    pct_change = (window[-1] - window[-2]) / window[-2] if window[-2] != 0 else 0.0
    trend_slope = np.polyfit(np.arange(len(window)), window, 1)[0]  # direction/strength of trend
    week_of_year = pd.Timestamp(reference_date).isocalendar().week  # captures seasonal harvest cycles

    return np.concatenate([
        window,
        [moving_avg, volatility, momentum, pct_change, trend_slope, week_of_year]
    ])


def build_training_matrix(prices_values, dates_values, window_size=WINDOW_SIZE):
    """
    Slide a window across the full price history and build (X, y_delta, y_level)
    for every valid position.

    y_delta  = price[t+1] - price[t]   <- what the model actually learns to predict
    y_level  = price[t+1]              <- kept alongside for evaluation/reporting only
    """
    X, y_delta, y_level = [], [], []
    n = len(prices_values)

    for i in range(n - window_size):
        window = prices_values[i:i + window_size]
        target_price = prices_values[i + window_size]
        target_date = dates_values[i + window_size]

        features = build_feature_vector(window, target_date)
        delta = target_price - window[-1]

        X.append(features)
        y_delta.append(delta)
        y_level.append(target_price)

    return np.array(X), np.array(y_delta), np.array(y_level)