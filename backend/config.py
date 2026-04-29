from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = BASE_DIR / "backend" / "saved_models"
DB_PATH = BASE_DIR / "traffic_app.db"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = os.getenv(
    "OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5/weather"
)
NOMINATIM_BASE_URL = os.getenv(
    "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org/search"
)
OSRM_BASE_URL = os.getenv(
    "OSRM_BASE_URL", "https://router.project-osrm.org/route/v1/driving"
)
APP_USER_AGENT = os.getenv("APP_USER_AGENT", "smart-traffic-capstone/1.0")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

BANGALORE_DATA_CANDIDATES = [
    RAW_DIR / "Banglore_traffic_Dataset.csv",
    BASE_DIR / "Banglore_traffic_Dataset.csv",
]

DELHI_TIME_DATA_CANDIDATES = [
    RAW_DIR / "2024_week_day_time_city.csv",
    BASE_DIR / "weekday_stats" / "2024_week_day_time_city.csv",
]
