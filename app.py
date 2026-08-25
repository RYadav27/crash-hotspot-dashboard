"""
app.py

Streamlit dashboard for crash hotspot analysis.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

from src.clean_data import load_and_clean
from src.hotspot_analysis import find_hotspots, summarize_by_hour, summarize_by_factor
from src.build_map import build_heatmap, build_hotspot_map

st.set_page_config(page_title="Crash Hotspot Dashboard", layout="wide")

st.title("🚧 Traffic Crash Hotspot Dashboard")
st.caption("DBSCAN spatial clustering on crash data to identify high-risk locations")

with st.sidebar:
    st.header("Data")
    data_path = st.text_input("CSV path", value="data/raw/sample_crashes.csv")

    st.header("Clustering Parameters")
    eps_km = st.slider("Cluster radius (km)", 0.05, 0.5, 0.15, 0.01,
                        help="Max distance between points in the same hotspot")
    min_samples = st.slider("Min crashes per hotspot", 3, 30, 8, 1)

    st.markdown("---")
    st.caption(
        "Default data is a **synthetic sample** with realistic clusters. "
        "Run `python download_data.py` to pull real NYC Open Data crash "
        "records, then point this at `data/raw/nyc_crashes.csv`."
    )

try:
    df = load_and_clean(data_path)
except FileNotFoundError:
    st.error(f"Could not find file: {data_path}")
    st.stop()
except ValueError as e:
    st.error(f"Data error: {e}")
    st.stop()

st.success(f"Loaded {len(df):,} cleaned crash records.")

# --- Top-line metrics ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Crashes", f"{len(df):,}")
c2.metric("Total Injuries", f"{int(df['NUMBER_OF_PERSONS_INJURED'].sum()):,}")
c3.metric("Total Fatalities", f"{int(df['NUMBER_OF_PERSONS_KILLED'].sum()):,}")
c4.metric("Date Range",
          f"{df['CRASH_DATETIME'].min().date()} → {df['CRASH_DATETIME'].max().date()}")

# --- Run clustering ---
clustered_df, hotspots = find_hotspots(df, eps_km=eps_km, min_samples=min_samples)

n_hotspots = len(hotspots)
n_noise = int((clustered_df["CLUSTER"] == -1).sum())
st.info(f"Identified **{n_hotspots} hotspots** covering "
        f"**{len(df) - n_noise:,} crashes** "
        f"({n_noise:,} crashes did not cluster into a hotspot).")

tab1, tab2, tab3 = st.tabs(["🗺️ Hotspot Map", "🔥 Density Heatmap", "📊 Patterns"])

with tab1:
    st.subheader("Top Hotspots")
    if hotspots.empty:
        st.warning("No hotspots found with current parameters -- try increasing "
                    "cluster radius or lowering min crashes per hotspot.")
    else:
        top_n = st.slider("Number of hotspots to show", 5, min(50, len(hotspots)), 20)
        hotspot_map = build_hotspot_map(hotspots, top_n=top_n)
        st_folium(hotspot_map, width=None, height=550)

        st.subheader("Hotspot Details")
        display_cols = [c for c in ["hotspot_id", "crash_count", "common_location",
                                     "total_injured", "total_killed"]
                         if c in hotspots.columns]
        st.dataframe(hotspots[display_cols].head(top_n), use_container_width=True)

with tab2:
    st.subheader("Crash Density Heatmap")
    heatmap = build_heatmap(df)
    st_folium(heatmap, width=None, height=550)

with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Crashes by Hour of Day")
        hourly = summarize_by_hour(df)
        fig, ax = plt.subplots()
        ax.bar(hourly.index, hourly.values, color="#d73027")
        ax.set_xlabel("Hour of day")
        ax.set_ylabel("Crash count")
        st.pyplot(fig)

    with col2:
        st.subheader("Top Contributing Factors")
        factors = summarize_by_factor(df)
        fig2, ax2 = plt.subplots()
        ax2.barh(factors.index[::-1], factors.values[::-1], color="#4575b4")
        ax2.set_xlabel("Crash count")
        st.pyplot(fig2)

st.markdown("---")
st.caption(
    "Data: NYC Open Data — Motor Vehicle Collisions - Crashes "
    "(or bundled synthetic sample). Clustering: scikit-learn DBSCAN "
    "with haversine distance."
)
