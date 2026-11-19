import time
from pathlib import Path
import h3
import numpy as np
import pandas as pd

# Total records to generate for high-throughput benchmark
TARGET_RECORDS = 500_000

print("Generating 500,000 NYC Taxi Spatiotemporal Trip Records...")

# Anchor paths to the script's directory
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

csv_path = DATA_DIR / "nyc_taxi_zones_h3.csv"
zip_path = DATA_DIR / "nyc_taxi_zones_h3.csv.zip"

# Step 1: Load (or auto-generate) the H3 Zone Lookup Table
if csv_path.exists():
    df_zones = pd.read_csv(csv_path)
elif zip_path.exists():
    df_zones = pd.read_csv(zip_path)
else:
    print(f"[INFO] '{csv_path.name}' not found. Generating default NYC zone lookup table...")
    np.random.seed(42)
    n_default_zones = 263
    boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    lats = np.random.uniform(40.5500, 40.9000, size=n_default_zones)
    lons = np.random.uniform(-74.2000, -73.7500, size=n_default_zones)

    df_zones = pd.DataFrame({
        "LocationID": np.arange(1, n_default_zones + 1),
        "zone": [f"NYC Zone {i}" for i in range(1, n_default_zones + 1)],
        "borough": np.random.choice(boroughs, size=n_default_zones),
        "latitude": np.round(lats, 6),
        "longitude": np.round(lons, 6),
        "h3_index": [h3.latlng_to_cell(lat, lon, 8) for lat, lon in zip(lats, lons)],
    })
    df_zones.to_csv(csv_path, index=False)
    print(f"[INFO] Saved lookup table to '{csv_path}'.")

num_zones = len(df_zones)

# Step 2: Randomly sample 500k trip locations across NYC zones
np.random.seed(42)
zone_indices = np.random.randint(0, num_zones, size=TARGET_RECORDS)
sampled_zones = df_zones.iloc[zone_indices].copy()

# Step 3: Add synthetic timestamps and jitter
base_timestamp = int(time.time()) - (86400 * 30)  # 30 days ago
timestamps = base_timestamp + np.random.randint(0, 86400 * 30, size=TARGET_RECORDS)

# Small GPS jitter to simulate multi-vehicle positions within zones
lat_jitter = np.random.uniform(-0.002, 0.002, size=TARGET_RECORDS)
lon_jitter = np.random.uniform(-0.002, 0.002, size=TARGET_RECORDS)

large_nyc_df = pd.DataFrame({
    "trip_id": np.arange(1000000, 1000000 + TARGET_RECORDS),
    "LocationID": sampled_zones["LocationID"].values,
    "zone": sampled_zones["zone"].values,
    "borough": sampled_zones["borough"].values,
    "latitude": np.round(sampled_zones["latitude"].values + lat_jitter, 6),
    "longitude": np.round(sampled_zones["longitude"].values + lon_jitter, 6),
    "h3_index": sampled_zones["h3_index"].values,
    "timestamp": timestamps,
})

print("\n[SUCCESS] Scaled NYC Spatiotemporal Dataset:")
print(
    large_nyc_df[
        ["trip_id", "LocationID", "zone", "latitude", "longitude", "h3_index", "timestamp"]
    ].head(10)
)

# Step 4: Export to CSV inside the script directory
output_csv = DATA_DIR / "nyc_trips_h3_large.csv"
large_nyc_df.to_csv(output_csv, index=False)
print(f"\nSuccessfully saved {len(large_nyc_df):,} records to '{output_csv}'")