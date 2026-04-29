from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import networkx as nx

from ..services.emission_service import calc_emissions
from ..services.weather_service import get_weather_penalty


@dataclass(frozen=True)
class Node:
    name: str
    lat: float
    lng: float
    area: str


class TrafficRouter:
    def __init__(self) -> None:
        self.nodes = self._build_nodes()
        self.graph = self._build_graph(self.nodes)

    def compute_routes(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        weather: dict[str, Any],
        predicted_speed: float,
        congestion_level: str,
        vehicle_type: str,
        optimize_for: str,
    ) -> list[dict[str, Any]]:
        origin_node = self._nearest_node(*origin)
        destination_node = self._nearest_node(*destination)
        graph = self.graph.copy()
        self._apply_dynamic_weights(graph, weather, predicted_speed, vehicle_type)

        routes = []
        path_iter = nx.shortest_simple_paths(graph, origin_node.name, destination_node.name, weight=self._weight_key(optimize_for))
        for idx, path in enumerate(path_iter):
            if idx >= 3:
                break
            distance = 0.0
            travel_time = 0.0
            co2 = 0.0
            coordinates = []
            for i in range(len(path) - 1):
                edge = graph[path[i]][path[i + 1]]
                distance += edge["distance"]
                travel_time += edge["travel_time"]
                co2 += edge["co2"]
                if i == 0:
                    coordinates.append([graph.nodes[path[i]]["lat"], graph.nodes[path[i]]["lng"]])
                coordinates.append([graph.nodes[path[i + 1]]["lat"], graph.nodes[path[i + 1]]["lng"]])
            routes.append(
                {
                    "route_index": idx,
                    "label": ["Fastest", "Balanced", "Scenic"][idx] if idx < 3 else f"Route {idx + 1}",
                    "coordinates": coordinates,
                    "path_nodes": path,
                    "distance_km": round(distance, 2),
                    "travel_time_min": round(travel_time, 2),
                    "co2_grams": round(co2, 2),
                    "congestion_level": congestion_level,
                }
            )

        if not routes:
            return []

        fastest = min(route["travel_time_min"] for route in routes)
        greenest = min(route["co2_grams"] for route in routes)
        best_index = min(range(len(routes)), key=lambda i: routes[i][self._summary_key(optimize_for)])
        for route in routes:
            route["recommended"] = route["route_index"] == best_index
            route["eco_badge"] = route["co2_grams"] == greenest
            route["savings_vs_fastest_min"] = round(route["travel_time_min"] - fastest, 2)
        return routes

    @staticmethod
    def _summary_key(optimize_for: str) -> str:
        return {
            "time": "travel_time_min",
            "distance": "distance_km",
            "eco": "co2_grams",
        }.get(optimize_for, "travel_time_min")

    @staticmethod
    def _weight_key(optimize_for: str) -> str:
        return {
            "time": "travel_time",
            "distance": "distance",
            "eco": "co2",
        }.get(optimize_for, "travel_time")

    def _apply_dynamic_weights(
        self,
        graph: nx.DiGraph,
        weather: dict[str, Any],
        predicted_speed: float,
        vehicle_type: str,
    ) -> None:
        penalty = get_weather_penalty(
            weather.get("precipitation", 0.0),
            weather.get("wind_speed", 0.0),
            weather.get("visibility", 4000.0),
        )
        vehicle_factor = {"car": 1.0, "bike": 0.82, "truck": 1.35}.get(vehicle_type, 1.0)
        for u, v, data in graph.edges(data=True):
            edge_speed = max(8.0, min(data["base_speed"], predicted_speed)) / vehicle_factor
            if vehicle_type == "bike" and data.get("road_type") == "highway":
                edge_speed *= 0.6
            travel_time = (data["distance"] / max(edge_speed, 5.0)) * 60.0 * penalty
            data["travel_time"] = round(travel_time, 2)
            data["co2"] = calc_emissions(data["distance"], edge_speed, vehicle_type)

    def _nearest_node(self, lat: float, lng: float) -> Node:
        return min(self.nodes, key=lambda node: sqrt((node.lat - lat) ** 2 + (node.lng - lng) ** 2))

    def _build_graph(self, nodes: list[Node]) -> nx.DiGraph:
        graph = nx.DiGraph()
        for node in nodes:
            graph.add_node(node.name, lat=node.lat, lng=node.lng, area=node.area)
        edges = [
            ("MG Road", "Indiranagar", 4.6, 34, "arterial"),
            ("Indiranagar", "Koramangala", 6.8, 28, "urban"),
            ("Koramangala", "Silk Board", 5.2, 24, "arterial"),
            ("Silk Board", "Electronic City", 9.7, 38, "highway"),
            ("MG Road", "Richmond Circle", 3.2, 30, "urban"),
            ("Richmond Circle", "Jayanagar", 5.7, 26, "urban"),
            ("Jayanagar", "BTM Layout", 4.0, 27, "urban"),
            ("BTM Layout", "Silk Board", 3.5, 22, "urban"),
            ("Indiranagar", "Marathahalli", 7.4, 31, "arterial"),
            ("Indiranagar", "CV Raman Nagar", 2.9, 27, "urban"),
            ("CV Raman Nagar", "Marathahalli", 6.4, 30, "arterial"),
            ("CV Raman Nagar", "MG Road", 5.8, 28, "urban"),
            ("Marathahalli", "Bellandur", 4.1, 26, "urban"),
            ("Bellandur", "Electronic City", 11.2, 35, "highway"),
            ("Koramangala", "HSR Layout", 4.4, 29, "urban"),
            ("HSR Layout", "Electronic City", 8.9, 33, "arterial"),
            ("Marathahalli", "Whitefield", 7.0, 32, "arterial"),
            ("Whitefield", "Electronic City", 18.5, 36, "highway"),
        ]
        for source, target, distance, base_speed, road_type in edges:
            graph.add_edge(
                source,
                target,
                distance=distance,
                base_speed=base_speed,
                road_type=road_type,
                travel_time=(distance / base_speed) * 60.0,
                co2=calc_emissions(distance, base_speed),
            )
            graph.add_edge(
                target,
                source,
                distance=distance,
                base_speed=base_speed * 0.95,
                road_type=road_type,
                travel_time=(distance / (base_speed * 0.95)) * 60.0,
                co2=calc_emissions(distance, base_speed * 0.95),
            )
        return graph

    @staticmethod
    def _build_nodes() -> list[Node]:
        return [
            Node("MG Road", 12.9756, 77.6050, "Central Bangalore"),
            Node("Indiranagar", 12.9784, 77.6408, "Indiranagar"),
            Node("Koramangala", 12.9352, 77.6245, "Koramangala"),
            Node("Silk Board", 12.9176, 77.6237, "South Bangalore"),
            Node("Electronic City", 12.8399, 77.6770, "Electronic City"),
            Node("Richmond Circle", 12.9611, 77.5983, "Central Bangalore"),
            Node("Jayanagar", 12.9250, 77.5938, "Jayanagar"),
            Node("BTM Layout", 12.9166, 77.6101, "BTM Layout"),
            Node("Marathahalli", 12.9591, 77.6974, "Marathahalli"),
            Node("Bellandur", 12.9279, 77.6762, "Bellandur"),
            Node("HSR Layout", 12.9116, 77.6474, "HSR Layout"),
            Node("CV Raman Nagar", 12.9854, 77.6639, "East Bangalore"),
            Node("Whitefield", 12.9698, 77.7499, "Whitefield"),
        ]
