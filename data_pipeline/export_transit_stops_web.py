# data_pipeline/export_transit_stops_web.py
# Export surface GTFS stops + OSM subway points to web/public/transit_stops.geojson

import zipfile
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
GTFS = ROOT / "data_pipeline" / "data" / "ttc_gtfs.zip"
SUBWAY = ROOT / "data_pipeline" / "data" / "ttc_subway_osm.geojson"
OUT = ROOT / "web" / "public" / "transit_stops.geojson"

def main():
  if not GTFS.exists():
    raise FileNotFoundError(GTFS)
  if not SUBWAY.exists():
    raise FileNotFoundError(SUBWAY)

  with zipfile.ZipFile(GTFS, "r") as z:
    with z.open("stops.txt") as f:
      df = pd.read_csv(f)

  df = df.dropna(subset=["stop_lat", "stop_lon"])
  df = df.drop_duplicates(subset=["stop_lat", "stop_lon"])

  surface_geom = [Point(xy) for xy in zip(df["stop_lon"], df["stop_lat"])]
  surface = gpd.GeoDataFrame({"source": ["surface"]*len(df)}, geometry=surface_geom, crs="EPSG:4326")[["source","geometry"]]

  subway = gpd.read_file(SUBWAY).to_crs(epsg=4326)
  subway = subway[subway.geometry.geom_type == "Point"].copy()
  subway["source"] = "subway"
  subway = subway[["source","geometry"]]

  allp = pd.concat([surface, subway], ignore_index=True)
  allg = gpd.GeoDataFrame(allp, geometry="geometry", crs="EPSG:4326")

  # dedupe by coordinates
  allg["lon"] = allg.geometry.x.round(6)
  allg["lat"] = allg.geometry.y.round(6)
  allg = allg.drop_duplicates(subset=["lon","lat"]).drop(columns=["lon","lat"])

  OUT.parent.mkdir(parents=True, exist_ok=True)
  allg.to_file(OUT, driver="GeoJSON")
  print("✅ Exported stops:", OUT)
  print("Count:", len(allg))

if __name__ == "__main__":
  main()
