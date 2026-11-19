import os
import glob
import zipfile
import requests
import geopandas as gpd

# Geofabrik Western Zone India shapefile URL
url = "https://download.geofabrik.de/asia/india/western-zone-latest-free.shp.zip"
zip_path = "/data/western_zone_india.zip"
extract_dir = "/data/pune_osm_data"

# Step 1: Download Geofabrik Western Zone Zip
if not os.path.exists(zip_path):
    print("Downloading Geofabrik Western Zone India OSM shapefiles...")
    response = requests.get(url, stream=True)
    with open(zip_path, "/data/wb") as f:
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    print("Download complete.")

# Step 2: Extract Zip Archive
if not os.path.exists(extract_dir):
    print("Extracting shapefile archive...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

# Step 3: Find the roads shapefile dynamically
print("Locating roads shapefile...")
roads_files = glob.glob(os.path.join(extract_dir, "**", "*roads*.shp"), recursive=True)

if not roads_files:
    raise FileNotFoundError("Could not find any roads shapefile inside extracted directory.")

roads_shp = roads_files[0]
print(f"Loading roads shapefile: {roads_shp}")

# Step 4: Load GIS layer into GeoPandas
roads_gdf = gpd.read_file(roads_shp)

# Step 5: Crop/Clip to Pune Bounding Box (Min Lon, Min Lat, Max Lon, Max Lat)
# Bounding box covers core Pune (Hinjawadi, Kothrud, Shivajinagar, Swargate, Viman Nagar)
pune_bbox = (73.70, 18.40, 73.98, 18.65)
print("Clipping road network to Pune Metropolitan Region...")
pune_roads = roads_gdf.cx[pune_bbox[0]:pune_bbox[2], pune_bbox[1]:pune_bbox[3]]

# Step 6: Reproject to WGS84 Lat/Long (EPSG:4326)
pune_roads = pune_roads.to_crs(epsg=4326)

print(f"Pune Road Segments Filtered: {len(pune_roads):,}")

# Step 7: Export to GeoJSON
output_file = "/data/pune_road_network.geojson"
pune_roads.to_file(output_file, driver="GeoJSON")
print(f"Successfully saved Pune road dataset to '{output_file}'!")