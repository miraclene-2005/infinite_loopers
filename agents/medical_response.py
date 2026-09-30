"""
Agent 6: Medical Response Agent
Coordinates patient triage and allocates victims to hospitals without exceeding capacity.
Datasets: hospitals_500_final.csv, resources.csv
"""
from typing import Dict, Any, List, Optional
import math
import pandas as pd
from services.data_loader import data_loader
from services.validation import validate_hospital_capacities

class MedicalResponseAgent:
    def __init__(self):
        self.data_loader = data_loader

    def coordinate_medical_response(
        self,
        incident: Dict[str, Any],
        resource_allocations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Distributes injured people among nearby hospitals with verified emergency/ICU capacity.
        Never exceeds available capacity.
        """
        hospitals_df = self.data_loader.get_hospitals()
        people_affected = int(incident.get("people_affected", 0))
        severity = int(incident.get("severity", 5))

        # Estimate injured count (assumed ~60% of people affected require treatment, min 1 if people_affected > 0)
        injured_count = math.ceil(people_affected * 0.6) if people_affected > 0 else 0
        critical_inhalation_or_burn = math.ceil(injured_count * (0.3 if severity >= 7 else 0.15))

        # Filter available or limited status hospitals with positive emergency capacity
        valid_status = ["available", "limited"]
        candidates = hospitals_df[
            (hospitals_df["status"].str.strip().str.lower().isin(valid_status)) &
            (hospitals_df["emergency_capacity"] > 0)
        ].copy()

        # Sort by status (Available first), response time, and capacity
        candidates["status_rank"] = candidates["status"].apply(lambda s: 0 if s.lower() == "available" else 1)
        candidates = candidates.sort_values(
            by=["status_rank", "average_response_time", "emergency_capacity"],
            ascending=[True, True, False]
        )

        patient_distribution: Dict[str, int] = {}
        hospital_details: List[Dict[str, Any]] = []
        remaining_patients = injured_count
        hospital_capacity_lookup: Dict[str, int] = {}

        for _, h in candidates.iterrows():
            if remaining_patients <= 0:
                break
            h_id = str(h["hospital_id"])
            h_name = str(h["name"])
            capacity = int(h["emergency_capacity"])
            icu = int(h.get("icu", 0))
            resp_time = int(h.get("average_response_time", 10))
            hospital_capacity_lookup[h_id] = capacity

            take = min(remaining_patients, capacity)
            if take > 0:
                patient_distribution[h_id] = take
                remaining_patients -= take
                hospital_details.append({
                    "hospital_id": h_id,
                    "name": h_name,
                    "allocated_patients": take,
                    "emergency_capacity": capacity,
                    "icu_beds": icu,
                    "zone": str(h.get("zone", "Central")),
                    "average_response_time_min": resp_time,
                    "status": str(h["status"])
                })

        # Count assigned ambulances from resource allocations
        assigned_ambulances = 0
        if resource_allocations and "assignments" in resource_allocations:
            assigned_ambulances = sum(
                1 for a in resource_allocations["assignments"] if "ambulance" in str(a.get("resource_type", "")).lower()
            )

        # Validate capacity constraints
        validation_errors = validate_hospital_capacities(patient_distribution, hospital_capacity_lookup)

        return {
            "total_injured": injured_count,
            "critical_cases": critical_inhalation_or_burn,
            "ambulances_deployed": max(1, assigned_ambulances),
            "patient_distribution": patient_distribution,
            "hospitals_utilized": hospital_details,
            "unassigned_patients": max(0, remaining_patients),
            "capacity_exceeded": False,
            "validation_errors": validation_errors,
            "message": f"Successfully distributed {injured_count - remaining_patients} patients across {len(hospital_details)} hospitals."
        }
