# 🚧 Traffic Crash Hotspot Dashboard

An interactive dashboard that identifies high-risk crash locations
using **DBSCAN spatial clustering**, built on real NYC Open Data
crash records (or the bundled synthetic sample for instant demo use).

## Demo

Run locally (see below). Add a screenshot/GIF here once you've run it:

```
[screenshot placeholder]
```

## Problem

Raw crash data is just a list of points — it doesn't tell you *where*
the recurring danger zones are. This tool clusters crash locations
spatially to surface hotspots, so safety improvements can be
prioritized by actual risk concentration rather than guesswork.

## Methodology

- **Clustering**: DBSCAN (Density-Based Spatial Clustering of
  Applications with Noise) using haversine distance on lat/lon. Chosen
  over k-means because hotspots are irregularly shaped and the number
  of hotspots isn't known ahead of time — DBSCAN discovers both
  automatically and labels sparse, non-clustered points as noise.
- **Parameters**: `eps_km` (max distance between points in the same
  cluster) and `min_samples` (min crashes to count as a hotspot) are
  adjustable live in the dashboard sidebar.

## Data

### Option A — Bundled synthetic sample (works immediately, no download)
`data/raw/sample_crashes.csv` — 930 synthetic records with 5 built-in
hotspot clusters plus background noise, matching the NYC Open Data
schema. Good for demoing the tool and for development, **not real
crash data**.

### Option B — Real NYC Open Data (recommended before showing this on your resume)
```bash
python download_data.py --start 2023-01-01 --end 2024-12-31 --limit 50000
```
This pulls from the free, no-API-key-required NYC Open Data Socrata
endpoint for the **Motor Vehicle Collisions - Crashes** dataset:
https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95

Then point the dashboard at `data/raw/nyc_crashes.csv` in the sidebar.

> Using a different city? Adjust `download_data.py`'s `BASE_URL` and
> field names to match your city's open data portal, and adjust the
> bounding-box filter in `src/clean_data.py`.

## How to run

```bash
git clone https://github.com/<your-username>/crash-hotspot-dashboard.git
cd crash-hotspot-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```
crash-hotspot-dashboard/
├── README.md
├── requirements.txt
├── download_data.py          # pulls real data from NYC Open Data API
├── data/
│   └── raw/
│       └── sample_crashes.csv  # synthetic sample, included for instant demo
├── src/
│   ├── clean_data.py          # loading, cleaning, date parsing
│   ├── hotspot_analysis.py    # DBSCAN clustering + summaries
│   └── build_map.py           # Folium heatmap + hotspot marker maps
├── app.py                      # Streamlit dashboard
└── notebooks/
    └── exploration.ipynb       # exploratory analysis / parameter tuning
```

## Tech stack

Python, pandas, scikit-learn (DBSCAN), Folium, Streamlit

## Results / Validation

On the bundled synthetic sample, the default parameters
(`eps_km=0.15`, `min_samples=8`) correctly recover all 5 built-in
hotspot clusters and correctly label scattered background points as
noise — see `notebooks/exploration.ipynb`.

## License

MIT
