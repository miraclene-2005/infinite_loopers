"""
Agent 8: Evacuation & Shelter Agent
Manages zone hazard classification (RED, ORANGE, GREEN) and assigns evacuees
to optimal shelters based on capacity, current occupancy, distance, and supply levels.
"""
from typing import Dict, Any, List, Optional
import math
import pandas as pd
from services.data_loader import data_loader
from services.validation import validate_shelter_capacities

class EvacuationShelterAgent:
    def __init__(self):
        self.data_loader = data_loader

    def plan_evacuation(
        self,
        incident: Dict[str, Any],
        spread_prediction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classifies hazard zones and allocates evacuees across available shelters.
        """
        shelters_df = self.data_loader.get_shelters()
        people_affected = int(incident.get("people_affected", 0))
        inc_x = float(incident.get("x", 50.0))
        inc_y = float(incident.get("y", 50.0))

        # Calculate Available Capacity = capacity - current_occupancy
        shelters_df["available_capacity"] = (shelters_df["capacity"] - shelters_df["current_occupancy"]).clip(lower=0)

        # Zone Classification
        red_radius = float(spread_prediction.get("red_zone_m", 500.0)) if spread_prediction else 500.0
        orange_radius = float(spread_prediction.get("orange_zone_m", 1200.0)) if spread_prediction else 1200.0

        # Number of people in each zone
        red_people = math.ceil(people_affected * 0.7) if people_affected > 0 else 0
        orange_people = max(0, people_affected - red_people)

        zones = {
            "RED": {
                "status": "IMMEDIATE_EVACUATION",
                "radius_m": red_radius,
                "affected_population": red_people,
                "urgency": "Immediate life-safety threat; proceed directly to assigned shelter."
            },
            "ORANGE": {
                "status": "CONTROLLED_PREPARED_EVACUATION",
                "radius_m": orange_radius,
                "affected_population": orange_people,
                "urgency": "Staged evacuation; shut down non-critical utilities and stage at muster points."
            },
            "GREEN": {
                "status": "NO_EVACUATION_REQUIRED",
                "radius_m": "> " + str(orange_radius),
                "affected_population": 0,
                "urgency": "Normal operations; monitor emergency radio channels."
            }
        }

        # Filter valid shelters with available capacity and active status
        valid_status = ["available", "limited"]
        candidates = shelters_df[
            (shelters_df["status"].str.strip().str.lower().isin(valid_status)) &
            (shelters_df["available_capacity"] > 0)
        ].copy()

        # Distance calculation
        candidates["distance"] = candidates.apply(
            lambda s: math.hypot(float(s.get("x", 0)) - inc_x, float(s.get("y", 0)) - inc_y),
            axis=1
        )

        # Prioritize supply levels
        supply_score = {"All": 5, "Medical": 4, "Food": 3, "Water": 2, "Basic": 1}
        candidates["supply_score"] = candidates["supply_level"].map(supply_score).fillna(1)

        # Sort: lowest distance, highest supply, highest capacity
        candidates = candidates.sort_values(
            by=["distance", "supply_score", "available_capacity"],
            ascending=[True, False, False]
        )

        assigned_shelters: List[Dict[str, Any]] = []
        shelter_distribution: Dict[str, int] = {}
        shelter_cap_lookup: Dict[str, int] = {}
        remaining_evacuees = people_affected

        for _, s in candidates.iterrows():
            if remaining_evacuees <= 0:
                break
            s_id = str(s["shelter_id"])
            s_name = str(s["name"])
            avail_cap = int(s["available_capacity"])
            shelter_cap_lookup[s_id] = avail_cap

            allot = min(remaining_evacuees, avail_cap)
            if allot > 0:
                shelter_distribution[s_id] = allot
                remaining_evacuees -= allot
                assigned_shelters.append({
                    "shelter_id": s_id,
                    "name": s_name,
                    "assigned_people": allot,
                    "available_capacity": avail_cap,
                    "total_capacity": int(s["capacity"]),
                    "current_occupancy_after": int(s["current_occupancy"]) + allot,
                    "zone": str(s.get("zone", "Central")),
                    "supply_level": str(s.get("supply_level", "Basic")),
                    "staff_count": int(s.get("staff_count", 10)),
                    "distance_km": round(float(s["distance"]), 1)
                })

        validation_errors = validate_shelter_capacities(shelter_distribution, shelter_cap_lookup)

        return {
            "total_evacuees": people_affected,
            "zones": zones,
            "assigned_shelters": assigned_shelters,
            "shelter_distribution": shelter_distribution,
            "unassigned_evacuees": max(0, remaining_evacuees),
            "validation_errors": validation_errors,
            "evacuation_complete": remaining_evacuees == 0
        }
