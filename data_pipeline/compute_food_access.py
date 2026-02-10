# data_pipeline/compute_food_access.py
# Food Access (Toronto) = nearest distance to food points (OSM: supermarkets/convenience/marketplace)
# Outputs: web/public/neighbourhood_food_scores.geojson

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]

NBH_GEOJSON = ROOT / "web" / "public" / "toronto_neighbourhoods.geojson"
FOOD_POINTS = ROOT / "data_pipeline" / "data" / "toronto_food_osm.geojson"

OUT_DIR = ROOT / "data_pipeline" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_GEOJSON = OUT_DIR / "neighbourhood_food_scores.geojson"
OUT_WEB_COPY = ROOT / "web" / "public" / "neighbourhood_food_scores.geojson"


def pick_name_col(gdf: gpd.GeoDataFrame) -> str:
    for c in ["neighbourhood_name", "AREA_NAME", "NAME", "Neighbourhood", "NEIGH_NAME", "NEIGHBOURHOOD_NAME"]:
        if c in gdf.columns:
            return c
    non_geom = [c for c in gdf.columns if c != "geometry"]
    return non_geom[0] if non_geom else "geometry"


def distance_to_score(dist_m: np.ndarray) -> np.ndarray:
    """
    Interpretable scoring:
      0m -> 100
      1500m+ -> 0  (roughly 15–20 min walk; policy-friendly)
    """
    max_dist = 1500.0
    scaled = np.clip(dist_m / max_dist, 0, 1)
    return np.round((1.0 - scaled) * 100.0, 1)


def main():
    if not NBH_GEOJSON.exists():
        raise FileNotFoundError(f"Missing neighbourhood GeoJSON: {NBH_GEOJSON}")
    if not FOOD_POINTS.exists():
        raise FileNotFoundError(f"Missing food points GeoJSON: {FOOD_POINTS} (run fetch_food_osm.py first)")

    # 1) Neighbourhoods
    nbh = gpd.read_file(NBH_GEOJSON)
    if nbh.crs is None:
        nbh = nbh.set_crs(epsg=4326)
    else:
        nbh = nbh.to_crs(epsg=4326)

    name_col = pick_name_col(nbh)

    # Representative points inside polygons
    nbh_points = gpd.GeoDataFrame(
        nbh[[name_col]].copy(),
        geometry=nbh.geometry.representative_point(),
        crs="EPSG:4326",
    )

    # 2) Food points
    food = gpd.read_file(FOOD_POINTS).to_crs(epsg=4326)
    food = food[food.geometry.geom_type == "Point"].copy()
    if len(food) == 0:
        raise ValueError("Food points GeoJSON has 0 point features.")

    # Deduplicate food by coordinate (defensive)
    food["lon"] = food.geometry.x.round(6)
    food["lat"] = food.geometry.y.round(6)
    food = food.drop_duplicates(subset=["lon", "lat"]).drop(columns=["lon", "lat"])

    # 3) Project to meters (Toronto)
    nbh_m = nbh.to_crs(epsg=26917)
    nbh_points_m = nbh_points.to_crs(epsg=26917)
    food_m = food.to_crs(epsg=26917)

    # 4) Nearest food distance (STRtree; Shapely 2 safe + order-safe)
    food_geoms = list(food_m.geometry.values)
    tree = STRtree(food_geoms)

    (idx_left, _idx_right), dist = tree.query_nearest(
        nbh_points_m.geometry.values,
        return_distance=True
    )

    dists = np.empty(len(nbh_points_m), dtype=float)
    dists[idx_left] = np.array(dist, dtype=float)

    # 5) Output
    out = nbh_m.copy()
    out["neighbourhood_name"] = nbh[name_col].astype(str).values
    out["food_dist_m"] = np.round(dists, 1)
    out["food_score"] = distance_to_score(dists)

    out = out.to_crs(epsg=4326)

    out.to_file(OUT_GEOJSON, driver="GeoJSON")
    out.to_file(OUT_WEB_COPY, driver="GeoJSON")

    print("✅ Saved:", OUT_GEOJSON)
    print("✅ Copied for web:", OUT_WEB_COPY)
    print("Food points used:", len(food))
    print('Attribution to include: "© OpenStreetMap contributors"')

if __name__ == "__main__":
    main()
