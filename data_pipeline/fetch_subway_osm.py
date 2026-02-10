import json
from pathlib import Path
import requests
import geopandas as gpd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_pipeline" / "data" / "ttc_subway_osm.geojson"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Toronto bbox (south, west, north, east) — covers city + a bit around
TORONTO_BBOX = (43.55, -79.65, 43.86, -79.10)

QUERY = f"""
[out:json][timeout:60];
(
  node["railway"="station"]["station"="subway"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  node["public_transport"="station"]["station"="subway"]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
  node["railway"="station"]["network"~"TTC|Toronto Transit Commission",i]({TORONTO_BBOX[0]},{TORONTO_BBOX[1]},{TORONTO_BBOX[2]},{TORONTO_BBOX[3]});
);
out body;
"""

def main():
    print("Fetching subway stations from OSM Overpass…")
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
        name = tags.get("name", "")
        feats.append({
            "name": name,
            "osm_id": el.get("id"),
            "geometry": Point(lon, lat)
        })

    gdf = gpd.GeoDataFrame(feats, geometry="geometry", crs="EPSG:4326")

    # remove duplicates (same coordinates)
    if len(gdf) > 0:
        gdf["lon"] = gdf.geometry.x.round(6)
        gdf["lat"] = gdf.geometry.y.round(6)
        gdf = gdf.drop_duplicates(subset=["lon", "lat"]).drop(columns=["lon", "lat"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUT, driver="GeoJSON")

    print("✅ Saved:", OUT)
    print("Stations:", len(gdf))
    print('Attribution to include: "© OpenStreetMap contributors"')

if __name__ == "__main__":
    main()
