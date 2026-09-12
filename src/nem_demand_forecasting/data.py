from pathlib import Path

import requests


BASE_URL = "https://www.aemo.com.au/aemo/data/nem/priceanddemand"


def download_month(
    year: int,
    month: int,
    region: str,
    output_dir: Path,
) -> Path:
    filename = f"PRICE_AND_DEMAND_{year}{month:02d}_{region}.csv"
    url = f"{BASE_URL}/{filename}"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    output_path.write_bytes(response.content)

    return output_path