import zipfile
import pandas as pd
from pathlib import Path

ZIP_PATH = Path("data_pipeline/data/ttc_gtfs.zip")

def main():
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        names = set(z.namelist())

        required = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
        print("=== Files present ===")
        for f in required:
            print(f"{f}: {'YES' if f in names else 'NO'}")

        # stops
        with z.open("stops.txt") as f:
            stops = pd.read_csv(f, usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"])
        print("\nStops:", len(stops))

        # routes: check route_type codes (subway is usually 1)
        if "routes.txt" in names:
            with z.open("routes.txt") as f:
                routes = pd.read_csv(f)
            if "route_type" in routes.columns:
                print("\nRoute types present (counts):")
                print(routes["route_type"].value_counts().sort_index())
                print("\nNote: GTFS route_type commonly uses 1=subway/metro, 3=bus, 0=tram/streetcar.")
            else:
                print("\nroutes.txt has no route_type column (unusual).")

        # Optional: prove route_type=1 actually has trips + stop_times (subway service exists)
        if all(x in names for x in ["routes.txt", "trips.txt", "stop_times.txt"]):
            with z.open("trips.txt") as f:
                trips = pd.read_csv(f, usecols=["trip_id", "route_id"])
            with z.open("stop_times.txt") as f:
                st = pd.read_csv(f, usecols=["trip_id", "stop_id"])

            subway_route_ids = set()
            if "route_type" in routes.columns:
                subway_route_ids = set(routes.loc[routes["route_type"] == 1, "route_id"].astype(str))

            if subway_route_ids:
                subway_trips = trips[trips["route_id"].astype(str).isin(subway_route_ids)]
                subway_stop_times = st[st["trip_id"].isin(subway_trips["trip_id"])]
                subway_stops = stops[stops["stop_id"].isin(subway_stop_times["stop_id"])]

                print("\n=== Subway proof ===")
                print("Subway routes:", len(subway_route_ids))
                print("Subway trips:", len(subway_trips))
                print("Subway stop_time rows:", len(subway_stop_times))
                print("Unique subway stops used in service:", subway_stops['stop_id'].nunique())

            else:
                print("\nNo route_type=1 routes found (may be surface-only feed).")

if __name__ == "__main__":
    main()
