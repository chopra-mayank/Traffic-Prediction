import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
});

export async function fetchHealth() {
  const { data } = await api.get("/health");
  return data;
}

export async function fetchPlaces(query = "") {
  const { data } = await api.get("/places", {
    params: query ? { query } : {},
  });
  return data.places;
}

export async function fetchWeather(city) {
  const { data } = await api.get(`/weather/${city}`);
  return data;
}

export async function fetchAreaPrediction(area, hour, day, vehicleType) {
  const { data } = await api.get(`/predict/${encodeURIComponent(area)}`, {
    params: { hour, day, vehicle_type: vehicleType },
  });
  return data;
}

export async function fetchOptimalRoutes(payload) {
  const { data } = await api.post("/routes/optimal", payload);
  return data;
}

export async function recalculateRoutes(payload) {
  const { data } = await api.post("/routes/recalculate", payload);
  return data;
}
