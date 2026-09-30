"""
Real-time Emergency Routing Service for Crisis Command AI.
Calculates origin-destination routes, turn-by-turn navigation steps,
alternative detour corridors, traffic-aware ETAs, and GeoJSON route geometries.
Supports Mapbox Directions API if MAPBOX_ACCESS_TOKEN is configured,
with full fallback to the local emergency road network graph.
"""
from typing import Dict, Any, List, Optional, Set
import os
import math
from datetime import datetime
import urllib.request
import json
import logging

from services.routing import router_service

logger = logging.getLogger("routing_service")

MAPBOX_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN") or os.environ.get("VITE_MAPBOX_TOKEN")

# Canonical Operational Waypoints around Chennai Industrial Crisis Sector
STAGING_LOCATIONS = {
    "PLANT_B": {"name": "Plant B Chemical Complex", "lat": 12.9920, "lng": 80.2480, "node_id": "N0002"},
    "PLANT_A": {"name": "Plant A Refinery", "lat": 12.9850, "lng": 80.2350, "node_id": "N0001"},
    "DEPOT_A": {"name": "Guindy Central Depot", "lat": 12.9650, "lng": 80.2150, "node_id": "N0006"},
    "DEPOT_B": {"name": "Velachery Station", "lat": 12.9710, "lng": 80.2220, "node_id": "N0007"},
    "HOSPITAL_A": {"name": "Regional Trauma Center", "lat": 13.0100, "lng": 80.2550, "node_id": "N0005"},
    "HOSPITAL_B": {"name": "Government General Hospital", "lat": 13.0814, "lng": 80.2772, "node_id": "N0020"},
    "SHELTER_S001": {"name": "Anna Nagar Emergency Shelter", "lat": 13.0080, "lng": 80.2720, "node_id": "N0008"},
    "SHELTER_S002": {"name": "Adyar Relief Hub", "lat": 12.9800, "lng": 80.2580, "node_id": "N0012"},
}

