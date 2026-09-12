from pathlib import Path

import pandas as pd
import requests


ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

MELBOURNE_LATITUDE = -37.8136
MELBOURNE_LONGITUDE = 144.9631


def download_melbourne_weather(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Download hourly historical Melbourne weather from Open-Meteo."""

    params = {
        "latitude": MELBOURNE_LATITUDE,
        "longitude": MELBOURNE_LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "precipitation",
                "wind_speed_10m",
            ]
        ),
        "timezone": "GMT",
    }

    response = requests.get(
        ARCHIVE_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    weather = pd.DataFrame(
        payload["hourly"]
    )

    weather["time"] = pd.to_datetime(
        weather["time"]
    )

    # AEMO market timestamps use fixed AEST (UTC+10).
    weather["SETTLEMENTDATE"] = (
        weather["time"]
        + pd.Timedelta(hours=10)
    )

    weather = weather.drop(
        columns=["time"]
    )

    return weather


def save_weather(
    weather: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save processed weather data as Parquet."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    weather.to_parquet(
        output_path,
        index=False,
    )