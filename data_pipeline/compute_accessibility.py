# data_pipeline/compute_accessibility.py
# Accessibility (Toronto) = nearest distance to essential services (OSM)
# Outputs: web/public/neighbourhood_access_scores.geojson

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]

NBH_GEOJSON = ROOT / "web" / "public" / "toronto_neighbourhoods.geojson"
ACCESS_POINTS = ROOT / "data_pipeline" / "data" / "toronto_access_osm.geojson"

OUT_DIR = ROOT / "data_pipeline" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_GEOJSON = OUT_DIR / "neighbourhood_access_scores.geojson"
OUT_WEB_COPY = ROOT / "web" / "public" / "neighbourhood_access_scores.geojson"


def pick_name_col(gdf: gpd.GeoDataFrame) -> str:
  for c in ["neighbourhood_name", "AREA_NAME", "NAME", "Neighbourhood", "NEIGH_NAME", "NEIGHBOURHOOD_NAME"]:
    if c in gdf.columns:
      return c
  non_geom = [c for c in gdf.columns if c != "geometry"]
  return non_geom[0] if non_geom else "geometry"


def distance_to_score(dist_m: np.ndarray) -> np.ndarray:
  """
  0m -> 100
  2000m+ -> 0   (about 25 min walk; policy-friendly)
  """
  max_dist = 2000.0
  scaled = np.clip(dist_m / max_dist, 0, 1)
  return np.round((1.0 - scaled) * 100.0, 1)


def main():
  if not NBH_GEOJSON.exists():
    raise FileNotFoundError(f"Missing: {NBH_GEOJSON}")
  if not ACCESS_POINTS.exists():
    raise FileNotFoundError(f"Missing: {ACCESS_POINTS} (run fetch_access_osm.py)")

  nbh = gpd.read_file(NBH_GEOJSON)
  nbh = nbh.set_crs(epsg=4326) if nbh.crs is None else nbh.to_crs(epsg=4326)
  name_col = pick_name_col(nbh)

  nbh_points = gpd.GeoDataFrame(
    nbh[[name_col]].copy(),
    geometry=nbh.geometry.representative_point(),
    crs="EPSG:4326",
  )

  access = gpd.read_file(ACCESS_POINTS).to_crs(epsg=4326)
  access = access[access.geometry.geom_type.isin(["Point"])].copy()

  # Deduplicate by coordinate
  access["lon"] = access.geometry.x.round(6)
  access["lat"] = access.geometry.y.round(6)
  access = access.drop_duplicates(subset=["lon", "lat"]).drop(columns=["lon", "lat"])

  if len(access) == 0:
    raise ValueError("No access points found in toronto_access_osm.geojson")

  # Project to meters (Toronto)
  nbh_m = nbh.to_crs(epsg=26917)
  nbh_points_m = nbh_points.to_crs(epsg=26917)
  access_m = access.to_crs(epsg=26917)

  geoms = list(access_m.geometry.values)
  tree = STRtree(geoms)

  (idx_left, _idx_right), dist = tree.query_nearest(
    nbh_points_m.geometry.values,
    return_distance=True
  )

  dists = np.empty(len(nbh_points_m), dtype=float)
  dists[idx_left] = np.array(dist, dtype=float)

  out = nbh_m.copy()
  out["neighbourhood_name"] = nbh[name_col].astype(str).values
  out["access_dist_m"] = np.round(dists, 1)
  out["access_score"] = distance_to_score(dists)

  out = out.to_crs(epsg=4326)

  out.to_file(OUT_GEOJSON, driver="GeoJSON")
  out.to_file(OUT_WEB_COPY, driver="GeoJSON")

  print("✅ Saved:", OUT_GEOJSON)
  print("✅ Copied for web:", OUT_WEB_COPY)
  print("Access points used:", len(access))
  print('Attribution: "© OpenStreetMap contributors"')

if __name__ == "__main__":
  main()
