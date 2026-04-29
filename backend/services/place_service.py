from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lng: float


KNOWN_BANGALORE_PLACES = [
    Place("MG Road", 12.9756, 77.6050),
    Place("M.G. Road", 12.9756, 77.6050),
    Place("Indiranagar", 12.9784, 77.6408),
    Place("Koramangala", 12.9352, 77.6245),
    Place("Electronic City", 12.8399, 77.6770),
    Place("Marathahalli", 12.9591, 77.6974),
    Place("HSR Layout", 12.9116, 77.6474),
    Place("CV Raman Nagar", 12.9854, 77.6639),
    Place("Whitefield", 12.9698, 77.7499),
    Place("Bellandur", 12.9279, 77.6762),
    Place("Silk Board", 12.9176, 77.6237),
    Place("Jayanagar", 12.9250, 77.5938),
    Place("Richmond Circle", 12.9611, 77.5983),
    Place("BTM Layout", 12.9166, 77.6101),
    Place("Hebbal", 13.0358, 77.5970),
    Place("Yeshwanthpur", 13.0281, 77.5400),
]

MODEL_AREAS = [
    Place("M.G. Road", 12.9756, 77.6050),
    Place("Indiranagar", 12.9784, 77.6408),
    Place("Koramangala", 12.9352, 77.6245),
    Place("Electronic City", 12.8399, 77.6770),
    Place("Hebbal", 13.0358, 77.5970),
    Place("Whitefield", 12.9698, 77.7499),
    Place("Yeshwanthpur", 13.0281, 77.5400),
    Place("Jayanagar", 12.9250, 77.5938),
]


def normalize_place_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def resolve_known_place(name: str) -> Place | None:
    normalized = normalize_place_name(name)
    for place in KNOWN_BANGALORE_PLACES:
        if normalize_place_name(place.name) == normalized:
            return place
    return None


def nearest_model_area(lat: float, lng: float) -> Place:
    return min(MODEL_AREAS, key=lambda place: sqrt((place.lat - lat) ** 2 + (place.lng - lng) ** 2))
