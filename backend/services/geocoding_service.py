from __future__ import annotations

from typing import Any

import httpx

from ..config import APP_USER_AGENT, NOMINATIM_BASE_URL
from .place_service import KNOWN_BANGALORE_PLACES, normalize_place_name, resolve_known_place


class GeocodingService:
    def __init__(self) -> None:
        self._headers = {"User-Agent": APP_USER_AGENT}
        self._viewbox = "77.4600,13.1737,77.7800,12.7343"

    async def search_places(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        known = [
            {"name": place.name, "lat": place.lat, "lng": place.lng, "source": "builtin"}
            for place in KNOWN_BANGALORE_PLACES
            if normalize_place_name(query) in normalize_place_name(place.name)
        ]
        seen = {normalize_place_name(item["name"]) for item in known}
        results.extend(known)

        if query.strip():
            try:
                async with httpx.AsyncClient(timeout=10, headers=self._headers) as client:
                    response = await client.get(
                        NOMINATIM_BASE_URL,
                        params={
                            "q": f"{query}, Bengaluru, Karnataka, India",
                            "format": "jsonv2",
                            "limit": limit,
                            "countrycodes": "in",
                            "viewbox": self._viewbox,
                            "bounded": 1,
                            "addressdetails": 1,
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                for item in payload:
                    display = item.get("display_name", "")
                    name = display.split(",")[0] if display else query
                    normalized = normalize_place_name(name)
                    if normalized in seen:
                        continue
                    seen.add(normalized)
                    results.append(
                        {
                            "name": name,
                            "lat": float(item["lat"]),
                            "lng": float(item["lon"]),
                            "source": "nominatim",
                            "display_name": display,
                        }
                    )
                    if len(results) >= limit:
                        break
            except Exception:
                pass

        return results[:limit]

    async def resolve_location(
        self,
        name: str | None,
        lat: float | None,
        lng: float | None,
    ) -> dict[str, Any]:
        if lat is not None and lng is not None:
            return {
                "label": name or "Selected location",
                "lat": float(lat),
                "lng": float(lng),
                "source": "manual",
            }

        if name:
            known = resolve_known_place(name)
            if known:
                return {
                    "label": known.name,
                    "lat": known.lat,
                    "lng": known.lng,
                    "source": "builtin",
                }

            matches = await self.search_places(name, limit=1)
            if matches:
                match = matches[0]
                return {
                    "label": match["name"],
                    "lat": float(match["lat"]),
                    "lng": float(match["lng"]),
                    "source": match.get("source", "nominatim"),
                }

        raise ValueError("Unable to resolve location. Enter a Bengaluru place name or valid coordinates.")
