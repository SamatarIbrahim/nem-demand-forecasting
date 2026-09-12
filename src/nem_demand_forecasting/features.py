"""Feature engineering for 30-minute Victorian demand forecasting."""

from __future__ import annotations

import pandas as pd


FORECAST_HORIZON_INTERVALS = 6
INTERVAL_MINUTES = 5

BASE_FEATURES = [
    "demand_current",
    "demand_lag_5m",
    "demand_lag_15m",
    "demand_lag_30m",
    "demand_lag_1h",
    "demand_lag_2h",
    "same_time_yesterday",
    "same_time_last_week",
    "change_15m",
    "change_30m",
    "change_1h",
    "rolling_mean_30m",
    "rolling_mean_1h",
    "rolling_std_1h",
    "target_hour",
    "target_minute",
    "target_day_of_week",
    "target_month",
    "target_is_weekend",
]

WEATHER_FEATURES = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
]

FINAL_FEATURES = BASE_FEATURES + WEATHER_FEATURES


def add_forecast_features(
    data: pd.DataFrame,
    horizon_intervals: int = FORECAST_HORIZON_INTERVALS,
) -> pd.DataFrame:
    """Return a copy with leakage-safe features for a future demand target.

    The input must be sorted at five-minute frequency and contain
    ``SETTLEMENTDATE`` and ``TOTALDEMAND``. Calendar features describe the
    target timestamp rather than the forecast-issue timestamp.
    """

    required = {"SETTLEMENTDATE", "TOTALDEMAND"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = data.sort_values("SETTLEMENTDATE").reset_index(drop=True).copy()

    horizon_minutes = horizon_intervals * INTERVAL_MINUTES
    df["FORECAST_TIME"] = df["SETTLEMENTDATE"] + pd.Timedelta(minutes=horizon_minutes)
    df["target_30m"] = df["TOTALDEMAND"].shift(-horizon_intervals)

    df["demand_current"] = df["TOTALDEMAND"]
    df["demand_lag_5m"] = df["TOTALDEMAND"].shift(1)
    df["demand_lag_15m"] = df["TOTALDEMAND"].shift(3)
    df["demand_lag_30m"] = df["TOTALDEMAND"].shift(6)
    df["demand_lag_1h"] = df["TOTALDEMAND"].shift(12)
    df["demand_lag_2h"] = df["TOTALDEMAND"].shift(24)

    intervals_per_day = 24 * 60 // INTERVAL_MINUTES
    intervals_per_week = 7 * intervals_per_day
    df["same_time_yesterday"] = df["TOTALDEMAND"].shift(
        intervals_per_day - horizon_intervals
    )
    df["same_time_last_week"] = df["TOTALDEMAND"].shift(
        intervals_per_week - horizon_intervals
    )

    df["change_15m"] = df["TOTALDEMAND"] - df["TOTALDEMAND"].shift(3)
    df["change_30m"] = df["TOTALDEMAND"] - df["TOTALDEMAND"].shift(6)
    df["change_1h"] = df["TOTALDEMAND"] - df["TOTALDEMAND"].shift(12)

    df["rolling_mean_30m"] = df["TOTALDEMAND"].rolling(6).mean()
    df["rolling_mean_1h"] = df["TOTALDEMAND"].rolling(12).mean()
    df["rolling_std_1h"] = df["TOTALDEMAND"].rolling(12).std()

    df["target_hour"] = df["FORECAST_TIME"].dt.hour
    df["target_minute"] = df["FORECAST_TIME"].dt.minute
    df["target_day_of_week"] = df["FORECAST_TIME"].dt.dayofweek
    df["target_month"] = df["FORECAST_TIME"].dt.month
    df["target_is_weekend"] = (df["target_day_of_week"] >= 5).astype(int)

    return df


def merge_weather_backward(
    demand: pd.DataFrame,
    weather: pd.DataFrame,
) -> pd.DataFrame:
    """Attach only the latest weather observation available at each demand timestamp."""

    left = demand.sort_values("SETTLEMENTDATE").copy()
    right = weather.copy()

    if "SETTLEMENTDATE" in right.columns and "WEATHER_TIME" not in right.columns:
        right = right.rename(columns={"SETTLEMENTDATE": "WEATHER_TIME"})

    right = right.sort_values("WEATHER_TIME")

    merged = pd.merge_asof(
        left,
        right,
        left_on="SETTLEMENTDATE",
        right_on="WEATHER_TIME",
        direction="backward",
    )

    if (merged["WEATHER_TIME"] > merged["SETTLEMENTDATE"]).any():
        raise ValueError("Weather merge introduced future information.")

    return merged
