import { useEffect, useMemo, useState } from "react";
import MapView from "./components/MapView";
import RerouteAlert from "./components/RerouteAlert";
import RouteCard from "./components/RouteCard";
import SearchPanel from "./components/SearchPanel";
import WeatherBadge from "./components/WeatherBadge";
import { usePolling } from "./hooks/usePolling";
import { fetchAreaPrediction, fetchHealth, fetchOptimalRoutes, fetchPlaces, recalculateRoutes } from "./services/api";

const initialOrigin = { label: "MG Road", lat: 12.9756, lng: 77.605 };
const initialDestination = { label: "Electronic City", lat: 12.8399, lng: 77.677 };

export default function App() {
  const [origin, setOrigin] = useState(initialOrigin);
  const [destination, setDestination] = useState(initialDestination);
  const [vehicleType, setVehicleType] = useState("car");
  const [optimizeFor, setOptimizeFor] = useState("time");
  const [routes, setRoutes] = useState([]);
  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0);
  const [weather, setWeather] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rerouteMessage, setRerouteMessage] = useState("");
  const [inputError, setInputError] = useState("");
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [theme, setTheme] = useState(() => localStorage.getItem("traffic-theme") || "light");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("traffic-theme", theme);
  }, [theme]);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {});
    fetchPlaces().then((places) => {
      setOriginSuggestions(places);
      setDestinationSuggestions(places);
    }).catch(() => {});
  }, []);

  const routePayload = useMemo(
    () => ({
      origin_name: origin.label,
      destination_name: destination.label,
      origin_lat: origin.lat,
      origin_lng: origin.lng,
      dest_lat: destination.lat,
      dest_lng: destination.lng,
      vehicle_type: vehicleType,
      optimize_for: optimizeFor,
      current_route_index: selectedRouteIndex,
      current_lat: origin.lat,
      current_lng: origin.lng,
    }),
    [destination.lat, destination.lng, optimizeFor, origin.lat, origin.lng, selectedRouteIndex, vehicleType],
  );

  async function loadDashboard() {
    setSubmitAttempted(true);
    if (!origin.label.trim() || !destination.label.trim()) {
      setInputError("Enter both an origin and a destination.");
      return;
    }
    setInputError("");
    setLoading(true);
    try {
      const [healthData, routeData, predictData] = await Promise.all([
        fetchHealth(),
        fetchOptimalRoutes(routePayload),
        fetchAreaPrediction(
          origin.label,
          new Date().getHours(),
          new Date().getDay() === 0 ? 6 : new Date().getDay() - 1,
          vehicleType,
        ),
      ]);
      setHealth(healthData);
      setRoutes(routeData.routes);
      setSelectedRouteIndex(routeData.best_route_index ?? 0);
      setWeather(routeData.weather);
      setPrediction(predictData);
      if (routeData.resolved_origin) setOrigin(routeData.resolved_origin);
      if (routeData.resolved_destination) setDestination(routeData.resolved_destination);
      setRerouteMessage(routeData.reroute_message || "");
    } catch (error) {
      setInputError(
        error?.response?.data?.detail || "Could not calculate route. Check the locations and try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function searchOrigin(query) {
    if (!query.trim()) return;
    const places = await fetchPlaces(query).catch(() => []);
    setOriginSuggestions(places);
  }

  async function searchDestination(query) {
    if (!query.trim()) return;
    const places = await fetchPlaces(query).catch(() => []);
    setDestinationSuggestions(places);
  }

  usePolling(async () => {
    if (!routes.length) return;
    const refreshed = await recalculateRoutes(routePayload);
    setRoutes(refreshed.routes);
    setWeather(refreshed.weather);
    if (refreshed.reroute_available) {
      setRerouteMessage(refreshed.reroute_message || "");
    }
  }, 30000, true);

  const predVolume = prediction?.predicted_traffic_volume;
  const displayVolume =
    predVolume != null ? Math.abs(Math.round(predVolume)).toLocaleString() : null;

  return (
    <div className="app">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="app-brand">
            <div className="brand-icon">🗺️</div>
            <div>
              <div className="brand-name">Traffic Optimizer</div>
              <div className="brand-sub">Bengaluru Route Intelligence</div>
            </div>
          </div>
          <div className="sidebar-meta">
            <span className={`status-pill${health?.status !== "ok" ? " offline" : ""}`}>
              {health?.status === "ok" ? "API connected" : "API offline"}
            </span>
            {health?.artifact_loaded && (
              <span className="status-pill">Model ready</span>
            )}
            <span className="meta-spacer" />
            <button
              type="button"
              className="theme-btn"
              onClick={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
            >
              {theme === "light" ? "🌙 Dark" : "☀️ Light"}
            </button>
          </div>
        </div>

        <div className="sidebar-body">
          <SearchPanel
            origin={origin}
            destination={destination}
            vehicleType={vehicleType}
            optimizeFor={optimizeFor}
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onVehicleChange={setVehicleType}
            onOptimizeChange={setOptimizeFor}
            onSubmit={loadDashboard}
            loading={loading}
            originSuggestions={originSuggestions}
            destinationSuggestions={destinationSuggestions}
            onOriginSearch={searchOrigin}
            onDestinationSearch={searchDestination}
            submitAttempted={submitAttempted}
          />

          {inputError && <div className="error-banner">{inputError}</div>}

          <WeatherBadge weather={weather} />

          {prediction && (
            <div className="card">
              <p className="section-label">Traffic prediction</p>
              <div className="pred-header">
                <span className="pred-name">
                  {prediction.requested_location || prediction.area_name}
                </span>
                <span className={`pill pill-${prediction.congestion_bucket}`}>
                  {prediction.congestion_bucket}
                </span>
              </div>
              <div className="pred-stats">
                <span>⚡ {prediction.predicted_average_speed} km/h avg</span>
                {displayVolume && <span>🚗 ~{displayVolume} veh/hr</span>}
                <span style={{ gridColumn: "1 / -1", fontSize: "0.72rem", opacity: 0.6 }}>
                  Source: {prediction.model_source}
                </span>
              </div>
            </div>
          )}

          {routes.length > 0 && (
            <div>
              <p className="section-label" style={{ marginBottom: 8 }}>
                {routes.length} routes found — click to select
              </p>
              <div className="route-list">
                {routes.map((route, index) => (
                  <RouteCard
                    key={route.route_index}
                    route={route}
                    selected={index === selectedRouteIndex}
                    onSelect={() => setSelectedRouteIndex(index)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* ── Map ── */}
      <MapView
        origin={origin}
        destination={destination}
        routes={routes}
        selectedRouteIndex={selectedRouteIndex}
        onSelectRoute={setSelectedRouteIndex}
      />

      <RerouteAlert
        message={rerouteMessage}
        onAccept={() => setSelectedRouteIndex(routes.findIndex((r) => r.recommended) || 0)}
        onDismiss={() => setRerouteMessage("")}
      />
    </div>
  );
}
