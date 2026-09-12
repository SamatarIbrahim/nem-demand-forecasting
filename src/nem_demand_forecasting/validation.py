"""Structural validation helpers for processed AEMO demand data."""

from __future__ import annotations

import pandas as pd


REQUIRED_DEMAND_COLUMNS = {
    "REGION",
    "SETTLEMENTDATE",
    "TOTALDEMAND",
    "RRP",
    "PERIODTYPE",
}


def validate_demand_series(
    data: pd.DataFrame,
    expected_region: str = "VIC1",
    expected_interval_minutes: int = 5,
) -> dict[str, object]:
    """Validate the structural assumptions used by the forecasting pipeline.

    Raises ``ValueError`` when required columns, timestamp continuity, uniqueness,
    region consistency, or required values do not meet expectations.
    """

    missing_columns = REQUIRED_DEMAND_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    if data.empty:
        raise ValueError("Demand dataset is empty.")

    df = data.sort_values("SETTLEMENTDATE").reset_index(drop=True)

    required_nulls = df[list(REQUIRED_DEMAND_COLUMNS)].isna().sum()
    if int(required_nulls.sum()) > 0:
        affected = required_nulls[required_nulls > 0].to_dict()
        raise ValueError(f"Missing values in required columns: {affected}")

    duplicate_count = int(df["SETTLEMENTDATE"].duplicated().sum())
    if duplicate_count:
        raise ValueError(f"Found {duplicate_count} duplicate settlement timestamps.")

    regions = set(df["REGION"].astype(str).unique())
    if regions != {expected_region}:
        raise ValueError(f"Expected region {expected_region!r}, found {sorted(regions)}.")

    expected_delta = pd.Timedelta(minutes=expected_interval_minutes)
    deltas = df["SETTLEMENTDATE"].diff().dropna()
    bad_intervals = deltas[deltas != expected_delta]
    if not bad_intervals.empty:
        first_bad_index = int(bad_intervals.index[0])
        previous_time = df.loc[first_bad_index - 1, "SETTLEMENTDATE"]
        current_time = df.loc[first_bad_index, "SETTLEMENTDATE"]
        raise ValueError(
            "Demand timestamps are not continuous at "
            f"{previous_time} -> {current_time}; expected {expected_delta}."
        )

    return {
        "rows": len(df),
        "start": df["SETTLEMENTDATE"].min(),
        "end": df["SETTLEMENTDATE"].max(),
        "region": expected_region,
        "interval_minutes": expected_interval_minutes,
        "duplicate_timestamps": duplicate_count,
    }
