"""
Live Responder GPS Tracking & Dynamic ETA Service.
Maintains continuous real-time telemetry, advances simulated vehicles along
operational route geometries, calculates instantaneous speed and heading,
and dynamically recalculates normal and traffic-adjusted ETAs.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import logging

from services.event_engine import event_engine, EVENT_TYPES
from services.routing_service import routing_service

logger = logging.getLogger("tracking_service")

class TrackingService:
    def __init__(self):
        # Maps resource_id -> dynamic telemetry object
        self._fleet: Dict[str, Dict[str, Any]] = {}

    def register_or_update_unit(
        self,
        resource_id: str,
        unit_type: str,
        name: str,
        origin_coords: Dict[str, float],
        dest_coords: Dict[str, float],
        destination_name: str,
        blocked_roads: Optional[List[str]] = None,
        initial_progress: float = 12.0
    ) -> Dict[str, Any]:
        """Registers a dispatched unit and generates its initial routing & telemetry."""
        clean_id = resource_id.strip().upper()
        now = datetime.now()

        # Compute initial route via routing_service
        route_plan = routing_service.calculate_responder_route(
            resource_id=clean_id,
            origin=origin_coords,
            destination=dest_coords,
            vehicle_type=unit_type,
            blocked_roads=set(blocked_roads or [])
        )

        polyline = route_plan.get("route_geometry", {}).get("coordinates", [
            [origin_coords["lat"], origin_coords["lng"]],
            [dest_coords["lat"], dest_coords["lng"]]
        ])

        # Initial interpolated coordinate
        lat, lng = self._interpolate_coords(polyline, initial_progress / 100.0)
        heading = self._calculate_bearing(polyline, initial_progress / 100.0)

        unit_state = {
            "resource_id": clean_id,
            "type": unit_type,
            "name": name,
            "status": "EN_ROUTE",
            "progress_pct": initial_progress,
            "latitude": lat,
            "longitude": lng,
            "current_location": {"lat": lat, "lng": lng},
            "destination": destination_name,
            "destination_coords": dest_coords,
            "speed_kmh": 46.5 if "fire" in unit_type.lower() else 42.0,
            "heading_deg": heading,
            "route_id": route_plan.get("primary_corridor", "R03108"),
            "distance_km": route_plan.get("distance_km", 5.4),
            "normal_eta_seconds": route_plan.get("normal_eta_seconds", 540),
            "traffic_eta_seconds": route_plan.get("traffic_eta_seconds", 660),
            "eta_minutes": route_plan.get("eta_minutes", 11.0),
            "eta_display": f"{int(route_plan.get('eta_minutes', 11.0)):02d}:{int((route_plan.get('traffic_eta_seconds', 660) % 60)):02d}",
            "route_status": route_plan.get("route_status", "ACTIVE"),
            "route_geometry": route_plan.get("route_geometry"),
            "turn_by_turn": route_plan.get("turn_by_turn", []),
            "alternative_routes": route_plan.get("alternative_routes", []),
            "data_source": route_plan.get("data_source", "SIMULATION ROUTE"),
            "last_updated": now.strftime("%H:%M:%S")
        }

        self._fleet[clean_id] = unit_state
        return unit_state

    def get_unit(self, resource_id: str) -> Optional[Dict[str, Any]]:
        return self._fleet.get(resource_id.strip().upper())

    def get_all_units(self) -> List[Dict[str, Any]]:
        return list(self._fleet.values())

    def tick_unit_gps(self, resource_id: str, incident_id: str = "I001", step_pct: float = 6.5) -> Dict[str, Any]:
        """
        Advances a unit along its route polyline, recalculating speed, heading,
        and dynamic remaining ETA.
        """
        clean_id = resource_id.strip().upper()
        unit = self._fleet.get(clean_id)
        if not unit:
            return {}

        if unit["status"] == "ARRIVED":
            return unit

        now = datetime.now()
        current_prog = unit.get("progress_pct", 10.0)
        new_prog = min(100.0, current_prog + step_pct)
        unit["progress_pct"] = round(new_prog, 1)

        polyline = unit.get("route_geometry", {}).get("coordinates", [])
        if polyline:
            new_lat, new_lng = self._interpolate_coords(polyline, new_prog / 100.0)
            new_heading = self._calculate_bearing(polyline, new_prog / 100.0)
            unit["latitude"] = new_lat
            unit["longitude"] = new_lng
            unit["current_location"] = {"lat": new_lat, "lng": new_lng}
            unit["heading_deg"] = new_heading

        # Dynamic ETA recalculation based on remaining road distance
        remaining_ratio = max(0.0, (100.0 - new_prog) / 100.0)
        total_dist = unit.get("distance_km", 6.0)
        remaining_dist = round(total_dist * remaining_ratio, 2)
        
        speed = unit.get("speed_kmh", 44.0)
        if remaining_dist > 0:
            normal_secs = int((remaining_dist / speed) * 3600)
            traffic_secs = int(normal_secs * 1.25)
            eta_mins = round(traffic_secs / 60.0, 1)
        else:
            normal_secs = 0
            traffic_secs = 0
            eta_mins = 0.0

        unit["normal_eta_seconds"] = normal_secs
        unit["traffic_eta_seconds"] = traffic_secs
        unit["eta_minutes"] = eta_mins
        unit["eta_display"] = f"{int(eta_mins):02d}:{int(traffic_secs % 60):02d}"
        unit["last_updated"] = now.strftime("%H:%M:%S")

        if new_prog >= 100.0:
            unit["status"] = "ARRIVED"
            unit["speed_kmh"] = 0.0
            event_engine.emit(
                event_type=EVENT_TYPES["RESOURCE_ASSIGNED"],
                incident_id=incident_id,
                source=f"GPS Telemetry ({clean_id})",
                severity="SUCCESS",
                data={"unit_id": clean_id, "status": "ARRIVED", "destination": unit["destination"]}
            )

        return unit

    def reroute_unit(
        self,
        resource_id: str,
        incident_id: str,
        blocked_roads: List[str],
        reason: str = "Road obstruction detected"
    ) -> Dict[str, Any]:
        """
        Forces immediate route recalculation for a responder when a road closure occurs.
        Updates route geometry, alternative routes, and ETAs.
        """
        clean_id = resource_id.strip().upper()
        unit = self._fleet.get(clean_id)
        if not unit:
            return {}

        prev_eta = unit.get("eta_display", "08:21")
        new_route = routing_service.calculate_responder_route(
            resource_id=clean_id,
            origin=unit["current_location"],
            destination=unit["destination_coords"],
            vehicle_type=unit["type"],
            blocked_roads=set(blocked_roads)
        )

        unit["route_geometry"] = new_route["route_geometry"]
        unit["route_status"] = new_route["route_status"]
        unit["distance_km"] = new_route["distance_km"]
        unit["normal_eta_seconds"] = new_route["normal_eta_seconds"]
        unit["traffic_eta_seconds"] = new_route["traffic_eta_seconds"]
        unit["eta_minutes"] = new_route["eta_minutes"]
        unit["eta_display"] = f"{int(new_route['eta_minutes']):02d}:{int(new_route['traffic_eta_seconds'] % 60):02d}"
        unit["turn_by_turn"] = new_route["turn_by_turn"]
        unit["alternative_routes"] = new_route["alternative_routes"]
        unit["progress_pct"] = 15.0 # Reset along detour
        unit["last_updated"] = datetime.now().strftime("%H:%M:%S")

        event_engine.emit(
            event_type=EVENT_TYPES["ROUTE_CHANGED"],
            incident_id=incident_id,
            source="Routing Agent (Agent 7)",
            severity="HIGH",
            data={
                "resource_id": clean_id,
                "unit_name": unit["name"],
                "previous_eta": prev_eta,
                "new_eta": unit["eta_display"],
                "reason": reason,
                "blocked_roads": blocked_roads,
                "route_status": "REROUTED"
            }
        )

        return unit

    def _interpolate_coords(self, coords: List[List[float]], progress_ratio: float) -> tuple[float, float]:
        """Interpolates lat, lng along polyline vertices given 0.0 - 1.0 progress."""
        if not coords:
            return (12.9716, 80.2200)
        if len(coords) == 1 or progress_ratio <= 0.0:
            return (coords[0][0], coords[0][1])
        if progress_ratio >= 1.0:
            return (coords[-1][0], coords[-1][1])

        total_segments = len(coords) - 1
        pos = progress_ratio * total_segments
        idx = int(pos)
        rem = pos - idx
        if idx >= total_segments:
            return (coords[-1][0], coords[-1][1])

        p1 = coords[idx]
        p2 = coords[idx + 1]
        lat = round(p1[0] + (p2[0] - p1[0]) * rem, 6)
        lng = round(p1[1] + (p2[1] - p1[1]) * rem, 6)
        return (lat, lng)

    def _calculate_bearing(self, coords: List[List[float]], progress_ratio: float) -> int:
        """Calculates compass heading angle (0-360 deg) for marker rotation."""
        if len(coords) < 2:
            return 315
        total_segments = len(coords) - 1
        idx = min(total_segments - 1, int(progress_ratio * total_segments))
        p1 = coords[idx]
        p2 = coords[idx + 1]
        y = math.sin(math.radians(p2[1] - p1[1])) * math.cos(math.radians(p2[0]))
        x = math.cos(math.radians(p1[0])) * math.sin(math.radians(p2[0])) - \
            math.sin(math.radians(p1[0])) * math.cos(math.radians(p2[0])) * math.cos(math.radians(p2[1] - p1[1]))
        brng = (math.degrees(math.atan2(y, x)) + 360) % 360
        return int(brng)

# Singleton instance
tracking_service = TrackingService()
