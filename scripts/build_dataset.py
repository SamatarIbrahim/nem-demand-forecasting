from pathlib import Path

from nem_demand_forecasting.data import (
    download_range,
    load_monthly_files,
)


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

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DIR
        / "vic_demand_2024-07_to_2026-06.parquet"
    )

    df.to_parquet(
        output_path,
        index=False,
    )

    print()
    print(f"Rows: {len(df):,}")
    print(f"Start: {df['SETTLEMENTDATE'].min()}")
    print(f"End: {df['SETTLEMENTDATE'].max()}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()