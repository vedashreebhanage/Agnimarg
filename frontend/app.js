const API = "/api";

let map, roadLayer, hotspotLayer, coneLayer, routeLayer, villageMarker, shelterMarker;
let state = null;
let lastCones = null;

function initMap(bbox) {
  map = L.map("map", { preferCanvas: true }).fitBounds([
    [bbox.south, bbox.west],
    [bbox.north, bbox.east],
  ]);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(map);
  roadLayer = L.layerGroup().addTo(map);
  hotspotLayer = L.layerGroup().addTo(map);
  coneLayer = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);
}

function renderRoads(edges) {
  const canvas = L.canvas();
  for (const [a, b] of edges) {
    L.polyline([a, b], { color: "#565f82", weight: 1, opacity: 0.55, renderer: canvas }).addTo(roadLayer);
  }
}

function fireIcon() {
  return L.divIcon({
    className: "",
    html: '<div style="font-size:18px;filter:drop-shadow(0 0 3px #000)">\u{1F525}</div>',
    iconSize: [22, 22],
  });
}

function renderHotspots(hotspots) {
  hotspotLayer.clearLayers();
  for (const h of hotspots) {
    L.marker([h.lat, h.lon], { icon: fireIcon() })
      .bindPopup(`Hotspot ${h.id} — ${h.near}<br>FRP ${h.frp_mw} MW · confidence ${h.confidence}`)
      .addTo(hotspotLayer);
  }
}

const RING_STYLE = {
  "1h": { color: "#ef4444", fillOpacity: 0.35 },
  "3h": { color: "#f97316", fillOpacity: 0.2 },
  "6h": { color: "#facc15", fillOpacity: 0.1 },
};

function renderCones(conesByHotspot) {
  coneLayer.clearLayers();
  for (const cones of Object.values(conesByHotspot)) {
    for (const [ringKey, ring] of Object.entries(cones)) {
      const style = RING_STYLE[ringKey] || { color: "#fff", fillOpacity: 0.1 };
      L.polygon(ring.polygon, { color: style.color, weight: 1, fillOpacity: style.fillOpacity })
        .bindPopup(`${ringKey} threat cone — radius ${ring.radius_km} km`)
        .addTo(coneLayer);
    }
  }
}

function renderRoutes(baseline, safe) {
  routeLayer.clearLayers();
  L.polyline(baseline.path_latlon, { color: "#8b949e", weight: 3, dashArray: "6 6" })
    .bindPopup(`Baseline route (ignores fire) — ${baseline.eta_min} min`)
    .addTo(routeLayer);
  L.polyline(safe.path_latlon, { color: "#22c55e", weight: 4 })
    .bindPopup(`Re-costed safe route — ${safe.eta_min} min`)
    .addTo(routeLayer);
}

function pointInPolygon(lat, lon, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [yi, xi] = polygon[i];
    const [yj, xj] = polygon[j];
    const intersects = yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi + 1e-15) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
}

function highlightBlockedRoads(edges, conesByHotspot) {
  const rings1h = Object.values(conesByHotspot).map((c) => c["1h"].polygon);
  const canvas = L.canvas();
  for (const [a, b] of edges) {
    const midLat = (a[0] + b[0]) / 2;
    const midLon = (a[1] + b[1]) / 2;
    const blocked = rings1h.some((poly) => pointInPolygon(midLat, midLon, poly));
    if (blocked) {
      L.polyline([a, b], { color: "#ef4444", weight: 3, opacity: 0.9, renderer: canvas })
        .bindPopup("Blocked — inside 1h threat cone")
        .addTo(routeLayer);
    }
  }
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

/** Fetch wrapper that turns network failures (server down, no connection,
 * CORS, etc.) into a consistent {ok: false, networkError: true, message}
 * shape instead of throwing — callers no longer need their own try/catch. */
async function apiFetch(path, options) {
  try {
    const res = await fetch(`${API}${path}`, options);
    let data = null;
    try {
      data = await res.json();
    } catch {
      // non-JSON body (e.g. an unexpected 500 with an HTML error page) — data stays null
    }
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    return { ok: false, networkError: true, message: `Could not reach the server: ${e.message}` };
  }
}

/** Offline/degraded-mode fallback — answers the original security audit's
 * Tier-1 finding #3 ("no offline/degraded-mode fallback ... wildfires
 * routinely take out power and cell towers, exactly when the system is
 * needed most"), whose own recommended fix was "cached last-known-good
 * state". Caches successful /api/state and /api/simulate responses in
 * localStorage; if a later request fails due to a network error, falls back
 * to the cache instead of just showing an error, with a clear "stale data"
 * banner so it's never mistaken for live. */
const CACHE_KEYS = { state: "agnimarg_cache_state", simulate: "agnimarg_cache_simulate" };

function cacheSave(key, data) {
  try {
    localStorage.setItem(key, JSON.stringify({ data, cachedAt: Date.now() }));
  } catch {
    // localStorage unavailable (private browsing, quota exceeded) — degraded
    // mode just won't have a cache to fall back on; not fatal on its own.
  }
}

function cacheLoad(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null; // {data, cachedAt} | null
  } catch {
    return null;
  }
}

