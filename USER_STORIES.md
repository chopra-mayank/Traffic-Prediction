# User Story Coverage

This implementation covers the requested user stories with the following project pieces.

| User Story | Coverage in this repo |
|---|---|
| US-01 Data collection | Raw Bangalore dataset supported from repo root or `data/raw/`; Delhi dataset already recognized from top-level folders |
| US-02 Data preprocessing | `scripts/preprocess_data.py` creates `data/processed/traffic_clean.csv` |
| US-03 Feature engineering | Time, lag, rolling, and categorical-ready columns are produced in preprocessing; Colab notebook builds training features |
| US-04 Traffic prediction | `backend/models/predictor.py` supports exported model artifacts and heuristic fallback |
| US-05 Model evaluation | `notebooks/03_model_training_colab.ipynb` computes MAE, RMSE, and MAPE |
| US-06 Shortest path algorithm | `backend/models/router.py` uses weighted route search for optimal paths |
| US-07 Route API | `backend/main.py` exposes route, compare, predict, weather, reroute, and health endpoints |
| US-08 Route dashboard | `frontend/src/App.jsx` + `MapView.jsx` + `RouteCard.jsx` render the trip planner and map |
| US-09 Real-time updates | `frontend/src/hooks/usePolling.js` polls every 30 seconds |
| US-10 Map integration | `frontend/src/components/MapView.jsx` uses React Leaflet with OpenStreetMap |
| US-11 Data storage | `backend/database.py` + startup seed path + route history persistence |
| US-12 Model optimization | Colab notebook is structured for tuning and replacement of baseline artifact |
| US-13 UI enhancements | Responsive layout, dark mode toggle, loading state, map legend, route cards, preset autocomplete inputs |
| US-14 Weather-aware routing | `backend/services/weather_service.py` and dynamic edge penalties |
| US-15 Eco-friendly routes | CO2 scoring and eco badge in route results |
| US-18 Vehicle type selection | Vehicle selector affects prediction and route edge weighting |
| US-20 Alternative route trade-offs | Top 3 route options with time, distance, and CO2 displayed |
| US-22 Mid-trip optimal rerouting | Reroute endpoint and toast notification flow in frontend |

## Remaining manual step

The main post-scaffold task is training the real model in Google Colab and copying the exported artifact into `backend/saved_models/`.
