"""
Validation and Safety Verification Layer
Enforces constraints:
- no negative capacities
- no resource assigned twice
- no unavailable resource assigned
- no hospital capacity exceeded
- no shelter capacity exceeded
- no blocked road selected
- missing dataset values handled safely
"""
from typing import Dict, List, Any

def validate_capacities(entity_name: str, capacity: int, current_occupancy: int = 0) -> bool:
    if capacity < 0 or current_occupancy < 0:
        raise ValueError(f"Negative capacity or occupancy detected for {entity_name}: cap={capacity}, occ={current_occupancy}")
    return True

def validate_resource_assignments(assignments: List[Dict[str, Any]], available_resource_ids: set) -> List[str]:
    """
    Validates:
    - No resource assigned twice
    - No unavailable resource assigned
    Returns a list of validation warnings/errors.
    """
    assigned_ids = set()
    errors = []
    for item in assignments:
        res_id = item.get("resource_id")
        if not res_id:
            continue
        if res_id in assigned_ids:
            errors.append(f"Safety Violation: Resource {res_id} assigned more than once.")
        assigned_ids.add(res_id)
        if res_id not in available_resource_ids:
            errors.append(f"Safety Violation: Resource {res_id} is unavailable or does not exist.")
    return errors

def validate_hospital_capacities(patient_distribution: Dict[str, int], hospital_capacities: Dict[str, int]) -> List[str]:
    """
    Validates that assigned patients do not exceed hospital capacity.
    """
    errors = []
    for hosp_id, assigned_count in patient_distribution.items():
        max_cap = hospital_capacities.get(hosp_id, 0)
        if assigned_count > max_cap:
            errors.append(f"Capacity Violation: Hospital {hosp_id} assigned {assigned_count} patients, exceeding capacity of {max_cap}.")
        if assigned_count < 0:
            errors.append(f"Value Error: Negative patient assignment to hospital {hosp_id}.")
    return errors

def validate_shelter_capacities(evacuee_distribution: Dict[str, int], shelter_capacities: Dict[str, int]) -> List[str]:
    """
    Validates that evacuees assigned to a shelter do not exceed available capacity.
    """
    errors = []
    for shelter_id, assigned_count in evacuee_distribution.items():
        avail_cap = shelter_capacities.get(shelter_id, 0)
        if assigned_count > avail_cap:
            errors.append(f"Capacity Violation: Shelter {shelter_id} assigned {assigned_count} people, exceeding capacity of {avail_cap}.")
        if assigned_count < 0:
            errors.append(f"Value Error: Negative evacuee assignment to shelter {shelter_id}.")
    return errors

def validate_route_roads(road_ids: List[str], blocked_roads: set) -> List[str]:
    """
    Validates that no road in the route is blocked.
    """
    errors = []
    for r_id in road_ids:
        if r_id in blocked_roads:
            errors.append(f"Route Hazard Violation: Road {r_id} is blocked or unusable but included in emergency route.")
    return errors

SAFETY_DISCLAIMER = (
    "DISCLAIMER: This system is an AI-assisted hackathon research prototype. "
    "All plume perimeters, hospital assignments, and route suggestions are algorithmic model estimates "
    "and NOT certified for real-world emergency command operations without human incident commander verification."
)
