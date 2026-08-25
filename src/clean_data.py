"""
src/clean_data.py

Loads and cleans raw crash CSV data (NYC Open Data schema, or the
bundled synthetic sample). Handles missing coordinates, parses dates,
and standardizes column names.
"""

import pandas as pd


REQUIRED_COLUMNS = [
    "CRASH_DATE", "CRASH_TIME", "BOROUGH", "LATITUDE", "LONGITUDE",
    "NUMBER_OF_PERSONS_INJURED", "NUMBER_OF_PERSONS_KILLED",
]


def load_raw_crashes(path: str) -> pd.DataFrame:
    """Load a raw crash CSV file into a DataFrame."""
    df = pd.read_csv(path)
    # Normalize column names: uppercase, spaces -> underscores
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]
    return df


def clean_crashes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw crash DataFrame:
      - drop rows missing lat/lon (can't be mapped or clustered)
      - drop obviously invalid coordinates (0,0 or out of NYC bounding box)
      - parse CRASH_DATE / CRASH_TIME into a single datetime column
      - fill missing injury/fatality counts with 0
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.copy()

    # Drop missing coordinates
    df = df.dropna(subset=["LATITUDE", "LONGITUDE"])

    # Drop invalid / placeholder coordinates (0,0) and anything wildly
    # outside a generous NYC bounding box -- adjust bounds for your city
    df = df[(df["LATITUDE"] != 0) & (df["LONGITUDE"] != 0)]
    df = df[df["LATITUDE"].between(40.4, 41.0)]
    df = df[df["LONGITUDE"].between(-74.3, -73.6)]

    # Parse datetime
    df["CRASH_DATETIME"] = pd.to_datetime(
        df["CRASH_DATE"].astype(str) + " " + df["CRASH_TIME"].astype(str),
        errors="coerce",
    )
    df = df.dropna(subset=["CRASH_DATETIME"])

    df["HOUR"] = df["CRASH_DATETIME"].dt.hour
    df["DAY_OF_WEEK"] = df["CRASH_DATETIME"].dt.day_name()
    df["MONTH"] = df["CRASH_DATETIME"].dt.month

    # Fill missing injury/fatality counts
    df["NUMBER_OF_PERSONS_INJURED"] = df["NUMBER_OF_PERSONS_INJURED"].fillna(0)
    df["NUMBER_OF_PERSONS_KILLED"] = df["NUMBER_OF_PERSONS_KILLED"].fillna(0)

    df["IS_FATAL"] = df["NUMBER_OF_PERSONS_KILLED"] > 0
    df["IS_INJURY"] = df["NUMBER_OF_PERSONS_INJURED"] > 0

    return df.reset_index(drop=True)


def load_and_clean(path: str) -> pd.DataFrame:
    """Convenience wrapper: load raw CSV and return a cleaned DataFrame."""
    raw = load_raw_crashes(path)
    return clean_crashes(raw)


if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/sample_crashes.csv"
    df = load_and_clean(input_path)
    print(f"Loaded and cleaned {len(df)} crash records from {input_path}")
    print(df.head())
