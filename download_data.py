"""
download_data.py

Downloads real crash data from NYC Open Data's "Motor Vehicle
Collisions - Crashes" dataset via the Socrata Open Data API (SODA).
Free, no API key required for this volume.

Usage:
    python download_data.py                     # last 2 years, ~50k rows
    python download_data.py --limit 200000       # more rows
    python download_data.py --start 2022-01-01 --end 2024-12-31

Dataset home page (for reference / manual download):
    https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95
"""

import argparse
import requests
import pandas as pd

BASE_URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"


def download_crashes(start_date: str, end_date: str, limit: int, output_path: str):
    params = {
        "$where": f"crash_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'",
        "$limit": limit,
        "$order": "crash_date DESC",
    }
    print(f"Requesting up to {limit} records from {start_date} to {end_date}...")
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()

    df = pd.DataFrame(resp.json())
    if df.empty:
        print("No records returned -- check your date range.")
        return

    # Standardize column names to match clean_data.py's expectations
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} records to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download NYC crash data.")
    parser.add_argument("--start", default="2023-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2024-12-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=50000, help="Max rows to fetch")
    parser.add_argument("--output", default="data/raw/nyc_crashes.csv",
                         help="Output CSV path")
    args = parser.parse_args()

    download_crashes(args.start, args.end, args.limit, args.output)
