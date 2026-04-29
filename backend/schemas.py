from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


VehicleType = Literal["car", "bike", "truck"]
OptimizeFor = Literal["time", "distance", "eco"]


class Coordinate(BaseModel):
    lat: float
    lng: float
    label: str | None = None


class RouteRequest(BaseModel):
    origin_name: str | None = None
    destination_name: str | None = None
    origin_lat: float | None = Field(default=None, ge=-90, le=90)
    origin_lng: float | None = Field(default=None, ge=-180, le=180)
    dest_lat: float | None = Field(default=None, ge=-90, le=90)
    dest_lng: float | None = Field(default=None, ge=-180, le=180)
    vehicle_type: VehicleType = "car"
    optimize_for: OptimizeFor = "time"
    current_route_index: int | None = None
    current_lat: float | None = None
    current_lng: float | None = None


class PredictResponse(BaseModel):
    area_name: str
    requested_location: str | None = None
    hour: int
    predicted_traffic_volume: float
    predicted_average_speed: float
    congestion_bucket: str
    model_source: str
    notes: list[str]


class WeatherResponse(BaseModel):
    city: str
    condition: str
    temperature: float
    precipitation: float
    wind_speed: float
    visibility: float
    source: str


class RouteSummary(BaseModel):
    route_index: int
    label: str
    coordinates: list[list[float]]
    path_nodes: list[str]
    distance_km: float
    travel_time_min: float
    co2_grams: float
    congestion_level: str
    recommended: bool = False
    eco_badge: bool = False
    savings_vs_fastest_min: float = 0


class RouteResponse(BaseModel):
    routes: list[RouteSummary]
    predicted_traffic: str
    weather: WeatherResponse
    best_route_index: int
    resolved_origin: Coordinate | None = None
    resolved_destination: Coordinate | None = None
    reroute_available: bool = False
    reroute_message: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
