from pathlib import Path

from nem_demand_forecasting.data import download_range, load_monthly_files
from nem_demand_forecasting.validation import validate_demand_series


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

START_MONTH = "2024-07"
END_MONTH = "2026-06"
REGION = "VIC1"


def main() -> None:
    paths = download_range(
        start=START_MONTH,
        end=END_MONTH,
        region=REGION,
        output_dir=RAW_DIR,
    )

    df = load_monthly_files(paths)
    validation = validate_demand_series(df, expected_region=REGION)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "vic_demand_2024-07_to_2026-06.parquet"
    df.to_parquet(output_path, index=False)

    print()
    print("Demand dataset validated")
    print(f"Rows: {validation['rows']:,}")
    print(f"Start: {validation['start']}")
    print(f"End: {validation['end']}")
    print(f"Region: {validation['region']}")
    print(f"Interval: {validation['interval_minutes']} minutes")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
