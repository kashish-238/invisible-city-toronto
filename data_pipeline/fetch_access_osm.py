# data_pipeline/fetch_access_osm.py
# Pull essential services for Toronto from OSM Overpass (free)
# Outputs: data_pipeline/data/toronto_access_osm.geojson

from pathlib import Path
import requests
import geopandas as gpd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_pipeline" / "data" / "toronto_access_osm.geojson"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Toronto bbox (south, west, north, east)
TORONTO_BBOX = (43.55, -79.65, 43.86, -79.10)

# We include nodes + ways + relations; ways/relations will come back with a "center"
QUERY = f"""
[out:json][timeout:120];
(
  node["amenity"="hospital"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  way["amenity"="hospital"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  relation["amenity"="hospital"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});

  node["amenity"="clinic"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  way["amenity"="clinic"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  relation["amenity"="clinic"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});

  node["amenity"="doctors"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  way["amenity"="doctors"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  relation["amenity"="doctors"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});

  node["amenity"="community_centre"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  way["amenity"="community_centre"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  relation["amenity"="community_centre"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
);
out center;
"""

def main():
  print("Fetching essential services (health + community) from OSM Overpass…")
  r = requests.post(OVERPASS_URL, data={"data": QUERY})
  r.raise_for_status()
  data = r.json()

  rows = []
  for el in data.get("elements", []):
    tags = el.get("tags", {}) or {}
    name = tags.get("name", "")
    amenity = tags.get("amenity", "")

    # Coordinates: nodes have lat/lon; ways/relations have center
    if el.get("type") == "node":
      lat = el.get("lat")
      lon = el.get("lon")
    else:
      center = el.get("center") or {}
      lat = center.get("lat")
      lon = center.get("lon")

    if lat is None or lon is None:
      continue

    rows.append({
      "osm_type": el.get("type"),
      "osm_id": el.get("id"),
      "category": amenity,
      "name": name,
      "geometry": Point(lon, lat),
    })

  gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")

  # Deduplicate by coordinate
  if len(gdf) > 0:
    gdf["lon"] = gdf.geometry.x.round(6)
    gdf["lat"] = gdf.geometry.y.round(6)
    gdf = gdf.drop_duplicates(subset=["lon", "lat"]).drop(columns=["lon", "lat"])

  OUT.parent.mkdir(parents=True, exist_ok=True)
  gdf.to_file(OUT, driver="GeoJSON")

  print("✅ Saved:", OUT)
  print("Essential service points:", len(gdf))
  print('Attribution to include: "© OpenStreetMap contributors"')

if __name__ == "__main__":
  main()
