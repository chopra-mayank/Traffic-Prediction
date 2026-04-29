from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_ORIGIN
from .database import init_db, seed_route_history
from .models.predictor import TrafficPredictor
from .schemas import PredictResponse, RouteRequest, RouteResponse, RouteSummary, WeatherResponse
from .services.data_loader import seed_bangalore_readings
from .services.geocoding_service import GeocodingService
from .services.place_service import KNOWN_BANGALORE_PLACES, nearest_model_area
from .services.routing_service import RoutingService
from .services.weather_service import WeatherService


app = FastAPI(title="Smart Traffic Prediction API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = TrafficPredictor()
weather_service = WeatherService()
geocoding_service = GeocodingService()
routing_service = RoutingService()


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    seed_bangalore_readings()


@app.get("/api/v1/health")
async def health() -> dict:
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "artifact_loaded": predictor.model is not None,
        "trained_model_active": predictor.model is not None and hasattr(predictor.model, "predict"),
        "artifact_path": str(predictor.model_path),
        "load_error": predictor.load_error,
    }


@app.get("/api/v1/places")
async def get_places(query: str | None = None) -> dict:
    places = [
        {"name": place.name, "lat": place.lat, "lng": place.lng}
        for place in KNOWN_BANGALORE_PLACES
    ]
    if query:
        places = await geocoding_service.search_places(query)
    return {"places": places}


@app.get("/api/v1/predict/{area_name}", response_model=PredictResponse)
async def predict_traffic(
    area_name: str,
    hour: int = Query(..., ge=0, le=23),
    day: int = Query(..., ge=0, le=6),
    vehicle_type: str = Query("car"),
) -> PredictResponse:
    try:
        resolved = await geocoding_service.resolve_location(area_name, None, None)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    model_area = nearest_model_area(resolved["lat"], resolved["lng"])
    weather = await weather_service.get_current_weather("Bangalore", resolved["lat"], resolved["lng"])
    return PredictResponse(
        **predictor.predict_for_area(
            model_area.name,
            hour,
            day,
            weather,
            vehicle_type,
            requested_location=resolved["label"],
        )
    )


@app.get("/api/v1/weather/{city}", response_model=WeatherResponse)
async def get_weather(city: str) -> WeatherResponse:
    coords = {
        "bangalore": (12.9716, 77.5946),
        "bengaluru": (12.9716, 77.5946),
        "delhi": (28.6139, 77.2090),
        "new delhi": (28.6139, 77.2090),
    }
    lat, lng = coords.get(city.lower(), (12.9716, 77.5946))
    weather = await weather_service.get_current_weather(city.title(), lat, lng)
    return WeatherResponse(**weather)


@app.post("/api/v1/routes/optimal", response_model=RouteResponse)
async def get_optimal_route(req: RouteRequest) -> RouteResponse:
    try:
        origin = await geocoding_service.resolve_location(req.origin_name, req.origin_lat, req.origin_lng)
        destination = await geocoding_service.resolve_location(req.destination_name, req.dest_lat, req.dest_lng)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    model_area = nearest_model_area(origin["lat"], origin["lng"])
    weather = await weather_service.get_current_weather("Bangalore", origin["lat"], origin["lng"])
    prediction = predictor.predict_for_area(
        model_area.name,
        datetime.now().hour,
        datetime.now().weekday(),
        weather,
        req.vehicle_type,
        requested_location=origin["label"],
    )
    try:
        routes = await routing_service.compute_routes(
            origin,
            destination,
            weather,
            prediction["predicted_average_speed"],
            prediction["congestion_bucket"],
            req.vehicle_type,
            req.optimize_for,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Routing service failed: {exc}") from exc
    if not routes:
        raise HTTPException(status_code=404, detail="No route found")
    best_route = next(route for route in routes if route["recommended"])
    seed_route_history(
        origin=f"{origin['label']} ({origin['lat']},{origin['lng']})",
        destination=f"{destination['label']} ({destination['lat']},{destination['lng']})",
        vehicle_type=req.vehicle_type,
        optimize_for=req.optimize_for,
        travel_time=best_route["travel_time_min"],
        distance=best_route["distance_km"],
        co2_emissions=best_route["co2_grams"],
    )
    return RouteResponse(
        routes=[RouteSummary(**route) for route in routes],
        predicted_traffic=prediction["congestion_bucket"],
        weather=WeatherResponse(**weather),
        best_route_index=best_route["route_index"],
        resolved_origin={"label": origin["label"], "lat": origin["lat"], "lng": origin["lng"]},
        resolved_destination={"label": destination["label"], "lat": destination["lat"], "lng": destination["lng"]},
        meta={
            "model_source": prediction["model_source"],
            "notes": prediction["notes"],
            "model_area": model_area.name,
        },
    )


@app.post("/api/v1/routes/compare", response_model=RouteResponse)
async def compare_routes(req: RouteRequest) -> RouteResponse:
    return await get_optimal_route(req)


@app.post("/api/v1/routes/recalculate", response_model=RouteResponse)
async def recalculate_route(req: RouteRequest) -> RouteResponse:
    response = await get_optimal_route(req)
    current_index = req.current_route_index or 0
    if current_index >= len(response.routes):
        current_index = 0
    current_route = response.routes[current_index]
    new_best = response.routes[response.best_route_index]
    savings = round(current_route.travel_time_min - new_best.travel_time_min, 2)
    if savings > 3:
        response.reroute_available = True
        response.reroute_message = f"Switching can save about {savings} minutes."
    return response
