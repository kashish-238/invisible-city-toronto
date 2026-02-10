\# Invisible City: Toronto 🌍

\*\*Built by Sahil Patel\*\*  

An interactive urban equity map for Toronto that reveals “invisible” access gaps across neighbourhoods.



🔗 \*\*Live Demo:\*\* https://YOUR-VERCEL-URL.vercel.app  

📦 \*\*Repo:\*\* https://github.com/kashish-238/invisible-city-toronto



---



\## What this project does

Invisible City: Toronto visualizes neighbourhood-level access using a clean, professor-friendly storytelling UI.



\### Current Layers (MVP+)

\- \*\*Transit Access (TTC)\*\* — distance to nearest TTC stop → `transit\_score (0–100)`

\- \*\*Food Access (OSM)\*\* — distance to nearest grocery/food location → `food\_score (0–100)`

\- \*\*Essential Services (OSM)\*\* — distance to clinics/hospitals/community centres → `access\_score (0–100)`

\- \*\*Equity Score v2\*\* — weighted blend of the 3 metrics → `equity\_score\_v2 (0–100)`



\### Visual Overlays

\- \*\*Stop Density Heatmap\*\* — identifies where transit stops cluster

\- \*\*Transit Dead Zone Dots\*\* — highlights neighbourhoods with large distance to nearest stop



---



\## Screenshots

\### Equity v2 Overview

!\[Equity v2](docs/screenshots/01-equity-v2.png)



\### Transit Overlays (Heatmap + Dead Zones)

!\[Transit overlays](docs/screenshots/02-heatmap-deadzones.png)



\### Neighbourhood Detail (Sidebar story)

!\[Neighbourhood detail](docs/screenshots/03-neighbourhood-detail.png)



---



\## Tech Stack

\- \*\*Frontend:\*\* React + Vite + MapLibre GL

\- \*\*Spatial/Data:\*\* Python (GeoPandas, Shapely, STRtree)

\- \*\*Sources:\*\* TTC GTFS (surface) + OpenStreetMap Overpass

\- \*\*Deployment:\*\* Vercel



---



\## How scoring works (high level)

Each layer computes distance from a neighbourhood representative point to the nearest relevant feature (stop/food/service).  

Distances are normalized into a \*\*0–100 score\*\* where \*\*higher is better\*\*.



Equity v2 (default):
equity_score_v2 = (transit_score + food_score + access_score) / 3


---

## Run locally

### Frontend
```bash
cd web
npm install
npm run dev

Data pipeline (optional rebuild)
# from project root (with your venv activated)
python data_pipeline/fetch_food_osm.py
python data_pipeline/compute_food_access.py

python data_pipeline/fetch_access_osm.py
python data_pipeline/compute_accessibility.py

python data_pipeline/compute_transit_access.py
python data_pipeline/export_transit_stops_web.py

python data_pipeline/compute_equity_v2.py

Data attribution & licensing

City of Toronto data: Contains information licensed under the Open Government Licence – Toronto

OpenStreetMap: © OpenStreetMap contributors
