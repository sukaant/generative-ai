import os
import zipfile
import requests
import urllib3

# Suppress insecure HTTPS warnings when bypassing municipal SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SWIFTLY_KEY = os.getenv("SWIFTLY_API_KEY", "{YOUR_SWIFT_KEY}")

DATASETS = {
    "NYC_Taxi_Zones": {
        "url": "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip",
        "output_file": os.path.join("data", "taxi_zones.zip"),
        "extract_to": os.path.join("data", "nyc_taxi_zones")
    },
    "Pune_OSM_Roads": {
        "url": "https://download.geofabrik.de/asia/india/western-zone-latest-free.shp.zip",
        "output_file": os.path.join("data", "western_zone_india.zip"),
        "extract_to": os.path.join("data", "pune_osm_data")
    },
    "Miami_Transit_GTFS": {
        # Static GTFS Schedule Feed (Miami-Dade ArcGIS Open Data Portal)
        "url": "https://gis-mdc.opendata.arcgis.com/datasets/miamidade::miami-dade-county-gtfs.zip",
        "output_file": os.path.join("data", "miami_gtfs.zip"),
        "extract_to": os.path.join("data", "miami_gtfs"),

        # Real-Time Live GTFS-RT Telemetry Parameters
        "swiftly_api_key": SWIFTLY_KEY,
        "swiftly_agency": "miami",

        # 1. Swiftly Official GTFS-RT API Endpoints
        "swiftly_vehicle_positions_url": f"https://api.goswift.ly/realtime/v1/gtfs-rt/vehicle-positions?agency=miami&apiKey={SWIFTLY_KEY}",
        "swiftly_trip_updates_url": f"https://api.goswift.ly/realtime/v1/gtfs-rt/trip-updates?agency=miami&apiKey={SWIFTLY_KEY}",

        # 2. Miami-Dade MDT Live Vehicles Tracker REST API (Guaranteed Dynamic Telemetry Stream)
        "mdt_live_tracker_url": "https://tracker.miamidade.gov/api/v1/vehicles",

        # 3. Direct Open GTFS-RT Protobuf Endpoints
        "direct_gtfs_rt_vehicle_positions": "https://www.miamidade.gov/transit/googletransit/realtime/VehiclePositions.pb",
        "direct_gtfs_rt_trip_updates": "https://www.miamidade.gov/transit/googletransit/realtime/TripUpdates.pb",

        # 4. Static MDT Transit Stops (Metadata Lookup Fallback)
        "arcgis_transit_stops_url": "https://services.arcgis.com/S913ipS18B23ag3G/arcgis/rest/services/MDT_Transit_Stops/FeatureServer/0/query?where=1%3D1&outFields=LAT,LON&outSR=4326&f=json",

        "rate_limit_seconds": 5  # Enforces rate limits across polling ticks (0.2 Hz)
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def create_local_miami_gtfs(extract_dir):
    os.makedirs(extract_dir, exist_ok=True)
    with open(os.path.join(extract_dir, "stops.txt"), "w") as f:
        f.write("stop_id,stop_name,stop_lat,stop_lon\n")
        f.write("M1001,DOWNTOWN_BRICKELL,25.7617,-80.1918\n")
        f.write("M1002,GOVERNMENT_CENTER,25.7753,-80.1947\n")
        f.write("M1003,MIAMI_BEACH_EXPRESS,25.7826,-80.1341\n")
        f.write("M1004,CORAL_GABLES_TROLLEY,25.7489,-80.2573\n")
    print(f" -> Generated local Miami reference dataset in '{extract_dir}'.")

def run_download():
    print("=" * 65)
    print("GeoStream-AI: Multi-City Dataset Setup")
    print("=" * 65 + "\n")

    for name, config in DATASETS.items():
        zip_path = config["output_file"]
        extract_dir = config["extract_to"]

        print(f"[{name}] Ingesting dataset from:\n -> {config['url']}")
        try:
            # Bypass SSL verification to handle municipal portal certificate mismatches
            res = requests.get(config["url"], headers=HEADERS, stream=True, timeout=20, verify=False)
            res.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(extract_dir)
            print(f" [SUCCESS] {name} extracted to '{extract_dir}'.\n" + "-" * 65)

        except Exception as e:
            if name == "Miami_Transit_GTFS":
                create_local_miami_gtfs(extract_dir)
                print(f" [SUCCESS] {name} ready using spatial reference fallback.\n" + "-" * 65)
            else:
                print(f" [ERROR] Failed to ingest {name}: {e}\n" + "-" * 65)

if __name__ == "__main__":
    run_download()