function formatCacheAge(cachedAt) {
  const seconds = Math.round((Date.now() - cachedAt) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.round(minutes / 60)}h ago`;
}

/** Disables the given button IDs for the duration of `fn`, restoring their
 * previous disabled state afterward (rather than force-enabling buttons that
 * were legitimately disabled for another reason, e.g. tamper/approve before
 * the first simulation has ever run). */
async function withButtonsDisabled(ids, fn) {
  const buttons = ids.map((id) => document.getElementById(id));
  const prevDisabled = buttons.map((b) => b.disabled);
  buttons.forEach((b) => (b.disabled = true));
  try {
    return await fn();
  } finally {
    buttons.forEach((b, i) => (b.disabled = prevDisabled[i]));
  }
}

async function loadAuditLog() {
  const result = await apiFetch("/audit-log");
  if (!result.ok) return; // non-critical panel — fail silently rather than blocking the main flow
  const el = document.getElementById("auditLog");
  el.innerHTML = result.data.entries
    .slice()
    .reverse()
    .map(
      (e) =>
        `<div class="audit-entry">#${e.seq} <span class="actor">${e.actor}</span> <span class="action">${e.action}</span><br>${JSON.stringify(e.details)}</div>`
    )
    .join("");
}

/** Renders a simulation result (fresh or from the offline cache) into the
 * panel and map. `offlinePrefix` is prepended to the weather readout when
 * this is cached data being shown because the live request failed. */
function applySimulationResult(data, offlinePrefix = "") {
  lastCones = data.cones_by_hotspot;

  const w = data.weather;
  setText(
    "weatherReadout",
    `${offlinePrefix}Weather (${w.source}):\ntemp ${w.temperature_c}°C, humidity ${w.humidity_pct}%, wind ${w.wind_speed_kmh} km/h @ ${w.wind_direction_deg}°`
  );
  const corroborationNote =
    data.unconfirmed_hotspots.length > 0
      ? `\n⚠️ ${data.unconfirmed_hotspots.length} report(s) excluded — no corroborating second source (single-point reports aren't trusted alone).`
      : `\nAll ${data.confirmed_hotspot_count} hotspot report(s) corroborated by a nearby second source.`;
  setText(
    "riskReadout",
    `Risk score: ${data.risk_score} (0-1 heuristic, FWI-style)\nThreat-cone signature: ${data.signature.slice(0, 24)}… (HMAC-SHA256, verified by EXODUS)${corroborationNote}`
  );
  setText(
    "routeReadout",
    `Baseline ETA (ignores fire): ${data.baseline_route.eta_min} min\nSafe ETA (re-costed around fire): ${data.safe_route.eta_min} min\nRe-routed: ${data.rerouted ? "yes" : "no"}\nBlocked road segments: ${data.blocked_edge_count}`
  );

  renderCones(data.cones_by_hotspot);
  renderRoutes(data.baseline_route, data.safe_route);
  highlightBlockedRoads(state.graph_edges, data.cones_by_hotspot);

  document.getElementById("btnTamper").disabled = false;
  document.getElementById("btnApprove").disabled = false;
}

async function runSimulation(mode) {
  await withButtonsDisabled(["btnSimScenario", "btnSimLive"], async () => {
    setText("weatherReadout", "Running simulation…");
    const result = await apiFetch(`/simulate?mode=${mode}`, { method: "POST" });

    if (result.networkError) {
      const cached = cacheLoad(CACHE_KEYS.simulate);
      if (cached) {
        applySimulationResult(cached.data, `⚠️ OFFLINE — server unreachable, showing cached simulation from ${formatCacheAge(cached.cachedAt)} (mode: ${cached.data.mode}).\n\n`);
      } else {
        setText("weatherReadout", `⚠️ ${result.message}\n(No cached simulation available to fall back to yet — run one successfully first.)`);
      }
      return;
    }
    if (!result.ok) {
      setText("weatherReadout", `Error: ${result.data?.detail ?? `HTTP ${result.status}`}`);
      return;
    }

    const data = result.data;
    applySimulationResult(data);
    cacheSave(CACHE_KEYS.simulate, { ...data, mode });

    await loadAuditLog();
  });
}

