from __future__ import annotations

import csv
from pathlib import Path

from ..config import BANGALORE_DATA_CANDIDATES
from ..database import get_connection


def seed_bangalore_readings() -> int:
    source = next((path for path in BANGALORE_DATA_CANDIDATES if path.exists()), None)
    if source is None:
        return 0

    with get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) AS count FROM traffic_readings").fetchone()
        if existing and existing["count"] > 0:
            return int(existing["count"])

        with Path(source).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = [
                (
                    row["Date"],
                    row["Area Name"],
                    row["Road/Intersection Name"],
                    float(row["Traffic Volume"]),
                    float(row["Average Speed"]),
                    row["Congestion Level"],
                    float(row["Travel Time Index"]),
                )
                for row in reader
            ]

        conn.executemany(
            """
            INSERT INTO traffic_readings
            (recorded_at, hour, area_name, road_name, traffic_volume, average_speed, congestion_level, travel_time_index)
            VALUES (?, CAST(strftime('%H', ?) AS INTEGER), ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    recorded_at,
                    recorded_at,
                    area_name,
                    road_name,
                    traffic_volume,
                    average_speed,
                    congestion_level,
                    travel_time_index,
                )
                for (
                    recorded_at,
                    area_name,
                    road_name,
                    traffic_volume,
                    average_speed,
                    congestion_level,
                    travel_time_index,
                ) in rows
            ],
        )
        return len(rows)
