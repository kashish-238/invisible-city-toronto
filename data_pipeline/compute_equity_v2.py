# data_pipeline/compute_equity_v2.py
# Merge transit + food + access into equity_score_v2

from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]

TRANSIT = ROOT / "web" / "public" / "neighbourhood_transit_scores.geojson"
FOOD = ROOT / "web" / "public" / "neighbourhood_food_scores.geojson"
ACCESS = ROOT / "web" / "public" / "neighbourhood_access_scores.geojson"

OUT_DIR = ROOT / "data_pipeline" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_GEOJSON = OUT_DIR / "neighbourhood_equity_v2_scores.geojson"
OUT_WEB_COPY = ROOT / "web" / "public" / "neighbourhood_equity_v2_scores.geojson"


def norm_name(x: str) -> str:
  if x is None:
    return ""
  return " ".join(str(x).strip().lower().split())


def main():
  for p in [TRANSIT, FOOD, ACCESS]:
    if not p.exists():
      raise FileNotFoundError(f"Missing: {p}")

  t = gpd.read_file(TRANSIT).to_crs(epsg=4326)
  f = gpd.read_file(FOOD).to_crs(epsg=4326)
  a = gpd.read_file(ACCESS).to_crs(epsg=4326)

  t["k"] = t["neighbourhood_name"].map(norm_name)
  f["k"] = f["neighbourhood_name"].map(norm_name)
  a["k"] = a["neighbourhood_name"].map(norm_name)

  out = t.merge(f[["k", "food_score", "food_dist_m"]], on="k", how="left")
  out = out.merge(a[["k", "access_score", "access_dist_m"]], on="k", how="left")

  # numeric
  for c in ["transit_score", "food_score", "access_score", "transit_dist_m", "food_dist_m", "access_dist_m"]:
    out[c] = pd.to_numeric(out[c], errors="coerce")

  # weights (equal by default)
  w_t, w_f, w_a = 1/3, 1/3, 1/3
  out["equity_score_v2"] = (w_t*out["transit_score"] + w_f*out["food_score"] + w_a*out["access_score"]).round(1)

  def limiting(row):
    vals = {
      "Transit": row.get("transit_score"),
      "Food": row.get("food_score"),
      "Access": row.get("access_score"),
    }
    vals = {k: v for k, v in vals.items() if pd.notna(v)}
    if not vals:
      return "Unknown"
    return min(vals, key=vals.get)

  out["limiting_factor_v2"] = out.apply(limiting, axis=1)
  out = out.drop(columns=["k"])

  out.to_file(OUT_GEOJSON, driver="GeoJSON")
  out.to_file(OUT_WEB_COPY, driver="GeoJSON")

  print("✅ Saved:", OUT_GEOJSON)
  print("✅ Copied for web:", OUT_WEB_COPY)

if __name__ == "__main__":
  main()