async function runTamperDemo() {
  await withButtonsDisabled(["btnTamper"], async () => {
    setText("tamperReadout", "Replaying tampered payload…");
    const result = await apiFetch("/tamper-demo", { method: "POST" });
    if (result.networkError) {
      setText("tamperReadout", `⚠️ ${result.message}`);
      return;
    }
    if (!result.ok) {
      setText("tamperReadout", `Error: ${result.data?.detail ?? `HTTP ${result.status}`}`);
      return;
    }
    setText(
      "tamperReadout",
      result.data.rejected
        ? `✅ EXODUS rejected the tampered payload:\n"${result.data.reason}"`
        : `⚠️ Unexpected: tampered payload was accepted.`
    );
    await loadAuditLog();
  });
}

let sessionToken = null;
let sessionUser = null;

async function login() {
  await withButtonsDisabled(["btnLogin"], async () => {
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;
    const statusEl = document.getElementById("loginStatus");
    statusEl.textContent = "Signing in…";

    const result = await apiFetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (result.networkError) {
      statusEl.textContent = `⚠️ ${result.message}`;
      statusEl.classList.remove("signed-in");
      return;
    }
    if (!result.ok) {
      statusEl.textContent = `Login failed: ${result.data?.detail ?? `HTTP ${result.status}`}`;
      statusEl.classList.remove("signed-in");
      sessionToken = null;
      sessionUser = null;
      return;
    }
    sessionToken = result.data.token;
    sessionUser = { username: result.data.username, role: result.data.role };
    statusEl.textContent = `Signed in as ${result.data.username} (${result.data.role})`;
    statusEl.classList.add("signed-in");
    await loadAuditLog();
  });
}

async function approveDispatch() {
  if (!sessionToken) {
    setText("approveReadout", "❌ Log in first (see the box in the top-right corner).");
    return;
  }
  await withButtonsDisabled(["btnApprove"], async () => {
    setText("approveReadout", "Requesting approval…");
    const result = await apiFetch("/dispatch/approve", {
      method: "POST",
      headers: { Authorization: `Bearer ${sessionToken}` },
    });
    if (result.networkError) {
      setText("approveReadout", `⚠️ ${result.message}`);
      return;
    }
    setText("approveReadout", result.ok ? result.data.message : `❌ Denied: ${result.data?.detail ?? `HTTP ${result.status}`}`);
    await loadAuditLog();
  });
}

function applyState(stateData, offlinePrefix = "") {
  state = stateData;

  document.getElementById("banner").textContent = `${offlinePrefix}${state.event_label} — ${state.event_note}`;

  initMap(state.graph_bbox);
  renderRoads(state.graph_edges);
  renderHotspots(state.hotspots);

  villageMarker = L.marker([state.village_at_risk.lat, state.village_at_risk.lon])
    .bindPopup(`At-risk village: ${state.village_at_risk.name}`)
    .addTo(map);
  shelterMarker = L.marker([state.shelter.lat, state.shelter.lon])
    .bindPopup(`Shelter: ${state.shelter.name}`)
    .addTo(map);
}

async function main() {
  const result = await apiFetch("/state");

  if (!result.ok) {
    const cached = cacheLoad(CACHE_KEYS.state);
    if (cached) {
      applyState(cached.data, `⚠️ OFFLINE — server unreachable, showing cached map data from ${formatCacheAge(cached.cachedAt)}. `);
    } else {
      const message = result.networkError
        ? result.message
        : `Server returned an error loading demo state (HTTP ${result.status}).`;
      document.getElementById("banner").textContent = `⚠️ ${message} (No cached data available to fall back to yet.)`;
      return; // no state at all — nothing to wire up buttons against
    }
  } else {
    applyState(result.data);
    cacheSave(CACHE_KEYS.state, result.data);
  }

  document.getElementById("btnSimScenario").addEventListener("click", () => runSimulation("scenario"));
  document.getElementById("btnSimLive").addEventListener("click", () => runSimulation("live"));
  document.getElementById("btnTamper").addEventListener("click", runTamperDemo);
  document.getElementById("btnApprove").addEventListener("click", approveDispatch);
  document.getElementById("btnLogin").addEventListener("click", login);

  await loadAuditLog();
}

main().catch((e) => {
  document.getElementById("banner").textContent = `Failed to load: ${e}`;
  console.error(e);
});
