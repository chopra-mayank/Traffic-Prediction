from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean


BASE_DIR = Path(__file__).resolve().parent.parent
BANGALORE_DIR = BASE_DIR / "data" / "bangalore"
RAW_DIR = BANGALORE_DIR / "raw"
PROCESSED_DIR = BANGALORE_DIR / "processed"


def _find_bangalore_csv() -> Path:
    candidate = RAW_DIR / "Banglore_traffic_Dataset.csv"
    if candidate.exists():
        return candidate
    raise FileNotFoundError("Banglore_traffic_Dataset.csv not found")


def preprocess() -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    source = _find_bangalore_csv()
    target = PROCESSED_DIR / "traffic_clean.csv"

    grouped_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = [row for row in reader if row["Traffic Volume"] and row["Average Speed"]]

    for row in rows:
        key = (row["Area Name"], row["Road/Intersection Name"])
        grouped_rows[key].append(row)

    for key in grouped_rows:
        grouped_rows[key].sort(key=lambda row: row["Date"])

    fieldnames = [
        "date",
        "area_name",
        "road_name",
        "traffic_volume",
        "average_speed",
        "travel_time_index",
        "congestion_level",
        "hour",
        "day_of_week",
        "month",
        "is_weekend",
        "weather_conditions",
        "traffic_volume_lag_1",
        "average_speed_lag_1",
        "traffic_volume_rolling_3",
        "average_speed_rolling_3",
    ]

    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for records in grouped_rows.values():
            vol_history: list[float] = []
            speed_history: list[float] = []
            for row in records:
                dt = datetime.fromisoformat(row["Date"])
                traffic_volume = float(row["Traffic Volume"])
                average_speed = float(row["Average Speed"])
                writer.writerow(
                    {
                        "date": row["Date"],
                        "area_name": row["Area Name"],
                        "road_name": row["Road/Intersection Name"],
                        "traffic_volume": traffic_volume,
                        "average_speed": average_speed,
                        "travel_time_index": float(row["Travel Time Index"]),
                        "congestion_level": float(row["Congestion Level"]),
                        "hour": dt.hour,
                        "day_of_week": dt.weekday(),
                        "month": dt.month,
                        "is_weekend": int(dt.weekday() >= 5),
                        "weather_conditions": row["Weather Conditions"],
                        "traffic_volume_lag_1": vol_history[-1] if vol_history else traffic_volume,
                        "average_speed_lag_1": speed_history[-1] if speed_history else average_speed,
                        "traffic_volume_rolling_3": round(mean(vol_history[-3:] or [traffic_volume]), 2),
                        "average_speed_rolling_3": round(mean(speed_history[-3:] or [average_speed]), 2),
                    }
                )
                vol_history.append(traffic_volume)
                speed_history.append(average_speed)
    return target


if __name__ == "__main__":
    path = preprocess()
    print(f"Processed dataset written to {path}")
