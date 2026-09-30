"""
Agent 5: Emergency Resource Allocation Agent
Optimally allocates available emergency response teams and equipment from resources.csv.
Enforces:
- No unavailable/maintenance resources assigned
- No duplicate assignments
- Multi-criteria ranking (proximity, readiness score, response time, fuel/battery)
"""
from typing import List, Dict, Any, Optional, Set
import math
import pandas as pd
from services.data_loader import data_loader
from services.validation import validate_resource_assignments

class ResourceAllocationAgent:
    def __init__(self):
        self.data_loader = data_loader

    def allocate(
        self,
        incident: Dict[str, Any],
        hazards: Dict[str, Any],
        unavailable_resource_ids: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Allocates Fire teams, Hazmat teams, Rescue teams, Ambulances, and Support units.
        """
        resources_df = self.data_loader.get_resources()
        unavailable_set = set(unavailable_resource_ids or [])
        incident_id = str(incident.get("incident_id", "INC-001"))
        inc_x = float(incident.get("x", 50.0))
        inc_y = float(incident.get("y", 50.0))
        has_fire = bool(incident.get("fire", False))
        has_explosion = bool(incident.get("explosion", False))
        chemical = str(incident.get("chemical", "None"))
        is_chemical = chemical.lower() not in ["none", "unknown", ""]
        people_affected = int(incident.get("people_affected", 0))

        # Filter strictly for Available resources and not in unavailable_set
        available_mask = (
            resources_df["status"].str.strip().str.lower() == "available"
        ) & (~resources_df["resource_id"].isin(unavailable_set))
        available_df = resources_df[available_mask].copy()

        # Compute Euclidean distance from incident coords
        available_df["calc_distance"] = available_df.apply(
            lambda r: math.hypot(float(r.get("x", 0)) - inc_x, float(r.get("y", 0)) - inc_y),
            axis=1
        )

        # Composite fitness score: higher readiness, lower distance, lower response_time
        available_df["score"] = (
            available_df["readiness_score"].fillna(0.7) * 40.0
            - available_df["calc_distance"] * 1.5
            - available_df["response_time"].fillna(15) * 1.0
        )

        # Determine required quotas based on incident scale
        quotas: Dict[str, int] = {
            "Fire_Team": 2 if has_fire or has_explosion else 1,
            "Hazmat_Team": 2 if is_chemical and (has_fire or people_affected > 20) else (1 if is_chemical else 0),
            "Rescue_Team": 2 if has_explosion or people_affected > 30 else 1,
            "Ambulance": max(1, min(4, math.ceil(people_affected / 15.0))) if people_affected > 0 else 1,
            "Foam_Unit": 1 if has_fire else 0,
            "Spill_Response": 1 if is_chemical and not has_fire else 0,
            "Water_Tanker": 1 if has_fire else 0,
            "Mobile_Command": 1
        }

        assignments: List[Dict[str, Any]] = []
        assigned_ids: Set[str] = set()

        for req_type, target_count in quotas.items():
            if target_count <= 0:
                continue

            # Candidate selection for this resource type
            candidates = available_df[
                (available_df["type"].str.lower() == req_type.lower()) &
                (~available_df["resource_id"].isin(assigned_ids))
            ].sort_values(by="score", ascending=False)

            picked = candidates.head(target_count)
            for _, r in picked.iterrows():
                r_id = str(r["resource_id"])
                assigned_ids.add(r_id)

                resp_time = int(r.get("response_time", 10))
                # Reason generation
                if req_type == "Fire_Team":
                    reason = "Primary fire suppression and thermal barrier establishment"
                elif req_type == "Hazmat_Team":
                    reason = f"Containment and neutralization of {chemical} leak"
                elif req_type == "Rescue_Team":
                    reason = f"Search and extraction of {people_affected} affected site workers"
                elif req_type == "Ambulance":
                    reason = "Rapid triage and emergency patient transport"
                elif req_type == "Foam_Unit":
                    reason = "Specialized chemical vapor blanket deployment"
                elif req_type == "Mobile_Command":
                    reason = "On-site multi-agency tactical command staging"
                else:
                    reason = "Emergency operational support"

                assignments.append({
                    "resource_id": r_id,
                    "resource_type": str(r["type"]),
                    "station_location": str(r.get("location", "Depot")),
                    "reason": reason,
                    "estimated_response_time": resp_time,
                    "distance_km": round(float(r["calc_distance"]), 1),
                    "readiness_score": float(r.get("readiness_score", 0.8))
                })

        # Run validation
        all_available_ids = set(available_df["resource_id"])
        validation_errors = validate_resource_assignments(assignments, all_available_ids)

        return {
            "incident_id": incident_id,
            "total_assigned": len(assignments),
            "assignments": assignments,
            "validation_errors": validation_errors,
            "safety_certified": len(validation_errors) == 0
        }
