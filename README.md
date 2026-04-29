# Smart Traffic Prediction and Route Optimization

This project is an entry-level capstone for predicting traffic conditions in Bengaluru and recommending route options with live map-based routing. It combines:

- a trained traffic model based on the Bangalore Pulse dataset
- a FastAPI backend for prediction and routing
- a React + Leaflet dashboard for trip planning
- free external map/weather services for real-world usability

## Project Summary

The system allows a user to:

- enter an origin and destination in Bengaluru
- resolve real place names to coordinates
- fetch road routes between those coordinates
- estimate traffic conditions using the trained model
- compare fastest, distance-aware, and eco-aware route options
- receive rerouting suggestions when conditions change

The current model is trained on the Bangalore Pulse dataset and generalized to arbitrary Bengaluru inputs by mapping the typed place to the nearest supported training area.

## Tech Stack

- Frontend: React, Vite, React Leaflet
- Backend: FastAPI, Pydantic
- ML: scikit-learn pipeline + XGBoost regressor
- Data processing: pandas
- Database: SQLite
- Routing: OSRM
- Geocoding: Nominatim
- Weather: OpenWeatherMap fallback/cached weather flow

## End-to-End Workflow

### 1. Training workflow

- The Bangalore Pulse CSV is used as the main supervised training dataset.
- Training is done in Google Colab.
- The trained model is exported as `xgboost_model.pkl`.
- That model is copied into `backend/saved_models/`.
- On backend startup, the FastAPI app loads that artifact and uses it for inference.

### 2. Runtime prediction and routing workflow

1. The user enters origin and destination place names in the frontend.
2. The frontend calls the backend route endpoint.
3. The backend uses Nominatim to convert those place names into coordinates.
4. The backend maps the resolved coordinates to the nearest supported training area from the Bangalore dataset.
5. The backend fetches weather conditions for the resolved location.
6. The trained XGBoost pipeline predicts traffic volume for the nearest trained area using time and contextual features.
7. The backend calls OSRM to get road routes between origin and destination coordinates.
8. The backend adjusts travel time using:
- predicted traffic
- weather penalty
- vehicle type behavior
9. The backend returns route options, traffic level, weather data, and reroute information.
10. The frontend renders the route polylines, route cards, traffic prediction panel, and reroute alerts.

### Why external APIs are used

This project uses free external APIs because the training dataset does not contain a full street-by-street Bengaluru road graph.

- Nominatim is used to resolve arbitrary Bengaluru place names into coordinates.
- OSRM is used to compute real road routes between coordinates.
- OpenWeatherMap is used to bring weather into travel-time adjustment.

Without these services, the model could estimate traffic only for known training areas, but it could not behave like a real map application for arbitrary locations.

## Model Technique Used

The current trained model uses:

- `scikit-learn` `Pipeline`
- `ColumnTransformer`
- `OneHotEncoder`
- `XGBRegressor`

### Features used for training

- categorical:
  - `Area Name`
  - `Road/Intersection Name`
  - `Weather Conditions`
- temporal:
  - `hour`
  - `day_of_week`
  - `month`
  - `is_weekend`
- numerical traffic context:
  - `Average Speed`
  - `Travel Time Index`
  - `Road Capacity Utilization`
  - `Incident Reports`
  - `Public Transport Usage`
  - `Pedestrian and Cyclist Count`

### Target

- `Traffic Volume`

### Inference behavior

At runtime, arbitrary Bengaluru locations are snapped to the nearest trained area such as:

- `M.G. Road`
- `Indiranagar`
- `Koramangala`
- `Whitefield`
- `Hebbal`
- `Yeshwanthpur`
- `Jayanagar`
- `Electronic City`

This allows the trained model to support broader place input even though the original dataset is not citywide street-level data.

## Model Scores

The current Colab-trained XGBoost model produced:

- MAE: `4309.95`
- RMSE: `6758.82`
- MAPE: `13.03%`

These scores come from the trained Bangalore Pulse model that is currently loaded into the backend.

## API Endpoints

### Health and diagnostics

- `GET /api/v1/health`
  - Returns backend status, model load status, and artifact path

### Place and weather services

- `GET /api/v1/places?query=<text>`
  - Returns matching Bengaluru places from built-in data plus Nominatim results

- `GET /api/v1/weather/{city}`
  - Returns current weather data for a supported city lookup

### Traffic prediction

- `GET /api/v1/predict/{area_name}?hour=<0-23>&day=<0-6>&vehicle_type=<car|bike|truck>`
  - Predicts traffic conditions for a place input
  - Internally resolves the place and maps it to the nearest training area

### Routing

- `POST /api/v1/routes/optimal`
  - Resolves origin and destination
  - predicts traffic
  - computes route alternatives
  - returns the best route

- `POST /api/v1/routes/compare`
  - Same route computation flow, explicitly intended for route comparison

- `POST /api/v1/routes/recalculate`
  - Recomputes routes during navigation and returns a reroute suggestion if enough time is saved

## User Story to Code Mapping

This section is presentation-friendly and explicitly shows where each implemented story is handled.

### US-01 Data Collection

Purpose:
- load the Bangalore dataset and optional supporting datasets

Code:
- [scripts/preprocess_data.py](D:\Traffic\scripts\preprocess_data.py)
- [backend/services/data_loader.py](D:\Traffic\backend\services\data_loader.py)

### US-02 Data Preprocessing

Purpose:
- clean and transform the raw Bangalore traffic CSV
 
Code:
- [scripts/preprocess_data.py](D:\Traffic\scripts\preprocess_data.py)

### US-03 Feature Engineering

Purpose:
- create time-based and model-ready features

Code:
- [scripts/preprocess_data.py](D:\Traffic\scripts\preprocess_data.py)
- [notebooks/03_model_training_colab.ipynb](D:\Traffic\notebooks\03_model_training_colab.ipynb)

