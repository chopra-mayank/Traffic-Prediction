from __future__ import annotations


EMISSION_FACTORS = {
    "car": 150.0,
    "bike": 70.0,
    "truck": 1200.0,
}


def calc_emissions(distance_km: float, avg_speed: float, vehicle_type: str = "car") -> float:
    factor = EMISSION_FACTORS.get(vehicle_type, EMISSION_FACTORS["car"])
    speed_penalty = 1.5 if avg_speed < 20 else 1.2 if avg_speed < 30 else 1.0
    return round(distance_km * factor * speed_penalty, 2)
