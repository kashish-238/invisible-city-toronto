# Invisible City: Toronto 🌍  
**Built by Sahil Patel**  
An interactive urban equity map for Toronto that reveals “invisible” access gaps across neighbourhoods.

🔗 **Live Demo:** https://invisible-city-toronto.vercel.app/  
📦 **GitHub Repo:** https://github.com/kashish-238/invisible-city-toronto  

---

## ✨ What this project does

**Invisible City: Toronto** visualizes neighbourhood-level inequality using a clean, professor-friendly storytelling UI.

It helps answer:

- Which neighbourhoods are underserved by transit?
- Where are food deserts located?
- Which areas lack access to essential services?
- What does overall urban equity look like?

---

## ✅ Current Layers (MVP+)

### 🚇 Transit Access (TTC)
Distance to the nearest TTC stop → `transit_score (0–100)`

### 🥗 Food Access (OSM)
Distance to the nearest grocery/food location → `food_score (0–100)`

### 🏥 Essential Services Access (OSM)
Distance to clinics/hospitals/community centres → `access_score (0–100)`

### 🌍 Equity Score v2
Weighted blend of the 3 metrics → `equity_score_v2 (0–100)`

---

## 🔥 Visual Overlays

- **Stop Density Heatmap** — identifies transit clustering
- **Transit Dead Zone Dots** — highlights neighbourhoods far from transit access

---

## 📸 Screenshots

### Equity v2 Overview
![Equity v2](docs/screenshots/01-equity-v2.png)

### Transit Overlays (Heatmap + Dead Zones)
![Transit overlays](docs/screenshots/02-heatmap-deadzones.png)

### Neighbourhood Detail View
![Neighbourhood detail](docs/screenshots/03-neighbourhood-detail.png)

---

## 🛠 Tech Stack

- **Frontend:** React + Vite + MapLibre GL  
- **Spatial/Data Pipeline:** Python (GeoPandas, Shapely, STRtree)  
- **Transit Data:** TTC GTFS (surface feed)  
- **Open Data:** OpenStreetMap Overpass API  
- **Deployment:** Vercel  

---

## 📊 How scoring works (high level)

Each layer computes distance from a neighbourhood centroid to the nearest relevant feature:

- TTC stop  
- Food source  
- Essential service  

Distances are normalized into a **0–100 score**, where:

✅ Higher = better access  
❌ Lower = underserved

Equity v2:
equity_score_v2 = (transit_score + food_score + access_score) / 3


---

## 🚀 Run locally

### Frontend
```bash
cd web
npm install
npm run dev

Data pipeline (optional rebuild)
python data_pipeline/fetch_food_osm.py
python data_pipeline/compute_food_access.py

python data_pipeline/fetch_access_osm.py
python data_pipeline/compute_accessibility.py

python data_pipeline/compute_transit_access.py
python data_pipeline/export_transit_stops_web.py

python data_pipeline/compute_equity_v2.py

📜 Data attribution & licensing

City of Toronto data: Contains information licensed under the
Open Government Licence – Toronto

OpenStreetMap: © OpenStreetMap contributors