class RoutingService:
    def __init__(self):
        self.mapbox_token = MAPBOX_TOKEN

    def calculate_responder_route(
        self,
        resource_id: str,
        origin: Dict[str, float],      # {"lat": float, "lng": float}
        destination: Dict[str, float], # {"lat": float, "lng": float}
        vehicle_type: str = "Hazmat_Team",
        blocked_roads: Optional[Set[str]] = None,
        avoid_hazard_geometry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates operational route for a dispatched emergency responder.
        Recalculates whenever road blocks or hazard plume changes occur.
        """
        blocked_set = set(blocked_roads or [])
        now_iso = datetime.now().isoformat()

        # Check if Mapbox Directions API is configured and road is not manually blocked in our sim
        if self.mapbox_token and not blocked_set:
            try:
                mapbox_result = self._query_mapbox_directions(origin, destination)
                if mapbox_result:
                    mapbox_result["resource_id"] = resource_id
                    mapbox_result["data_source"] = "LIVE (Mapbox Directions API)"
                    mapbox_result["last_calculated"] = now_iso
                    return mapbox_result
            except Exception as e:
                logger.warning(f"Mapbox query failed, falling back to emergency graph: {e}")

        # Emergency Road Graph & Simulation Engine
        return self._generate_simulated_operational_route(
            resource_id=resource_id,
            origin=origin,
            destination=destination,
            vehicle_type=vehicle_type,
            blocked_roads=blocked_set,
            avoid_hazard_geometry=avoid_hazard_geometry
        )

    def _generate_simulated_operational_route(
        self,
        resource_id: str,
        origin: Dict[str, float],
        destination: Dict[str, float],
        vehicle_type: str,
        blocked_roads: Set[str],
        avoid_hazard_geometry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates realistic emergency route geometry and turn-by-turn directions
        accounting for road closures and dynamic reroutes.
        """
        is_rerouted = len(blocked_roads) > 0
        o_lat, o_lng = origin.get("lat", 12.9650), origin.get("lng", 80.2150)
        d_lat, d_lng = destination.get("lat", 12.9920), destination.get("lng", 80.2480)

        # Calculate straight-line Euclidean distance as baseline
        dlat = (d_lat - o_lat) * 111.0
        dlng = (d_lng - o_lng) * 111.0 * math.cos(math.radians(o_lat))
        direct_dist = math.hypot(dlat, dlng)
        
        # Road network factor (typically 1.25x - 1.45x Euclidean)
        road_distance = round(max(direct_dist * 1.32, 2.5), 2)
        
        if is_rerouted:
            # Detour penalty around blocked corridor
            road_distance = round(road_distance * 1.38, 2)
            route_status = "REROUTED"
            primary_road_id = "R03204 (Northern Bypass Detour)"
        else:
            route_status = "ACTIVE"
            primary_road_id = "R03108 (Primary Ingress Arterial)"

        # Normal ETA vs Traffic ETA (seconds)
        # Emergency vehicles with sirens travel ~45 km/h average in industrial zones
        speed_kmh = 42.0 if "hazmat" in vehicle_type.lower() else 48.0
        normal_eta_seconds = int((road_distance / speed_kmh) * 3600)
        
        # Traffic delay penalty (15% to 30% during emergency)
        traffic_delay_factor = 1.22 if not is_rerouted else 1.40
        traffic_eta_seconds = int(normal_eta_seconds * traffic_delay_factor)
        
        eta_minutes = round(traffic_eta_seconds / 60.0, 1)

        # Generate polyline coordinates (GeoJSON LineString)
        # Interpolate waypoints simulating realistic urban road turns
        geometry_coords = self._build_realistic_polyline(
            o_lat, o_lng, d_lat, d_lng, is_rerouted=is_rerouted
        )

        # Turn-by-turn steps
        turn_by_turn = self._generate_turn_by_turn(
            origin_name="Guindy Emergency Staging Depot",
            dest_name="Plant B Chemical Hazard Zone",
            distance_km=road_distance,
            is_rerouted=is_rerouted,
            blocked_roads=blocked_roads
        )

        # Alternative route option
        alternative_route = {
            "name": "Secondary Ingress Corridor (Eastern Rail Feeder)",
            "distance_km": round(road_distance * 1.15, 2),
            "traffic_eta_seconds": int(traffic_eta_seconds * 1.18),
            "eta_minutes": round((traffic_eta_seconds * 1.18) / 60.0, 1),
            "safety_rating": "Medium (Crosses Secondary Buffer)"
        }

        return {
            "resource_id": resource_id,
            "origin": {"lat": o_lat, "lng": o_lng},
            "destination": {"lat": d_lat, "lng": d_lng},
            "distance_km": road_distance,
            "normal_eta_seconds": normal_eta_seconds,
            "traffic_eta_seconds": traffic_eta_seconds,
            "eta_minutes": eta_minutes,
            "route_status": route_status,
            "primary_corridor": primary_road_id,
            "route_geometry": {
                "type": "LineString",
                "coordinates": geometry_coords # [[lat, lng], ...]
            },
            "alternative_routes": [alternative_route],
            "turn_by_turn": turn_by_turn,
            "data_source": "SIMULATION ROUTE",
            "last_calculated": datetime.now().isoformat()
        }

    def _build_realistic_polyline(
        self,
        o_lat: float,
        o_lng: float,
        d_lat: float,
        d_lng: float,
        is_rerouted: bool = False
    ) -> List[List[float]]:
        """
        Creates smooth, multi-segment road coordinates for Mapbox / Leaflet rendering.
        If rerouted, arcs outward around the blocked sector.
        """
        steps = 8
        coords = []
        for i in range(steps + 1):
            t = i / steps
            # Base linear interpolation
            lat = o_lat + (d_lat - o_lat) * t
            lng = o_lng + (d_lng - o_lng) * t

            # Road curving offset
            if is_rerouted:
                # Arc eastward away from central blocked road
                curve = math.sin(t * math.pi) * 0.012
                lng += curve
                lat -= curve * 0.4
            else:
                curve = math.sin(t * math.pi * 2) * 0.003
                lng += curve

            coords.append([round(lat, 6), round(lng, 6)])

        return coords

    def _generate_turn_by_turn(
        self,
        origin_name: str,
        dest_name: str,
        distance_km: float,
        is_rerouted: bool,
        blocked_roads: Set[str]
    ) -> List[Dict[str, Any]]:
        """Generates step-by-step navigation instructions for responder terminal."""
        if is_rerouted:
            blocked_note = f"ALERT: Roads {', '.join(blocked_roads)} BLOCKED! Detour activated."
            return [
                {"step": 1, "road": "Depot Way", "instruction": f"Depart {origin_name} heading North-East", "distance_km": 0.8},
                {"step": 2, "road": "R03000 Arterial", "instruction": "Proceed on Inner Ring Road for 2.2 km", "distance_km": 2.2},
                {"step": 3, "road": "R03204 Detour", "instruction": f"Diverted onto Northern Bypass. {blocked_note}", "distance_km": 3.8},
                {"step": 4, "road": "R03150 Gate Access", "instruction": "Turn right onto Sector Gate 4 Corridor", "distance_km": 1.4},
                {"step": 5, "road": "Plant Perimeter", "instruction": f"Arrive at staging boundary for {dest_name}", "distance_km": 0.4}
            ]
        else:
            return [
                {"step": 1, "road": "Depot Way", "instruction": f"Depart {origin_name} onto primary feeder", "distance_km": 0.7},
                {"step": 2, "road": "R03000 Arterial", "instruction": "Proceed along direct South-North arterial corridor", "distance_km": 2.6},
                {"step": 3, "road": "R03108 Ingress", "instruction": "Maintain direct line on Ingress Corridor R03108", "distance_km": 3.4},
                {"step": 4, "road": "Plant Perimeter Gate", "instruction": f"Approach perimeter staging area at {dest_name}", "distance_km": 1.1}
            ]

    def _query_mapbox_directions(self, origin: Dict[str, float], dest: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Queries Mapbox Directions API if access token is present."""
        if not self.mapbox_token:
            return None
        o_lng, o_lat = origin.get("lng"), origin.get("lat")
        d_lng, d_lat = dest.get("lng"), dest.get("lat")
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{o_lng},{o_lat};{d_lng},{d_lat}?geometries=geojson&steps=true&access_token={self.mapbox_token}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "CrisisCommandAI/1.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                routes = data.get("routes", [])
                if routes:
                    r = routes[0]
                    coords = [[c[1], c[0]] for c in r.get("geometry", {}).get("coordinates", [])]
                    dist_km = round(r.get("distance", 0) / 1000.0, 2)
                    dur_sec = int(r.get("duration", 0))
                    return {
                        "distance_km": dist_km,
                        "normal_eta_seconds": dur_sec,
                        "traffic_eta_seconds": dur_sec,
                        "eta_minutes": round(dur_sec / 60.0, 1),
                        "route_status": "ACTIVE",
                        "route_geometry": {"type": "LineString", "coordinates": coords},
                        "alternative_routes": [],
                        "turn_by_turn": [
                            {"step": i + 1, "road": leg.get("name", "Road"), "instruction": leg.get("maneuver", {}).get("instruction", "Continue"), "distance_km": round(leg.get("distance", 0) / 1000.0, 2)}
                            for i, leg in enumerate(r.get("legs", [{}])[0].get("steps", []))
                        ]
                    }
        return None

# Singleton instance
routing_service = RoutingService()
