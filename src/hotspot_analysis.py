"""
src/hotspot_analysis.py

Finds crash hotspots using DBSCAN spatial clustering on crash
coordinates. DBSCAN is well-suited to this task because hotspots are
irregularly shaped and we don't know the number of clusters in
advance (unlike k-means).
"""

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

KMS_PER_RADIAN = 6371.0088


def find_hotspots(df: pd.DataFrame,
                   lat_col: str = "LATITUDE",
                   lon_col: str = "LONGITUDE",
                   eps_km: float = 0.15,
                   min_samples: int = 8) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cluster crash points using DBSCAN with haversine distance.

    Args:
        df: cleaned crash DataFrame (must have lat/lon columns)
        eps_km: neighborhood radius in kilometers -- points within this
            distance of each other are considered "close." Smaller =
            tighter, more numerous clusters. 0.1-0.2 km is a reasonable
            starting point for street-level hotspots.
        min_samples: minimum number of crashes required to form a
            hotspot (DBSCAN's min_samples). Higher = fewer, more
            significant hotspots.

    Returns:
        (df_with_cluster_labels, hotspot_summary)
        - df_with_cluster_labels: original df + a "CLUSTER" column
          (-1 means "not part of any hotspot" / noise)
        - hotspot_summary: one row per hotspot, sorted by crash count
          descending, with center coordinates and severity stats
    """
    df = df.dropna(subset=[lat_col, lon_col]).copy()
    if df.empty:
        raise ValueError("No valid coordinates to cluster.")

    coords = np.radians(df[[lat_col, lon_col]].to_numpy())
    eps = eps_km / KMS_PER_RADIAN

    db = DBSCAN(eps=eps, min_samples=min_samples, algorithm="ball_tree",
                metric="haversine")
    df["CLUSTER"] = db.fit_predict(coords)

    n_hotspots = len(set(df["CLUSTER"])) - (1 if -1 in df["CLUSTER"].values else 0)
    n_noise = int((df["CLUSTER"] == -1).sum())
    print(f"Found {n_hotspots} hotspots covering "
          f"{len(df) - n_noise} crashes ({n_noise} points classified as noise).")

    agg_dict = {
        "crash_count": (lat_col, "size"),
        "center_lat": (lat_col, "mean"),
        "center_lon": (lon_col, "mean"),
    }
    if "NUMBER_OF_PERSONS_INJURED" in df.columns:
        agg_dict["total_injured"] = ("NUMBER_OF_PERSONS_INJURED", "sum")
    if "NUMBER_OF_PERSONS_KILLED" in df.columns:
        agg_dict["total_killed"] = ("NUMBER_OF_PERSONS_KILLED", "sum")
    if "ON_STREET_NAME" in df.columns:
        agg_dict["common_location"] = (
            "ON_STREET_NAME",
            lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown",
        )

    hotspots = (
        df[df["CLUSTER"] != -1]
        .groupby("CLUSTER")
        .agg(**agg_dict)
        .sort_values("crash_count", ascending=False)
        .reset_index()
        .rename(columns={"CLUSTER": "hotspot_id"})
    )

    return df, hotspots


def summarize_by_hour(df: pd.DataFrame) -> pd.Series:
    """Crash counts by hour of day, useful for a time-of-day chart."""
    if "HOUR" not in df.columns:
        raise ValueError("DataFrame must have an HOUR column (run clean_data first).")
    return df["HOUR"].value_counts().sort_index()


def summarize_by_factor(df: pd.DataFrame, top_n: int = 10) -> pd.Series:
    """Top N contributing factors across all crashes."""
    col = "CONTRIBUTING_FACTOR_VEHICLE_1"
    if col not in df.columns:
        raise ValueError(f"DataFrame must have a {col} column.")
    return df[col].value_counts().head(top_n)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from src.clean_data import load_and_clean

    df = load_and_clean("data/raw/sample_crashes.csv")
    clustered_df, hotspots = find_hotspots(df)
    print("\nTop hotspots:")
    print(hotspots.head(10))
