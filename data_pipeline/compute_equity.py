# data_pipeline/compute_equity.py
# Merge transit + food scores into a single Equity GeoJSON for the web app.

from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]

TRANSIT = ROOT / "web" / "public" / "neighbourhood_transit_scores.geojson"
FOOD = ROOT / "web" / "public" / "neighbourhood_food_scores.geojson"

OUT_DIR = ROOT / "data_pipeline" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_GEOJSON = OUT_DIR / "neighbourhood_equity_scores.geojson"
OUT_WEB_COPY = ROOT / "web" / "public" / "neighbourhood_equity_scores.geojson"


def norm_name(x: str) -> str:
    if x is None:
        return ""
    return " ".join(str(x).strip().lower().split())


def main():
    if not TRANSIT.exists():
        raise FileNotFoundError(f"Missing: {TRANSIT}")
    if not FOOD.exists():
        raise FileNotFoundError(f"Missing: {FOOD}")

    t = gpd.read_file(TRANSIT)
    f = gpd.read_file(FOOD)

    # Ensure same CRS
    if t.crs is None:
        t = t.set_crs(epsg=4326)
    else:
        t = t.to_crs(epsg=4326)

    if f.crs is None:
        f = f.set_crs(epsg=4326)
    else:
        f = f.to_crs(epsg=4326)

    # Build merge keys
    t["k"] = t["neighbourhood_name"].map(norm_name)
    f["k"] = f["neighbourhood_name"].map(norm_name)

    # Keep only needed columns from food (avoid geometry duplication)
    f2 = f[["k", "food_score", "food_dist_m"]].copy()

    out = t.merge(f2, on="k", how="left")

    # If any food values missing, set to NaN-safe defaults
    out["food_score"] = pd.to_numeric(out["food_score"], errors="coerce")
    out["transit_score"] = pd.to_numeric(out["transit_score"], errors="coerce")
    out["food_dist_m"] = pd.to_numeric(out["food_dist_m"], errors="coerce")
    out["transit_dist_m"] = pd.to_numeric(out["transit_dist_m"], errors="coerce")

    # Equity weights (simple + defendable)
    w_transit = 0.5
    w_food = 0.5

    out["equity_score"] = (w_transit * out["transit_score"] + w_food * out["food_score"]).round(1)

    # Primary limiting factor (for sidebar storytelling)
    def limiting(row):
        ts = row.get("transit_score")
        fs = row.get("food_score")
        if pd.isna(ts) and pd.isna(fs):
            return "Unknown"
        if pd.isna(ts):
            return "Transit"
        if pd.isna(fs):
            return "Food"
        return "Transit" if ts < fs else "Food"

    out["limiting_factor"] = out.apply(limiting, axis=1)

    # Cleanup
    out = out.drop(columns=["k"])

    out.to_file(OUT_GEOJSON, driver="GeoJSON")
    out.to_file(OUT_WEB_COPY, driver="GeoJSON")

    print("✅ Saved:", OUT_GEOJSON)
    print("✅ Copied for web:", OUT_WEB_COPY)
    print("Note: Add attribution:")
    print(' - Contains information licensed under the Open Government Licence - Toronto')
    print(' - © OpenStreetMap contributors')


if __name__ == "__main__":
    main()
