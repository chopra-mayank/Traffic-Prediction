from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from .config import DB_PATH


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS traffic_readings (
        id INTEGER PRIMARY KEY,
        recorded_at TEXT,
        hour INTEGER,
        area_name TEXT,
        road_name TEXT,
        traffic_volume REAL,
        average_speed REAL,
        congestion_level TEXT,
        travel_time_index REAL,
        source TEXT DEFAULT 'bangalore'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS weather_cache (
        id INTEGER PRIMARY KEY,
        city TEXT,
        timestamp TEXT,
        temperature REAL,
        precipitation REAL,
        wind_speed REAL,
        visibility REAL,
        condition TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS route_history (
        id INTEGER PRIMARY KEY,
        origin TEXT,
        destination TEXT,
        vehicle_type TEXT,
        optimize_for TEXT,
        travel_time REAL,
        distance REAL,
        co2_emissions REAL,
        created_at TEXT
    )
    """,
]

_shared_memory_conn: sqlite3.Connection | None = None


def _configure_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.row_factory = sqlite3.Row
    return conn


def _connect() -> sqlite3.Connection:
    global _shared_memory_conn
    try:
        conn = _configure_connection(sqlite3.connect(DB_PATH))
        conn.execute("CREATE TABLE IF NOT EXISTS __healthcheck (id INTEGER PRIMARY KEY)")
        return conn
    except sqlite3.OperationalError:
        if _shared_memory_conn is None:
            _shared_memory_conn = _configure_connection(
                sqlite3.connect("file:traffic_app_mem?mode=memory&cache=shared", uri=True)
            )
            _shared_memory_conn.execute("CREATE TABLE IF NOT EXISTS __healthcheck (id INTEGER PRIMARY KEY)")
        return _shared_memory_conn


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        if conn is not _shared_memory_conn:
            conn.close()


def init_db() -> None:
    with get_connection() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)


def seed_route_history(
    origin: str,
    destination: str,
    vehicle_type: str,
    optimize_for: str,
    travel_time: float,
    distance: float,
    co2_emissions: float,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO route_history
            (origin, destination, vehicle_type, optimize_for, travel_time, distance, co2_emissions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                origin,
                destination,
                vehicle_type,
                optimize_for,
                travel_time,
                distance,
                co2_emissions,
                datetime.utcnow().isoformat(),
            ),
        )
