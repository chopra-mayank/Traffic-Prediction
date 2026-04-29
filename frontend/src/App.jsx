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
  const [theme, setTheme] = useState(() => localStorage.getItem("traffic-theme") || "light");
  const [inputError, setInputError] = useState("");
  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("traffic-theme", theme);
  }, [theme]);

  useEffect(() => {
    async function loadDefaults() {
      const places = await fetchPlaces();
      setOriginSuggestions(places);
      setDestinationSuggestions(places);
    }
    loadDefaults();
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
    if (!origin.label.trim() || !destination.label.trim()) {
      setInputError("Enter both an origin and a destination in Bengaluru.");
      return;
    }
    setInputError("");
    setLoading(true);
    try {
      const [healthData, routeData, predictData] = await Promise.all([
        fetchHealth(),
        fetchOptimalRoutes(routePayload),
        fetchAreaPrediction(origin.label, new Date().getHours(), new Date().getDay() === 0 ? 6 : new Date().getDay() - 1, vehicleType),
      ]);
      setHealth(healthData);
      setRoutes(routeData.routes);
      setSelectedRouteIndex(routeData.best_route_index);
      setWeather(routeData.weather);
      setPrediction(predictData);
      if (routeData.resolved_origin) {
        setOrigin(routeData.resolved_origin);
      }
      if (routeData.resolved_destination) {
        setDestination(routeData.resolved_destination);
      }
      setRerouteMessage(routeData.reroute_message || "");
    } catch (error) {
      setInputError(error?.response?.data?.detail || "Could not calculate the route for the selected Bengaluru locations.");
    } finally {
      setLoading(false);
    }
  }

  async function searchOrigin(query) {
    if (!query.trim()) return;
    const places = await fetchPlaces(query);
    setOriginSuggestions(places);
  }

  async function searchDestination(query) {
    if (!query.trim()) return;
    const places = await fetchPlaces(query);
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

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Entry-level capstone</p>
          <h1>Smart Traffic Prediction and Route Optimization</h1>
          <p className="hero-copy">
            Localhost dashboard with route comparison, traffic prediction, weather-aware rerouting,
            eco scoring, and vehicle-specific recommendations.
          </p>
        </div>
        <div className="hero-stats glass">
          <span>API: {health?.status || "not checked"}</span>
          <span>Model: {health?.artifact_loaded ? "Colab export loaded" : "fallback demo mode"}</span>
          <span>Polling: every 30 seconds</span>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
          >
            {theme === "light" ? "Dark mode" : "Light mode"}
          </button>
        </div>
      </section>

      <div className="layout">
        <div className="left-column">
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
            invalidOrigin={origin.label.trim() !== "" && origin.lat === "" && origin.lng === ""}
            invalidDestination={destination.label.trim() !== "" && destination.lat === "" && destination.lng === ""}
            originSuggestions={originSuggestions}
            destinationSuggestions={destinationSuggestions}
            onOriginSearch={searchOrigin}
            onDestinationSearch={searchDestination}
          />
          {inputError ? <section className="panel glass input-error-banner">{inputError}</section> : null}
          <WeatherBadge weather={weather} />
          {prediction ? (
            <section className="panel glass">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Traffic prediction</p>
                  <h2>{prediction.requested_location || prediction.area_name}</h2>
                </div>
                <span className={`pill congestion-${prediction.congestion_bucket}`}>
                  {prediction.congestion_bucket}
                </span>
              </div>
              <div className="route-grid">
                <span>Volume: {prediction.predicted_traffic_volume}</span>
                <span>Speed: {prediction.predicted_average_speed} km/h</span>
                <span>Model: {prediction.model_source}</span>
              </div>
            </section>
          ) : null}
          <section className="routes-stack">
            {routes.map((route, index) => (
              <RouteCard
                key={route.route_index}
                route={route}
                selected={index === selectedRouteIndex}
                onSelect={() => setSelectedRouteIndex(index)}
              />
            ))}
          </section>
        </div>

        <div className="right-column">
          <MapView
            origin={origin}
            destination={destination}
            routes={routes}
            selectedRouteIndex={selectedRouteIndex}
          />
        </div>
      </div>

      <RerouteAlert
        message={rerouteMessage}
        onAccept={() => setSelectedRouteIndex(routes.findIndex((route) => route.recommended) || 0)}
        onDismiss={() => setRerouteMessage("")}
      />
    </main>
  );
}
