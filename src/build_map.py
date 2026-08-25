"""
src/build_map.py

Builds interactive Folium maps: a heatmap of all crashes, and a
marker map highlighting the top hotspots identified by DBSCAN.
"""

import folium
from folium.plugins import HeatMap
import pandas as pd


def build_heatmap(df: pd.DataFrame,
                   lat_col: str = "LATITUDE",
                   lon_col: str = "LONGITUDE",
                   zoom_start: int = 12) -> folium.Map:
    """Build a density heatmap of all crash points."""
    center = [df[lat_col].mean(), df[lon_col].mean()]
    m = folium.Map(location=center, zoom_start=zoom_start, tiles="cartodbpositron")

    heat_data = df[[lat_col, lon_col]].dropna().values.tolist()
    HeatMap(heat_data, radius=10, blur=15).add_to(m)
    return m


def build_hotspot_map(hotspots: pd.DataFrame,
                       zoom_start: int = 12,
                       top_n: int = 20) -> folium.Map:
    """
    Build a marker map showing the top N hotspots, sized/colored by
    crash count severity.
    """
    if hotspots.empty:
        raise ValueError("No hotspots to plot.")

    top = hotspots.head(top_n)
    center = [top["center_lat"].mean(), top["center_lon"].mean()]
    m = folium.Map(location=center, zoom_start=zoom_start, tiles="cartodbpositron")

    max_count = top["crash_count"].max()

    for _, row in top.iterrows():
        crash_count = row["crash_count"]
        # Scale radius 8-25 px based on relative severity
        radius = 8 + (crash_count / max_count) * 17

        color = "#d73027" if crash_count > max_count * 0.6 else \
                "#fc8d59" if crash_count > max_count * 0.3 else "#fee08b"

        popup_lines = [f"<b>Hotspot #{int(row['hotspot_id'])}</b>",
                        f"Crashes: {int(crash_count)}"]
        if "common_location" in row:
            popup_lines.append(f"Near: {row['common_location']}")
        if "total_injured" in row:
            popup_lines.append(f"Total injured: {int(row['total_injured'])}")
        if "total_killed" in row:
            popup_lines.append(f"Total killed: {int(row['total_killed'])}")

        folium.CircleMarker(
            location=[row["center_lat"], row["center_lon"]],
            radius=radius,
            popup=folium.Popup("<br>".join(popup_lines), max_width=250),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
        ).add_to(m)

    return m


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from src.clean_data import load_and_clean
    from src.hotspot_analysis import find_hotspots

    df = load_and_clean("data/raw/sample_crashes.csv")
    clustered_df, hotspots = find_hotspots(df)

    heatmap = build_heatmap(clustered_df)
    heatmap.save("heatmap.html")
    print("Saved heatmap.html")

    hotspot_map = build_hotspot_map(hotspots)
    hotspot_map.save("hotspot_map.html")
    print("Saved hotspot_map.html")
