// Shared map logic for all map pages.
// Each page sets `window.MAP_BOROUGH` (e.g. "Manhattan") before loading this;
// leave it null for the all-NYC map. Data: places.js (pins) + boroughs.js (basemap).
//
// The basemap is a vector borough outline (boroughs.js) — NOT raster tiles — so
// the map always renders an outline with no external network dependency.

(function () {
  const CATEGORIES = {
    playground:    { color: "#2e9e4f", label: "Playgrounds", emoji: "🛝" },
    museum:        { color: "#7048c4", label: "Museums",     emoji: "🎨" },
    restaurant:    { color: "#e8702a", label: "Restaurants", emoji: "🍴" },
    library:       { color: "#8a5a2b", label: "Libraries",   emoji: "📚" },
    class:         { color: "#2b7fd6", label: "Classes",     emoji: "🎵" },
    pool:          { color: "#1c9bd1", label: "Pools",       emoji: "🏊" },
    "indoor-play": { color: "#f2b705", label: "Indoor play", emoji: "🏠" },
    other:         { color: "#0d9488", label: "Other",       emoji: "📍" },
  };
  const catOf = (c) => (CATEGORIES[c] ? c : "other");

  const BOROUGH = (typeof window.MAP_BOROUGH === "string") ? window.MAP_BOROUGH : null;

  const map = L.map("map", { scrollWheelZoom: true });

  // --- Vector basemap: NYC borough outlines (always renders, no tiles needed) ---
  let boroLayer = null;
  if (typeof NYC_BOROUGHS !== "undefined") {
    const feats = BOROUGH
      ? { type: "FeatureCollection", features: NYC_BOROUGHS.features.filter((f) => f.properties && f.properties.name === BOROUGH) }
      : NYC_BOROUGHS;
    boroLayer = L.geoJSON(feats, {
      style: () => ({ color: "#d6478f", weight: 1.5, fillColor: "#f7c4dd", fillOpacity: 0.9 }),
    }).addTo(map);
    boroLayer.eachLayer((l) => {
      const nm = l.feature && l.feature.properties && l.feature.properties.name;
      if (nm) l.bindTooltip(nm, { permanent: true, direction: "center", className: "borough-label" });
    });
  }

  const groups = {}, counts = {};
  Object.keys(CATEGORIES).forEach((k) => { groups[k] = L.layerGroup(); counts[k] = 0; });

  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const data = (typeof PLACES !== "undefined" && Array.isArray(PLACES)) ? PLACES : [];
  const scoped = BOROUGH ? data.filter((p) => p.borough === BOROUGH) : data;

  const bounds = [];
  scoped.forEach((p) => {
    if (typeof p.lat !== "number" || typeof p.lng !== "number") return;
    const cat = catOf(p.category);
    const { color } = CATEGORIES[cat];
    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 9, color: "#fff", weight: 2, fillColor: color, fillOpacity: 0.95,
    });
    const meta = [p.neighborhood, p.borough].filter(Boolean).join(", ");
    const bits = [p.cost && esc(p.cost), p.age_range && "ages " + esc(p.age_range),
                  p.indoor === "true" ? "indoor" : p.indoor === "false" ? "outdoor" : ""]
                 .filter(Boolean).join(" · ");
    const parking = p.parking ? `<div class="meta">🚗 ${esc(p.parking)}</div>` : "";
    marker.bindPopup(
      `<div class="title">${CATEGORIES[cat].emoji} ${esc(p.name)}</div>` +
      `<div class="meta">${esc(meta)}</div>` +
      (bits ? `<div class="meta">${bits}</div>` : "") + parking +
      (p.url ? `<a class="more" href="${esc(p.url)}">Open page →</a>` : "")
    );
    marker.addTo(groups[cat]);
    counts[cat] += 1;
    bounds.push([p.lat, p.lng]);
  });

  // Borough switcher.
  const sw = document.getElementById("boroughs");
  if (sw) {
    const tabs = [["", "All NYC", "map.html"], ["Manhattan", "Manhattan", "manhattan.html"],
                  ["Brooklyn", "Brooklyn", "brooklyn.html"], ["Queens", "Queens", "queens.html"]];
    sw.innerHTML = tabs.map(([b, label, href]) =>
      `<a class="tab${(BOROUGH || "") === b ? " active" : ""}" href="${href}">${label}</a>`).join("");
  }

  // Category filters (only those present in scope).
  const filters = document.getElementById("filters");
  Object.keys(CATEGORIES).forEach((k) => {
    if (counts[k] === 0) return;
    groups[k].addTo(map);
    const { color, label, emoji } = CATEGORIES[k];
    const row = document.createElement("label");
    row.innerHTML =
      `<input type="checkbox" checked data-cat="${k}">` +
      `<span class="dot" style="background:${color}"></span>` +
      `<span>${emoji} ${label}</span><span class="count">${counts[k]}</span>`;
    row.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) groups[k].addTo(map); else map.removeLayer(groups[k]);
    });
    filters.appendChild(row);
  });

  // Frame the view: the borough outline(s) for context, else the pins.
  if (boroLayer && boroLayer.getBounds().isValid()) {
    map.fitBounds(boroLayer.getBounds(), { padding: [20, 20] });
  } else if (bounds.length) {
    map.fitBounds(bounds, { padding: [50, 50] });
  } else {
    map.setView([40.7308, -73.9975], 11);
  }
})();
