import requests
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_pipeline" / "data" / "toronto_food_osm.geojson"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Toronto bbox (south, west, north, east)
TORONTO_BBOX = (43.55, -79.65, 43.86, -79.10)

QUERY = f"""
[out:json][timeout:90];
(
  node["shop"="supermarket"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  node["shop"="convenience"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  node["amenity"="marketplace"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
);
out body;
"""

def main():
    print("Fetching food locations from OSM Overpass…")
    r = requests.post(OVERPASS_URL, data={"data": QUERY})
    r.raise_for_status()
    data = r.json()

    feats = []
    for el in data.get("elements", []):
        if el.get("type") != "node":
            continue
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            continue
        tags = el.get("tags", {})
        feats.append({
            "name": tags.get("name", ""),
            "category": tags.get("shop") or tags.get("amenity") or "",
            "osm_id": el.get("id"),
            "geometry": Point(lon, lat),
        })

    gdf = gpd.GeoDataFrame(feats, geometry="geometry", crs="EPSG:4326")

    # Deduplicate by coordinates
    if len(gdf) > 0:
        gdf["lon"] = gdf.geometry.x.round(6)
        gdf["lat"] = gdf.geometry.y.round(6)
        gdf = gdf.drop_duplicates(subset=["lon", "lat"]).drop(columns=["lon", "lat"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUT, driver="GeoJSON")

    print("✅ Saved:", OUT)
    print("Food points:", len(gdf))
    print('Attribution to include: "© OpenStreetMap contributors"')

if __name__ == "__main__":
    main()