### US-04 Traffic Prediction Model

Purpose:
- load and run the trained XGBoost model

Code:
- [backend/models/predictor.py](D:\Traffic\backend\models\predictor.py)

### US-05 Model Evaluation

Purpose:
- measure model quality

Code:
- [notebooks/03_model_training_colab.ipynb](D:\Traffic\notebooks\03_model_training_colab.ipynb)
- [notebooks/04_model_evaluation.md](D:\Traffic\notebooks\04_model_evaluation.md)

### US-06 Shortest Path / Routing Logic

Purpose:
- compute route alternatives and optimize by time, distance, or eco score

Code:
- [backend/services/routing_service.py](D:\Traffic\backend\services\routing_service.py)

### US-07 Route API

Purpose:
- expose prediction and routing through REST endpoints

Code:
- [backend/main.py](D:\Traffic\backend\main.py)
- [backend/schemas.py](D:\Traffic\backend\schemas.py)

### US-08 Route Dashboard

Purpose:
- show search, prediction, map, and route results

Code:
- [frontend/src/App.jsx](D:\Traffic\frontend\src\App.jsx)
- [frontend/src/components/SearchPanel.jsx](D:\Traffic\frontend\src\components\SearchPanel.jsx)
- [frontend/src/components\RouteCard.jsx](D:\Traffic\frontend\src\components\RouteCard.jsx)
- [frontend/src/components\MapView.jsx](D:\Traffic\frontend\src\components\MapView.jsx)

### US-09 Real-Time Updates

Purpose:
- poll for refreshed route state

Code:
- [frontend/src/hooks/usePolling.js](D:\Traffic\frontend\src\hooks\usePolling.js)
- [backend/main.py](D:\Traffic\backend\main.py)

### US-10 Map Integration

Purpose:
- render route polylines and markers on a live map

Code:
- [frontend/src/components\MapView.jsx](D:\Traffic\frontend\src\components\MapView.jsx)

### US-11 Data Storage

Purpose:
- store weather cache and route history

Code:
- [backend/database.py](D:\Traffic\backend\database.py)
- [backend/services/data_loader.py](D:\Traffic\backend\services\data_loader.py)

### US-12 Model Optimization

Purpose:
- support tunable training in Colab

Code:
- [notebooks/03_model_training_colab.ipynb](D:\Traffic\notebooks\03_model_training_colab.ipynb)

### US-13 UI Enhancements

Purpose:
- improve usability and presentation quality

Code:
- [frontend/src/styles.css](D:\Traffic\frontend\src\styles.css)
- [frontend/src/App.jsx](D:\Traffic\frontend\src\App.jsx)
- [frontend/src/components/SearchPanel.jsx](D:\Traffic\frontend\src\components\SearchPanel.jsx)

Implemented UI features:
- dark mode toggle
- place suggestions
- responsive layout
- route comparison cards
- error handling banner

### US-14 Weather-Aware Routing

Purpose:
- adjust ETA using weather conditions

Code:
- [backend/services/weather_service.py](D:\Traffic\backend\services\weather_service.py)
- [backend/services/routing_service.py](D:\Traffic\backend\services\routing_service.py)

### US-15 Eco-Friendly Routes

Purpose:
- compare routes using CO2 estimates

Code:
- [backend/services/emission_service.py](D:\Traffic\backend\services\emission_service.py)
- [backend/services/routing_service.py](D:\Traffic\backend\services\routing_service.py)
- [frontend/src/components\RouteCard.jsx](D:\Traffic\frontend\src\components\RouteCard.jsx)

### US-18 Vehicle Type Selection

Purpose:
- support car, bike, and truck routing differences

Code:
- [frontend/src/components/SearchPanel.jsx](D:\Traffic\frontend\src\components\SearchPanel.jsx)
- [backend/services/routing_service.py](D:\Traffic\backend\services\routing_service.py)
- [backend/models/predictor.py](D:\Traffic\backend\models\predictor.py)

### US-20 Alternative Route Trade-offs

Purpose:
- return multiple route options with time, distance, and eco comparisons

Code:
- [backend/services/routing_service.py](D:\Traffic\backend\services\routing_service.py)
- [frontend/src/components\RouteCard.jsx](D:\Traffic\frontend\src\components\RouteCard.jsx)

### US-22 Mid-Trip Optimal Rerouting

Purpose:
- recommend a better route when enough time can be saved

Code:
- [backend/main.py](D:\Traffic\backend\main.py)
- [frontend/src/components\RerouteAlert.jsx](D:\Traffic\frontend\src\components\RerouteAlert.jsx)
- [frontend/src/hooks/usePolling.js](D:\Traffic\frontend\src\hooks\usePolling.js)

## External Services Used

### Nominatim

Used for:
- converting arbitrary Bengaluru place names to coordinates

Why needed:
- the model dataset does not contain every possible place name in Bengaluru

### OSRM

Used for:
- real road route generation between origin and destination

Why needed:
- the ML model predicts traffic, but does not contain a full navigable road graph

### OpenWeatherMap

Used for:
- weather lookup to influence route timing

Why needed:
- rainfall, wind, and visibility affect effective travel time

## Local Run Commands

### Backend

```powershell
uvicorn backend.main:app --reload
```

### Frontend

```powershell
cd frontend
npm run dev
```

## Future Work

1. Train a larger citywide Bengaluru model with segment-level geo features rather than nearest-area mapping.
2. Replace live routing dependencies with full offline OSM routing for no-runtime-API deployment.
3. Add route-history analytics and user trip history views.
4. Improve rerouting logic with live refresh confidence thresholds.
5. Add stronger geospatial validation for arbitrary locations outside Bengaluru.