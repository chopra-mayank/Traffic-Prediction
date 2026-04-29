from __future__ import annotations

from typing import Any

import httpx

from ..config import APP_USER_AGENT, OSRM_BASE_URL
from .emission_service import calc_emissions
from .weather_service import get_weather_penalty


def _speed_to_congestion(speed_kmh: float) -> str:
    if speed_kmh >= 35:
        return "low"
    if speed_kmh >= 20:
        return "medium"
    return "high"


class RoutingService:
    def __init__(self) -> None:
        self._headers = {"User-Agent": APP_USER_AGENT}

    async def compute_routes(
        self,
        origin: dict[str, Any],
        destination: dict[str, Any],
        weather: dict[str, Any],
        predicted_speed: float,
        congestion_level: str,
        vehicle_type: str,
        optimize_for: str,
    ) -> list[dict[str, Any]]:
        coordinates = f"{origin['lng']},{origin['lat']};{destination['lng']},{destination['lat']}"
        async with httpx.AsyncClient(timeout=20, headers=self._headers) as client:
            response = await client.get(
                f"{OSRM_BASE_URL}/{coordinates}",
                params={
                    "alternatives": 2,
                    "overview": "full",
                    "geometries": "geojson",
                    "steps": "false",
                },
            )
            response.raise_for_status()
            payload = response.json()

        routes_payload = payload.get("routes", [])
        if not routes_payload:
            return []

        weather_penalty = get_weather_penalty(
            weather.get("precipitation", 0.0),
            weather.get("wind_speed", 0.0),
            weather.get("visibility", 4000.0),
        )
        vehicle_factor = {"car": 1.0, "bike": 0.88, "truck": 1.25}.get(vehicle_type, 1.0)
        labels = ["Fastest", "Balanced", "Scenic"]

        normalized_routes: list[dict[str, Any]] = []
        for index, route in enumerate(routes_payload[:3]):
            geometry = route.get("geometry", {}).get("coordinates", [])
            coordinates_latlng = [[coord[1], coord[0]] for coord in geometry]
            distance_km = route.get("distance", 0.0) / 1000.0
            base_minutes = route.get("duration", 0.0) / 60.0
            adjusted_minutes = base_minutes * weather_penalty * vehicle_factor
            avg_speed = distance_km / max(adjusted_minutes / 60.0, 0.1)
            co2 = calc_emissions(distance_km, avg_speed, vehicle_type)
            if optimize_for == "eco":
                adjusted_minutes *= 1.05
            normalized_routes.append(
                {
                    "route_index": index,
                    "label": labels[index] if index < len(labels) else f"Route {index + 1}",
                    "coordinates": coordinates_latlng,
                    "path_nodes": [origin["label"], destination["label"]],
                    "distance_km": round(distance_km, 2),
                    "travel_time_min": round(adjusted_minutes, 2),
                    "co2_grams": round(co2, 2),
                    "congestion_level": _speed_to_congestion(avg_speed),
                }
            )

        ranking_key = {
            "time": "travel_time_min",
            "distance": "distance_km",
            "eco": "co2_grams",
        }.get(optimize_for, "travel_time_min")
        best_index = min(range(len(normalized_routes)), key=lambda idx: normalized_routes[idx][ranking_key])
        fastest = min(route["travel_time_min"] for route in normalized_routes)
        greenest = min(route["co2_grams"] for route in normalized_routes)
        for route in normalized_routes:
            route["recommended"] = route["route_index"] == best_index
            route["eco_badge"] = route["co2_grams"] == greenest
            route["savings_vs_fastest_min"] = round(route["travel_time_min"] - fastest, 2)
        return normalized_routes
