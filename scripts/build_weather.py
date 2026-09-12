from pathlib import Path

from nem_demand_forecasting.weather import (
    download_melbourne_weather,
    save_weather,
)


OUTPUT_PATH = (
    Path("data/processed")
    / "melbourne_weather_2024-07_to_2026-06.parquet"
)


def main() -> None:
    weather = download_melbourne_weather(
        start_date="2024-06-30",
        end_date="2026-06-30",
    )

    save_weather(
        weather,
        OUTPUT_PATH,
    )

    print(f"Rows: {len(weather):,}")
    print(
        "Start:",
        weather["SETTLEMENTDATE"].min(),
    )
    print(
        "End:",
        weather["SETTLEMENTDATE"].max(),
    )

    print()
    print(weather.isna().sum())

    print()
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()