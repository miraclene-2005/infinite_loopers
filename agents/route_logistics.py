"""
Agent 7: Route & Logistics Agent
Determines the safest emergency routes using NetworkX, avoiding blocked roads
and hazardous plume zones with dynamic recalculation on replanning.
"""
from typing import Dict, Any, List, Optional, Set
from services.routing import router_service
from services.validation import validate_route_roads

class RouteLogisticsAgent:
    def __init__(self):
        self.router = router_service

    def plan_routes(
        self,
        incident: Dict[str, Any],
        spread_prediction: Optional[Dict[str, Any]] = None,
        blocked_roads: Optional[Set[str]] = None,
        destination_nodes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculates safe primary emergency access routes and evacuation corridors.
        """
        plant_name = str(incident.get("location", "Plant_A"))
        incident_node = self.router.get_plant_node(plant_name)

        # Dispatch base nodes
        hq_node = "N0001" # Command / Depot Base
        dest_nodes = destination_nodes or ["N0050", "N0100", "N0200"]

        blocked_set = set(blocked_roads or [])

        # Nodes within red hazard spread zone to avoid
        avoid_nodes: Set[str] = set()
        if spread_prediction and "red_zone_m" in spread_prediction:
            red_m = float(spread_prediction["red_zone_m"])
            # Map hazard radius to nearby node IDs if within proximity
            inc_x = float(incident.get("x", 50.0))
            inc_y = float(incident.get("y", 50.0))
            # Proximity check in nodes
            nodes_df = self.router.nodes_df
            if nodes_df is not None:
                for _, row in nodes_df.head(200).iterrows():
                    d_approx = ((float(row.get("latitude", 0)) - inc_y)**2 + (float(row.get("longitude", 0)) - inc_x)**2)**0.5
                    if d_approx < (red_m / 1000.0) * 0.1:
                        avoid_nodes.add(str(row["node_id"]))

        # Remove incident node itself from avoid list so we can reach it
        avoid_nodes.discard(incident_node)

        # 1. Ingress route: Command Base -> Incident Location
        ingress_route = self.router.find_safest_route(
            start_node=hq_node,
            end_node=incident_node,
            blocked_roads=blocked_set,
            avoid_hazard_nodes=avoid_nodes
        )

        # 2. Egress / Evacuation route: Incident Location -> Outer Perimeter Safe Node
        egress_route = self.router.find_safest_route(
            start_node=incident_node,
            end_node=dest_nodes[0] if dest_nodes else "N0050",
            blocked_roads=blocked_set,
            avoid_hazard_nodes=avoid_nodes
        )

        # Validation check: ensure no road in route is in blocked_roads
        all_roads_used = ingress_route.get("roads", []) + egress_route.get("roads", [])
        validation_errors = validate_route_roads(all_roads_used, blocked_set)

        routes_summary = [
            {
                "route_type": "Primary Emergency Ingress",
                "purpose": "First responder arrival corridor",
                "start": hq_node,
                "destination": incident_node,
                "roads": ingress_route.get("roads", []),
                "path_nodes": ingress_route.get("path", []),
                "distance_km": ingress_route.get("total_distance_km", 0.0),
                "eta_minutes": ingress_route.get("estimated_time_min", 0.0),
                "is_active": ingress_route.get("success", False),
                "rerouted": ingress_route.get("rerouted", False)
            },
            {
                "route_type": "Primary Evacuation Corridor",
                "purpose": "Worker & perimeter safe evacuation pathway",
                "start": incident_node,
                "destination": dest_nodes[0] if dest_nodes else "N0050",
                "roads": egress_route.get("roads", []),
                "path_nodes": egress_route.get("path", []),
                "distance_km": egress_route.get("total_distance_km", 0.0),
                "eta_minutes": egress_route.get("estimated_time_min", 0.0),
                "is_active": egress_route.get("success", False),
                "rerouted": egress_route.get("rerouted", False)
            }
        ]

        return {
            "incident_node": incident_node,
            "blocked_roads_avoided": list(blocked_set),
            "hazard_nodes_bypassed": list(avoid_nodes),
            "routes": routes_summary,
            "validation_errors": validation_errors,
            "all_routes_clear": len(validation_errors) == 0
        }
