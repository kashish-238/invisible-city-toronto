import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { centroid } from "@turf/turf";

function buildDeadzonePoints(neighbourhoodsGeojson, thresholdM) {
  if (!neighbourhoodsGeojson?.features) return { type: "FeatureCollection", features: [] };

  const features = neighbourhoodsGeojson.features
    .filter((f) => {
      const d = Number(f?.properties?.transit_dist_m);
      return Number.isFinite(d) && d > thresholdM;
    })
    .map((f) => {
      const c = centroid(f);
      c.properties = {
        neighbourhood_name: f?.properties?.neighbourhood_name ?? "",
        transit_dist_m: f?.properties?.transit_dist_m ?? null,
        transit_score: f?.properties?.transit_score ?? null,
      };
      return c;
    });

  return { type: "FeatureCollection", features };
}

export default function MapView({
  geojson,
  onSelect,
  metric,
  showHeatmap = false,
  showDeadZones = false,
  deadZoneThresholdM = 1200,
}) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const [hoverName, setHoverName] = useState(null);

  useEffect(() => {
    if (!geojson) return;

    const fillExpr = [
      "interpolate",
      ["linear"],
      ["coalesce", ["to-number", ["get", metric]], 0],
      0, "#c0392b",
      25, "#e67e22",
      50, "#f1c40f",
      75, "#7fbf7b",
      100, "#27ae60",
    ];

    const getName = (p) =>
      p?.neighbourhood_name ||
      p?.AREA_NAME ||
      p?.NAME ||
      p?.Neighbourhood ||
      p?.NEIGH_NAME ||
      "Neighbourhood";

    const deadzonePoints = buildDeadzonePoints(geojson, deadZoneThresholdM);

    // Update existing map instance
    if (mapRef.current) {
      const map = mapRef.current;

      const nSrc = map.getSource("neighbourhoods");
      if (nSrc && typeof nSrc.setData === "function") nSrc.setData(geojson);

      if (map.getLayer("nbh-fill")) {
        map.setPaintProperty("nbh-fill", "fill-color", fillExpr);
      }

      // Heatmap toggle
      if (map.getLayer("stops-heat")) {
        map.setLayoutProperty("stops-heat", "visibility", showHeatmap ? "visible" : "none");
      }

      // Deadzone dots update + toggle
      const dzSrc = map.getSource("deadzonePoints");
      if (dzSrc && typeof dzSrc.setData === "function") dzSrc.setData(deadzonePoints);

      if (map.getLayer("deadzone-dots")) {
        map.setLayoutProperty("deadzone-dots", "visibility", showDeadZones ? "visible" : "none");
      }

      setTimeout(() => map.resize(), 50);
      return;
    }

    // Create map first time
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [-79.3832, 43.6532],
      zoom: 9.5,
    });

    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", async () => {
      // Neighbourhood polygons
      map.addSource("neighbourhoods", { type: "geojson", data: geojson });

      map.addLayer({
        id: "nbh-fill",
        type: "fill",
        source: "neighbourhoods",
        paint: { "fill-opacity": 0.78, "fill-color": fillExpr },
      });

      map.addLayer({
        id: "nbh-line",
        type: "line",
        source: "neighbourhoods",
        paint: { "line-color": "#bdbdbd", "line-width": 1 },
      });

      // Hover / click
      map.on("mousemove", "nbh-fill", (e) => {
        if (!e.features?.length) return;
        setHoverName(getName(e.features[0].properties));
        map.getCanvas().style.cursor = "pointer";
      });

      map.on("mouseleave", "nbh-fill", () => {
        setHoverName(null);
        map.getCanvas().style.cursor = "";
      });

      map.on("click", "nbh-fill", (e) => {
        if (!e.features?.length) return;
        onSelect?.(e.features[0].properties);
      });

      // Heatmap of stops (optional)
      try {
        const stops = await fetch("/transit_stops.geojson").then((r) => r.json());
        map.addSource("stops", { type: "geojson", data: stops });

        map.addLayer({
          id: "stops-heat",
          type: "heatmap",
          source: "stops",
          layout: { visibility: showHeatmap ? "visible" : "none" },
          paint: {
            "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 9, 8, 12, 20],
            "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 9, 0.6, 12, 1.2],
            "heatmap-opacity": 0.6,
          },
        });
      } catch {
        // ignore if missing
      }

      // Deadzone dot layer (centroids)
      map.addSource("deadzonePoints", { type: "geojson", data: deadzonePoints });

      map.addLayer({
        id: "deadzone-dots",
        type: "circle",
        source: "deadzonePoints",
        layout: { visibility: showDeadZones ? "visible" : "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 4, 12, 7],
          "circle-opacity": 0.9,
          "circle-color": "#8e0000",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1,
        },
      });

      setTimeout(() => map.resize(), 50);
    });

    const onResize = () => mapRef.current?.resize();
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      map.remove();
      mapRef.current = null;
    };
  }, [geojson, metric, onSelect, showHeatmap, showDeadZones, deadZoneThresholdM]);

  return (
    <div style={{ position: "relative", height: "100%", width: "100%" }}>
      <div ref={mapContainer} style={{ height: "100%", width: "100%" }} />
      {hoverName && (
        <div
          style={{
            position: "absolute",
            left: 12,
            bottom: 12,
            background: "white",
            border: "1px solid #e0e0e0",
            borderRadius: 8,
            padding: "8px 10px",
            fontSize: 13,
            maxWidth: 280,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {hoverName}
        </div>
      )}
    </div>
  );
}
