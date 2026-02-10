import { useEffect, useMemo, useState } from "react";
import MapView from "./MapView";
import "./app.css";

const MODES = {
  TRANSIT: "transit",
  FOOD: "food",
  ACCESS: "access",
  EQUITY_V2: "equity_v2",
};

function fmtMeters(m) {
  if (m == null || Number.isNaN(Number(m))) return "—";
  const n = Number(m);
  if (n >= 1000) return `${(n / 1000).toFixed(2)} km`;
  return `${Math.round(n)} m`;
}

function clamp01to100(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(100, n));
}

export default function App() {
  // Mode + overlays
  const [mode, setMode] = useState(MODES.TRANSIT);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showDeadZones, setShowDeadZones] = useState(false);
  const [deadZoneThresholdM, setDeadZoneThresholdM] = useState(1200);

  // Data
  const [transitGJ, setTransitGJ] = useState(null);
  const [foodGJ, setFoodGJ] = useState(null);
  const [accessGJ, setAccessGJ] = useState(null);
  const [equityV2GJ, setEquityV2GJ] = useState(null);

  // Selected feature props from current map dataset
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch("/neighbourhood_transit_scores.geojson").then((r) => r.json()).then(setTransitGJ);
    fetch("/neighbourhood_food_scores.geojson").then((r) => r.json()).then(setFoodGJ);
    fetch("/neighbourhood_access_scores.geojson").then((r) => r.json()).then(setAccessGJ);
    fetch("/neighbourhood_equity_v2_scores.geojson").then((r) => r.json()).then(setEquityV2GJ);
  }, []);

  const { geojson, metric, title } = useMemo(() => {
    if (mode === MODES.TRANSIT) return { geojson: transitGJ, metric: "transit_score", title: "Transit Access" };
    if (mode === MODES.FOOD) return { geojson: foodGJ, metric: "food_score", title: "Food Access" };
    if (mode === MODES.ACCESS) return { geojson: accessGJ, metric: "access_score", title: "Essential Services Access" };
    return { geojson: equityV2GJ, metric: "equity_score_v2", title: "Equity Score (v2)" };
  }, [mode, transitGJ, foodGJ, accessGJ, equityV2GJ]);

  const name =
    selected?.neighbourhood_name ||
    selected?.AREA_NAME ||
    selected?.NAME ||
    selected?.Neighbourhood ||
    selected?.NEIGH_NAME ||
    "Select a neighbourhood";

  // Fields (available in current dataset only)
  const transitScore = selected?.transit_score;
  const transitDist = selected?.transit_dist_m;

  const foodScore = selected?.food_score;
  const foodDist = selected?.food_dist_m;

  const accessScore = selected?.access_score;
  const accessDist = selected?.access_dist_m;

  const equityV2Score = selected?.equity_score_v2;
  const limitingV2 = selected?.limiting_factor_v2;

  const score =
    mode === MODES.TRANSIT ? transitScore :
    mode === MODES.FOOD ? foodScore :
    mode === MODES.ACCESS ? accessScore :
    equityV2Score;

  const scoreWidth = `${clamp01to100(score)}%`;

  // Overlays only meaningful when we have transit_dist_m in the active geojson:
  // Transit geojson definitely has it, Equity v2 geojson also has it (because it starts from transit).
  const overlaysEnabled = (mode === MODES.TRANSIT || mode === MODES.EQUITY_V2);

  if (!geojson) return <div style={{ padding: 20 }}>Loading {title}…</div>;

  return (
    <div className="layout">
      <header className="header">
        <div>
          <div className="title">Invisible City: Toronto</div>
          <div className="subtitle">
  Urban Access & Equity Overview • Built by <b>Kashish Dhanani</b>
</div>

        </div>

        <div className="topRight">
          <div className="modes">
            <button className={`mode ${mode === MODES.TRANSIT ? "active" : ""}`} onClick={() => { setMode(MODES.TRANSIT); setSelected(null); }}>
              Transit
            </button>
            <button className={`mode ${mode === MODES.FOOD ? "active" : ""}`} onClick={() => { setMode(MODES.FOOD); setSelected(null); }}>
              Food
            </button>
            <button className={`mode ${mode === MODES.ACCESS ? "active" : ""}`} onClick={() => { setMode(MODES.ACCESS); setSelected(null); }}>
              Access
            </button>
            <button className={`mode ${mode === MODES.EQUITY_V2 ? "active" : ""}`} onClick={() => { setMode(MODES.EQUITY_V2); setSelected(null); }}>
              Equity v2
            </button>
          </div>

          <div className="overlays">
            <label className={`check ${!overlaysEnabled ? "disabled" : ""}`}>
              <input
                type="checkbox"
                checked={showHeatmap}
                onChange={(e) => setShowHeatmap(e.target.checked)}
                disabled={!overlaysEnabled}
              />
              Stop density heatmap
            </label>

            <label className={`check ${!overlaysEnabled ? "disabled" : ""}`}>
              <input
                type="checkbox"
                checked={showDeadZones}
                onChange={(e) => setShowDeadZones(e.target.checked)}
                disabled={!overlaysEnabled}
              />
              Transit dead zones
            </label>

            <div className={`threshold ${(!overlaysEnabled || !showDeadZones) ? "disabled" : ""}`}>
              <span>Threshold:</span>
              <select
                value={deadZoneThresholdM}
                onChange={(e) => setDeadZoneThresholdM(Number(e.target.value))}
                disabled={!overlaysEnabled || !showDeadZones}
              >
                <option value={600}>600 m</option>
                <option value={800}>800 m</option>
                <option value={1000}>1000 m</option>
                <option value={1200}>1200 m</option>
                <option value={1500}>1500 m</option>
                <option value={2000}>2000 m</option>
              </select>
            </div>

            {!overlaysEnabled && (
              <div className="hint">Overlays available in Transit / Equity v2.</div>
            )}
          </div>
        </div>
      </header>

      <main className="main">
        <section className="map">
          <MapView
            geojson={geojson}
            onSelect={setSelected}
            metric={metric}
            showHeatmap={showHeatmap}
            showDeadZones={showDeadZones}
            deadZoneThresholdM={deadZoneThresholdM}
          />

          <div className="legend">
            <div className="legendTitle">{title}</div>
            <div className="legendRow">
              <span>Lower</span>
              <div className="legendBar" />
              <span>Higher</span>
            </div>
            <div className="legendFoot">0–100 score (higher is better)</div>
          </div>
        </section>

        <aside className="side">
          <div className="panelTitle">Neighbourhood Overview</div>
          <div className="name">{name}</div>

          <div className="block">
            <div className="label">{title}</div>
            <div className="score">
              {score ?? "—"} <span className="outOf">/ 100</span>
            </div>
            <div className="barBg">
              <div className="barFill" style={{ width: scoreWidth }} />
            </div>

            {mode === MODES.TRANSIT && (
              <div className="meta">
                Nearest transit stop: <b>{fmtMeters(transitDist)}</b>
              </div>
            )}

            {mode === MODES.FOOD && (
              <div className="meta">
                Nearest food point: <b>{fmtMeters(foodDist)}</b>
              </div>
            )}

            {mode === MODES.ACCESS && (
              <div className="meta">
                Nearest essential service: <b>{fmtMeters(accessDist)}</b>
              </div>
            )}

            {mode === MODES.EQUITY_V2 && (
              <>
                <div className="meta"><b>Transit:</b> {transitScore ?? "—"} ( {fmtMeters(transitDist)} )</div>
                <div className="meta"><b>Food:</b> {foodScore ?? "—"} ( {fmtMeters(foodDist)} )</div>
                <div className="meta"><b>Access:</b> {accessScore ?? "—"} ( {fmtMeters(accessDist)} )</div>
                <div className="meta">Primary limiting factor: <b>{limitingV2 ?? "—"}</b></div>
              </>
            )}
          </div>

          <div className="block">
            <div className="label">Attribution</div>
            <div className="note">
              Contains information licensed under the Open Government Licence - Toronto<br />
              © OpenStreetMap contributors
            </div>
          </div>

          <footer className="footer">
  Data sources: City of Toronto Neighbourhoods + TTC Surface GTFS + OSM (Overpass)
  <br />
  Project by <b>Kashish Dhanani</b> • Invisible City: Toronto © 2026
</footer>

        </aside>
      </main>
    </div>
  );
}
