import pandas as pd

from nem_demand_forecasting.features import add_forecast_features, merge_weather_backward


def make_demand(rows: int = 2200) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01 00:00", periods=rows, freq="5min")
    return pd.DataFrame(
        {
            "SETTLEMENTDATE": timestamps,
            "TOTALDEMAND": range(rows),
        }
    )


def test_target_is_30_minutes_ahead() -> None:
    df = add_forecast_features(make_demand())

    assert df.loc[0, "FORECAST_TIME"] == pd.Timestamp("2026-01-01 00:30")
    assert df.loc[0, "target_30m"] == 6


def test_historical_target_time_lags_are_correct() -> None:
    df = add_forecast_features(make_demand())

    # At row 282, the target is row 288. The same target time yesterday is row 0.
    assert df.loc[282, "same_time_yesterday"] == 0

    # At row 2010, the target is row 2016. The same target time last week is row 0.
    assert df.loc[2010, "same_time_last_week"] == 0


def test_calendar_features_describe_forecast_time() -> None:
    data = pd.DataFrame(
        {
            "SETTLEMENTDATE": pd.date_range(
                "2026-01-04 23:45",
                periods=20,
                freq="5min",
            ),
            "TOTALDEMAND": range(20),
        }
    )

    df = add_forecast_features(data)

    # Sunday 23:45 + 30 minutes = Monday 00:15.
    assert df.loc[0, "target_day_of_week"] == 0
    assert df.loc[0, "target_hour"] == 0
    assert df.loc[0, "target_minute"] == 15
    assert df.loc[0, "target_is_weekend"] == 0


def test_weather_join_never_uses_future_observation() -> None:
    demand = pd.DataFrame(
        {
            "SETTLEMENTDATE": pd.to_datetime(
                ["2026-01-01 00:05", "2026-01-01 00:55", "2026-01-01 01:05"]
            ),
            "TOTALDEMAND": [100, 110, 120],
        }
    )

    weather = pd.DataFrame(
        {
            "SETTLEMENTDATE": pd.to_datetime(
                ["2026-01-01 00:00", "2026-01-01 01:00"]
            ),
            "temperature_2m": [20.0, 21.0],
        }
    )

    merged = merge_weather_backward(demand, weather)

    assert list(merged["temperature_2m"]) == [20.0, 20.0, 21.0]
    assert (merged["WEATHER_TIME"] <= merged["SETTLEMENTDATE"]).all()
