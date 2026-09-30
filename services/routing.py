"""
Graph Routing Service using NetworkX.
Builds the road network and provides safest path routing with dynamic rerouting.
"""
from typing import List, Dict, Any, Optional, Set
import math
import networkx as nx
import pandas as pd
from services.data_loader import data_loader

class EmergencyRouter:
    def __init__(self):
        self.graph: Optional[nx.Graph] = None
        self.nodes_df: Optional[pd.DataFrame] = None
        self.roads_df: Optional[pd.DataFrame] = None
        self.road_status_df: Optional[pd.DataFrame] = None
        self.routing_df: Optional[pd.DataFrame] = None
        self.build_graph()

    def build_graph(self):
        self.nodes_df = data_loader.get_nodes()
        self.roads_df = data_loader.get_roads()
        self.road_status_df = data_loader.get_road_status()
        self.routing_df = data_loader.get_routing_training()

        self.graph = nx.Graph()

        # Add nodes with latitude, longitude
        for _, row in self.nodes_df.iterrows():
            self.graph.add_node(
                str(row["node_id"]),
                name=str(row.get("node_name", "")),
                node_type=str(row.get("node_type", "")),
                lat=float(row.get("latitude", 0.0)),
                lon=float(row.get("longitude", 0.0)),
            )

        # Merge risk and delay from routing_training
        route_enrich = {}
        for _, r in self.routing_df.iterrows():
            route_enrich[str(r["road_id"])] = {
                "traffic_delay_min": float(r.get("traffic_delay_min", 0.5)),
                "risk_score": float(r.get("risk_score", 0.25)),
                "route_cost": float(r.get("route_cost", 2.0)),
                "usable": int(r.get("usable_for_emergency", 1))
            }

        # Real-time blocked roads from road_status
        live_blocked = set()
        for _, s in self.road_status_df.iterrows():
            if str(s.get("status", "")).strip().lower() == "blocked":
                live_blocked.add(str(s["road_id"]))

        # Add edges
        for _, row in self.roads_df.iterrows():
            r_id = str(row["road_id"])
            u = str(row["from_node"])
            v = str(row["to_node"])
            dist = float(row.get("distance_km", 1.0))
            is_blocked = (int(row.get("blocked_binary", 0)) == 1) or (r_id in live_blocked)

            enrich = route_enrich.get(r_id, {})
            traffic_delay = enrich.get("traffic_delay_min", dist * 1.5)
            risk = enrich.get("risk_score", 0.25)
            usable = enrich.get("usable", 1) == 1 and not is_blocked

            # Compute safety weight (distance + traffic delay + risk penalty)
            weight = dist * 1.0 + traffic_delay * 0.8 + risk * 2.0
            if not usable or is_blocked:
                weight = 1e9

            self.graph.add_edge(
                u, v,
                road_id=r_id,
                distance_km=dist,
                weight=weight,
                traffic_delay=traffic_delay,
                risk_score=risk,
                is_blocked=is_blocked,
                road_type=str(row.get("road_type", "Standard"))
            )

    def find_nearest_node(self, x: float, y: float) -> str:
        """Find the closest node to (x, y) coordinates."""
        best_node = None
        min_dist = float("inf")
        for node_id, data in self.graph.nodes(data=True):
            lat = data.get("lat", 0.0)
            lon = data.get("lon", 0.0)
            d = math.hypot(x - lon, y - lat)
            if d < min_dist:
                min_dist = d
                best_node = node_id
        return best_node or "N0001"

    def get_plant_node(self, plant_name: str) -> str:
        """Find node corresponding to plant name or default."""
        plant_clean = plant_name.strip().lower().replace(" ", "_")
        for node_id, data in self.graph.nodes(data=True):
            name = data.get("name", "").strip().lower()
            if plant_clean in name or name in plant_clean:
                return node_id
        return "N0001"

    def find_safest_route(
        self,
        start_node: str,
        end_node: str,
        blocked_roads: Optional[Set[str]] = None,
        avoid_hazard_nodes: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Finds the safest emergency route avoiding blocked roads and hazard nodes.
        Returns path details, roads used, total distance, travel time, and risk score.
        """
        if not self.graph.has_node(start_node) or not self.graph.has_node(end_node):
            return {
                "success": False,
                "error": f"Node not found: {start_node} or {end_node}",
                "path": [],
                "roads": [],
                "total_distance_km": 0.0,
                "estimated_time_min": 0.0
            }

        blocked_set = set(blocked_roads or [])
        hazard_set = set(avoid_hazard_nodes or [])

        # Create a view / subgraph or custom weight function
        def edge_weight(u, v, d):
            r_id = d.get("road_id", "")
            if r_id in blocked_set or d.get("is_blocked", False):
                return float("inf")
            if u in hazard_set or v in hazard_set:
                return d.get("weight", 1.0) * 10.0  # heavy penalty for entering hazard zone
            return d.get("weight", 1.0)

        try:
            path = nx.shortest_path(self.graph, source=start_node, target=end_node, weight=edge_weight)
            
            # Verify no edge is infinite
            roads_used = []
            total_dist = 0.0
            total_delay = 0.0
            total_risk = 0.0

            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                data = self.graph.get_edge_data(u, v)
                r_id = data.get("road_id", f"R_conn_{i}")
                if r_id in blocked_set or data.get("is_blocked", False):
                    raise nx.NetworkXNoPath("Blocked road encountered")
                roads_used.append(r_id)
                total_dist += data.get("distance_km", 0.0)
                total_delay += data.get("traffic_delay", 0.0)
                total_risk += data.get("risk_score", 0.0)

            est_time = round((total_dist / 40.0) * 60.0 + total_delay, 1)

            return {
                "success": True,
                "start_node": start_node,
                "end_node": end_node,
                "path": path,
                "roads": roads_used,
                "total_distance_km": round(total_dist, 2),
                "estimated_time_min": max(1.0, est_time),
                "average_risk_score": round(total_risk / max(len(roads_used), 1), 3),
                "rerouted": len(blocked_set) > 0
            }
        except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
            # Fallback path if fully isolated
            return {
                "success": False,
                "error": f"No accessible route found between {start_node} and {end_node}: {str(e)}",
                "path": [],
                "roads": [],
                "total_distance_km": 0.0,
                "estimated_time_min": 0.0,
                "rerouted": False
            }

router_service = EmergencyRouter()
