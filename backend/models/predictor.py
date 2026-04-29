from __future__ import annotations

import csv
import json
import pickle
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

try:
    import joblib
except ModuleNotFoundError:  # pragma: no cover - optional until dependencies are installed
    joblib = None
try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - optional until dependencies are installed
    pd = None

from ..config import BANGALORE_DATA_CANDIDATES, MODEL_DIR


class TrafficPredictor:
    def __init__(self) -> None:
        self.model_path = MODEL_DIR / "xgboost_model.pkl"
        self.meta_path = MODEL_DIR / "model_metadata.json"
        self.load_error: str | None = None
        self.area_stats, self.area_templates = self._load_area_stats()
        self.model = self._load_pickle(self.model_path)
        self.metadata = self._load_metadata()

    def predict_for_area(
        self,
        area_name: str,
        hour: int,
        day: int,
        weather: dict[str, Any] | None = None,
        vehicle_type: str = "car",
        requested_location: str | None = None,
    ) -> dict[str, Any]:
        weather = weather or {}
        baseline = self.area_stats.get(area_name) or self.area_stats.get("city_average") or {
            "traffic_volume": 20000.0,
            "average_speed": 32.0,
            "congestion_level": 55.0,
        }

        features = {
            "hour": hour,
            "day_of_week": day,
            "is_weekend": 1 if day >= 5 else 0,
            "temperature": float(weather.get("temperature", 27.0)),
            "precipitation": float(weather.get("precipitation", 0.0)),
            "wind_speed": float(weather.get("wind_speed", 8.0)),
            "vehicle_type": vehicle_type,
        }

        if self.model is not None and hasattr(self.model, "predict"):
            try:
                frame = self._build_inference_frame(area_name, hour, day, weather)
                predicted_volume = float(self.model.predict(frame)[0])
                inferred_speed = max(8.0, baseline["average_speed"] - predicted_volume / 2500.0)
                congestion_score = min(100.0, max(0.0, predicted_volume / 800.0))
                return self._response(
                    area_name,
                    requested_location,
                    hour,
                    predicted_volume,
                    inferred_speed,
                    congestion_score,
                    "trained-artifact",
                    ["Loaded exported model artifact from Colab."],
                )
            except Exception as exc:
                self.load_error = f"Predict failed: {exc}"

        weather_penalty = 1.0 + min(float(weather.get("precipitation", 0.0)) / 20.0, 0.35)
        peak_penalty = 1.25 if hour in {8, 9, 10, 17, 18, 19, 20} else 1.0
        weekend_factor = 0.88 if day >= 5 else 1.0
        vehicle_factor = {"car": 1.0, "bike": 0.9, "truck": 1.2}.get(vehicle_type, 1.0)

        predicted_volume = baseline["traffic_volume"] * peak_penalty * weather_penalty * weekend_factor * vehicle_factor
        predicted_speed = baseline["average_speed"] / (peak_penalty * weather_penalty)
        congestion_score = min(
            100.0,
            baseline["congestion_level"] * peak_penalty * weather_penalty / weekend_factor,
        )
        return self._response(
            area_name,
            requested_location,
            hour,
            predicted_volume,
            predicted_speed,
            congestion_score,
            "heuristic-fallback",
            [
                "Using dataset-derived heuristics until Colab-trained artifacts are copied into backend/saved_models/.",
                "This still enables the routing, dashboard, and API user stories locally.",
            ],
        )

    def _response(
        self,
        area_name: str,
        requested_location: str | None,
        hour: int,
        predicted_volume: float,
        predicted_speed: float,
        congestion_score: float,
        model_source: str,
        notes: list[str],
    ) -> dict[str, Any]:
        return {
            "area_name": area_name,
            "requested_location": requested_location,
            "hour": hour,
            "predicted_traffic_volume": round(predicted_volume, 2),
            "predicted_average_speed": round(max(predicted_speed, 5.0), 2),
            "congestion_bucket": self._bucket(congestion_score),
            "model_source": model_source,
            "notes": notes,
        }

    def _load_area_stats(self) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, Any]]]:
        rows: list[dict[str, str]] = []
        source = next((path for path in BANGALORE_DATA_CANDIDATES if path.exists()), None)
        if source is None:
            return (
                {
                    "city_average": {
                        "traffic_volume": 20000.0,
                        "average_speed": 32.0,
                        "congestion_level": 55.0,
                    }
                },
                {
                    "city_average": {
                        "Area Name": "MG Road",
                        "Road/Intersection Name": "100 Feet Road",
                        "Weather Conditions": "Clear",
                        "Average Speed": 32.0,
                        "Travel Time Index": 1.3,
                        "Road Capacity Utilization": 65.0,
                        "Incident Reports": 0.0,
                        "Public Transport Usage": 45.0,
                        "Pedestrian and Cyclist Count": 120.0,
                    }
                },
            )
        with source.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows.extend(reader)

        grouped: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: {
                "traffic_volume": [],
                "average_speed": [],
                "congestion_level": [],
            }
        )
        for row in rows:
            area = row["Area Name"].strip()
            grouped[area]["traffic_volume"].append(float(row["Traffic Volume"]))
            grouped[area]["average_speed"].append(float(row["Average Speed"]))
            grouped[area]["congestion_level"].append(float(row["Congestion Level"]))

        stats: dict[str, dict[str, float]] = {}
        templates: dict[str, dict[str, Any]] = {}
        all_volume: list[float] = []
        all_speed: list[float] = []
        all_congestion: list[float] = []
        for area, values in grouped.items():
            stats[area] = {
                "traffic_volume": mean(values["traffic_volume"]),
                "average_speed": mean(values["average_speed"]),
                "congestion_level": mean(values["congestion_level"]),
            }
            all_volume.extend(values["traffic_volume"])
            all_speed.extend(values["average_speed"])
            all_congestion.extend(values["congestion_level"])
            area_rows = [row for row in rows if row["Area Name"].strip() == area]
            if area_rows:
                first = area_rows[0]
                templates[area] = {
                    "Area Name": first["Area Name"],
                    "Road/Intersection Name": first["Road/Intersection Name"],
                    "Weather Conditions": first["Weather Conditions"],
                    "Average Speed": mean(float(row["Average Speed"]) for row in area_rows),
                    "Travel Time Index": mean(float(row["Travel Time Index"]) for row in area_rows),
                    "Road Capacity Utilization": mean(float(row["Road Capacity Utilization"]) for row in area_rows),
                    "Incident Reports": mean(float(row["Incident Reports"]) for row in area_rows),
                    "Public Transport Usage": mean(float(row["Public Transport Usage"]) for row in area_rows),
                    "Pedestrian and Cyclist Count": mean(float(row["Pedestrian and Cyclist Count"]) for row in area_rows),
                }

        stats["city_average"] = {
            "traffic_volume": mean(all_volume),
            "average_speed": mean(all_speed),
            "congestion_level": mean(all_congestion),
        }
        templates["city_average"] = {
            "Area Name": "MG Road",
            "Road/Intersection Name": "100 Feet Road",
            "Weather Conditions": "Clear",
            "Average Speed": mean(all_speed),
            "Travel Time Index": mean(float(row["Travel Time Index"]) for row in rows),
            "Road Capacity Utilization": mean(float(row["Road Capacity Utilization"]) for row in rows),
            "Incident Reports": mean(float(row["Incident Reports"]) for row in rows),
            "Public Transport Usage": mean(float(row["Public Transport Usage"]) for row in rows),
            "Pedestrian and Cyclist Count": mean(float(row["Pedestrian and Cyclist Count"]) for row in rows),
        }
        return stats, templates

    @staticmethod
    def _bucket(congestion_score: float) -> str:
        if congestion_score >= 75:
            return "high"
        if congestion_score >= 40:
            return "medium"
        return "low"

    def _load_pickle(self, path: Path) -> Any:
        if not path.exists():
            return None
        if joblib is not None:
            try:
                return joblib.load(path)
            except Exception as exc:
                self.load_error = f"joblib load failed: {exc}"
        try:
            with path.open("rb") as handle:
                return pickle.load(handle)
        except Exception as exc:
            self.load_error = f"pickle load failed: {exc}"
            return None

    def _build_inference_frame(
        self,
        area_name: str,
        hour: int,
        day: int,
        weather: dict[str, Any] | None,
    ):
        if pd is None:
            raise RuntimeError("pandas is required for trained-model inference")
        weather = weather or {}
        template = self.area_templates.get(area_name) or self.area_templates["city_average"]
        month = datetime.utcnow().month
        weather_condition = str(weather.get("condition", template["Weather Conditions"]))
        if weather.get("precipitation", 0.0) > 1:
            weather_condition = "Rain"

        row = {
            "Area Name": area_name if area_name in self.area_templates else template["Area Name"],
            "Road/Intersection Name": template["Road/Intersection Name"],
            "Weather Conditions": weather_condition,
            "hour": hour,
            "day_of_week": day,
            "month": month,
            "is_weekend": 1 if day >= 5 else 0,
            "Average Speed": template["Average Speed"],
            "Travel Time Index": template["Travel Time Index"],
            "Road Capacity Utilization": template["Road Capacity Utilization"],
            "Incident Reports": template["Incident Reports"],
            "Public Transport Usage": template["Public Transport Usage"],
            "Pedestrian and Cyclist Count": template["Pedestrian and Cyclist Count"],
        }
        return pd.DataFrame([row])

    def _load_metadata(self) -> dict[str, Any]:
        if not self.meta_path.exists():
            return {
                "created_at": datetime.utcnow().isoformat(),
                "artifact_present": False,
            }
        try:
            return json.loads(self.meta_path.read_text(encoding="utf-8"))
        except Exception:
            return {"artifact_present": False}
