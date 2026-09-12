from pathlib import Path

import pandas as pd
import requests


BASE_URL = "https://www.aemo.com.au/aemo/data/nem/priceanddemand"


def download_month(
    year: int,
    month: int,
    region: str,
    output_dir: Path,
    overwrite: bool = False,
) -> Path:
    """Download one month of AEMO price and demand data."""

    filename = f"PRICE_AND_DEMAND_{year}{month:02d}_{region}.csv"
    url = f"{BASE_URL}/{filename}"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    if output_path.exists() and not overwrite:
        print(f"Already exists: {filename}")
        return output_path

    print(f"Downloading: {filename}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    output_path.write_bytes(response.content)

    return output_path


def download_range(
    start: str,
    end: str,
    region: str,
    output_dir: Path,
) -> list[Path]:
    """Download monthly AEMO files between two YYYY-MM dates."""

    months = pd.period_range(start=start, end=end, freq="M")

    paths = []

    for period in months:
        path = download_month(
            year=period.year,
            month=period.month,
            region=region,
            output_dir=output_dir,
        )
        paths.append(path)

    return paths

def load_monthly_files(paths: list[Path]) -> pd.DataFrame:
    """Load and combine multiple AEMO monthly CSV files."""

    frames = []

    for path in paths:
        df = pd.read_csv(
            path,
            parse_dates=["SETTLEMENTDATE"],
        )

        frames.append(df)

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    combined = (
        combined
        .sort_values("SETTLEMENTDATE")
        .reset_index(drop=True)
    )

    return combined