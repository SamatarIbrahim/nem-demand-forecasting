import pandas as pd
import pytest

from nem_demand_forecasting.validation import validate_demand_series


def make_valid_frame() -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01 00:00:00", periods=4, freq="5min")
    return pd.DataFrame(
        {
            "REGION": ["VIC1"] * 4,
            "SETTLEMENTDATE": timestamps,
            "TOTALDEMAND": [5000.0, 5010.0, 5020.0, 5030.0],
            "RRP": [50.0, 51.0, 52.0, 53.0],
            "PERIODTYPE": ["TRADE"] * 4,
        }
    )


def test_validate_demand_series_accepts_clean_series() -> None:
    summary = validate_demand_series(make_valid_frame())

    assert summary["rows"] == 4
    assert summary["region"] == "VIC1"
    assert summary["interval_minutes"] == 5


def test_validate_demand_series_rejects_gap() -> None:
    frame = make_valid_frame().drop(index=2).reset_index(drop=True)

    with pytest.raises(ValueError, match="not continuous"):
        validate_demand_series(frame)


def test_validate_demand_series_rejects_duplicate_timestamp() -> None:
    frame = make_valid_frame()
    frame.loc[2, "SETTLEMENTDATE"] = frame.loc[1, "SETTLEMENTDATE"]

    with pytest.raises(ValueError, match="duplicate"):
        validate_demand_series(frame)


def test_validate_demand_series_rejects_wrong_region() -> None:
    frame = make_valid_frame()
    frame.loc[0, "REGION"] = "NSW1"

    with pytest.raises(ValueError, match="Expected region"):
        validate_demand_series(frame)
