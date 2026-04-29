from __future__ import annotations

from datetime import datetime
from math import isfinite

import httpx

from ..config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL
from ..database import get_connection


class WeatherService:
    def __init__(self) -> None:
        self._fallback = {
            "condition": "Clear",
            "temperature": 27.0,
            "precipitation": 0.0,
            "wind_speed": 8.0,
            "visibility": 4000.0,
            "source": "fallback",
        }

    async def get_current_weather(self, city: str, lat: float, lng: float) -> dict:
        if OPENWEATHER_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        OPENWEATHER_BASE_URL,
                        params={
                            "lat": lat,
                            "lon": lng,
                            "appid": OPENWEATHER_API_KEY,
                            "units": "metric",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                weather = {
                    "city": city,
                    "condition": payload["weather"][0]["main"],
                    "temperature": float(payload["main"]["temp"]),
                    "precipitation": float(payload.get("rain", {}).get("1h", 0.0)),
                    "wind_speed": float(payload.get("wind", {}).get("speed", 0.0)),
                    "visibility": float(payload.get("visibility", 4000.0)),
                    "source": "openweathermap",
                }
                self._cache_weather(weather)
                return weather
            except Exception:
                pass

        cached = self._latest_cached(city)
        if cached:
            return cached

        return {"city": city, **self._fallback}

    def _cache_weather(self, weather: dict) -> None:
        if not isfinite(weather["temperature"]):
            return
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO weather_cache
                (city, timestamp, temperature, precipitation, wind_speed, visibility, condition)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    weather["city"],
                    datetime.utcnow().isoformat(),
                    weather["temperature"],
                    weather["precipitation"],
                    weather["wind_speed"],
                    weather["visibility"],
                    weather["condition"],
                ),
            )

    def _latest_cached(self, city: str) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT city, temperature, precipitation, wind_speed, visibility, condition, timestamp
                FROM weather_cache
                WHERE city = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (city,),
            ).fetchone()
        if row is None:
            return None
        return {
            "city": row["city"],
            "condition": row["condition"],
            "temperature": row["temperature"],
            "precipitation": row["precipitation"],
            "wind_speed": row["wind_speed"],
            "visibility": row["visibility"],
            "source": "sqlite-cache",
        }


def get_weather_penalty(precipitation: float, wind_speed: float, visibility: float) -> float:
    penalty = 1.0
    if precipitation > 5:
        penalty *= 1.3
    elif precipitation > 1:
        penalty *= 1.1
    if wind_speed > 40:
        penalty *= 1.1
    if visibility < 1000:
        penalty *= 1.2
    return penalty
