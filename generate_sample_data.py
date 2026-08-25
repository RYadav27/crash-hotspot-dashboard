"""
One-off script to generate a realistic SAMPLE crash dataset so the
dashboard works out-of-the-box without needing to download the full
real dataset first. Schema mirrors NYC Open Data's
"Motor Vehicle Collisions - Crashes" dataset.

This is SYNTHETIC data for demo/testing purposes only, not real
crash records. Swap in the real dataset via download_data.py for
production use.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# Define a few "hotspot" centers (realistic NYC-area coordinates) plus
# background noise scattered around Manhattan, so DBSCAN has real
# clusters to find.
hotspots = [
    {"name": "Times Square area",      "lat": 40.7580, "lon": -73.9855, "n": 180, "spread": 0.003},
    {"name": "Union Square area",      "lat": 40.7359, "lon": -73.9911, "n": 140, "spread": 0.0025},
    {"name": "Downtown Brooklyn",      "lat": 40.6928, "lon": -73.9903, "n": 120, "spread": 0.003},
    {"name": "Flushing, Queens",       "lat": 40.7654, "lon": -73.8318, "n": 100, "spread": 0.003},
    {"name": "Fordham Rd, The Bronx",  "lat": 40.8610, "lon": -73.8977, "n": 90,  "spread": 0.003},
]

boroughs_by_hotspot = ["MANHATTAN", "MANHATTAN", "BROOKLYN", "QUEENS", "BRONX"]

contributing_factors = [
    "Driver Inattention/Distraction", "Failure to Yield Right-of-Way",
    "Following Too Closely", "Backing Unsafely", "Unsafe Speed",
    "Traffic Control Disregarded", "Turning Improperly", "Unspecified",
    "Alcohol Involvement", "Pavement Slippery",
]

vehicle_types = ["Sedan", "SUV", "Taxi", "Bus", "Bike", "Pick-up Truck", "Box Truck"]

rows = []
crash_id = 100000

start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
date_range_days = (end_date - start_date).days

for hotspot, borough in zip(hotspots, boroughs_by_hotspot):
    for _ in range(hotspot["n"]):
        lat = hotspot["lat"] + np.random.normal(0, hotspot["spread"])
        lon = hotspot["lon"] + np.random.normal(0, hotspot["spread"])
        crash_date = start_date + timedelta(days=int(np.random.uniform(0, date_range_days)))
        hour_weights = np.array([1,1,1,1,1,2,4,6,7,5,4,4,5,5,5,6,7,8,7,5,4,3,2,1], dtype=float)
        hour_probs = hour_weights / hour_weights.sum()
        crash_hour = np.random.choice(range(24), p=hour_probs)
        crash_time = f"{crash_hour:02d}:{np.random.randint(0,60):02d}"
        persons_injured = np.random.choice([0,1,2,3], p=[0.55,0.30,0.10,0.05])
        persons_killed = np.random.choice([0,1], p=[0.995,0.005])

        rows.append({
            "CRASH_ID": crash_id,
            "CRASH_DATE": crash_date.strftime("%m/%d/%Y"),
            "CRASH_TIME": crash_time,
            "BOROUGH": borough,
            "LATITUDE": round(lat, 6),
            "LONGITUDE": round(lon, 6),
            "ON_STREET_NAME": hotspot["name"],
            "NUMBER_OF_PERSONS_INJURED": persons_injured,
            "NUMBER_OF_PERSONS_KILLED": persons_killed,
            "CONTRIBUTING_FACTOR_VEHICLE_1": np.random.choice(contributing_factors),
            "VEHICLE_TYPE_CODE_1": np.random.choice(vehicle_types),
        })
        crash_id += 1

# Add background "noise" crashes scattered around the wider NYC area
# (not part of any hotspot) so DBSCAN correctly labels them as noise (-1)
n_noise = 300
for _ in range(n_noise):
    lat = 40.70 + np.random.uniform(-0.15, 0.15)
    lon = -73.95 + np.random.uniform(-0.20, 0.20)
    crash_date = start_date + timedelta(days=int(np.random.uniform(0, date_range_days)))
    crash_hour = np.random.randint(0, 24)
    crash_time = f"{crash_hour:02d}:{np.random.randint(0,60):02d}"
    persons_injured = np.random.choice([0,1,2,3], p=[0.65,0.25,0.07,0.03])
    persons_killed = np.random.choice([0,1], p=[0.997,0.003])

    rows.append({
        "CRASH_ID": crash_id,
        "CRASH_DATE": crash_date.strftime("%m/%d/%Y"),
        "CRASH_TIME": crash_time,
        "BOROUGH": np.random.choice(["MANHATTAN","BROOKLYN","QUEENS","BRONX","STATEN ISLAND"]),
        "LATITUDE": round(lat, 6),
        "LONGITUDE": round(lon, 6),
        "ON_STREET_NAME": "Unnamed Street",
        "NUMBER_OF_PERSONS_INJURED": persons_injured,
        "NUMBER_OF_PERSONS_KILLED": persons_killed,
        "CONTRIBUTING_FACTOR_VEHICLE_1": np.random.choice(contributing_factors),
        "VEHICLE_TYPE_CODE_1": np.random.choice(vehicle_types),
    })
    crash_id += 1

df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
df.to_csv("data/raw/sample_crashes.csv", index=False)
print(f"Generated {len(df)} sample crash records -> data/raw/sample_crashes.csv")
