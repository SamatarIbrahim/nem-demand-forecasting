"""Model construction and evaluation helpers for the forecasting project."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


FINAL_XGB_PARAMS = {
    "objective": "reg:squarederror",
    "n_estimators": 800,
    "learning_rate": 0.05,
    "max_depth": 6,
    "min_child_weight": 5,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "random_state": 42,
    "n_jobs": -1,
}


def make_final_model() -> XGBRegressor:
    """Return the frozen XGBoost specification used for final evaluation."""

    return XGBRegressor(**FINAL_XGB_PARAMS)


def split_development_test(
    data: pd.DataFrame,
    test_start: str = "2026-05-01",
    test_end: str = "2026-07-01",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a feature frame into pre-test development data and the holdout period."""

    if "FORECAST_TIME" not in data.columns:
        raise ValueError("FORECAST_TIME is required to create the chronological split.")

    development = data[data["FORECAST_TIME"] < test_start].copy()
    test = data[
        (data["FORECAST_TIME"] >= test_start) & (data["FORECAST_TIME"] < test_end)
    ].copy()

    if development.empty or test.empty:
        raise ValueError("Chronological split produced an empty development or test set.")

    return development, test


def evaluate_predictions(
    actual: pd.Series | np.ndarray,
    predicted: pd.Series | np.ndarray,
) -> dict[str, float]:
    """Return headline regression metrics and absolute-error quantiles."""

    actual_values = np.asarray(actual)
    predicted_values = np.asarray(predicted)

    if actual_values.shape != predicted_values.shape:
        raise ValueError("Actual and predicted arrays must have the same shape.")

    absolute_error = np.abs(actual_values - predicted_values)

    return {
        "mae_mw": float(mean_absolute_error(actual_values, predicted_values)),
        "rmse_mw": float(np.sqrt(mean_squared_error(actual_values, predicted_values))),
        "median_absolute_error_mw": float(np.quantile(absolute_error, 0.50)),
        "p90_absolute_error_mw": float(np.quantile(absolute_error, 0.90)),
        "p95_absolute_error_mw": float(np.quantile(absolute_error, 0.95)),
        "p99_absolute_error_mw": float(np.quantile(absolute_error, 0.99)),
    }
