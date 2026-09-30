from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class RiskInfo(BaseModel):
    chemical: str = "high"
    fire: str = "high"
    explosion: str = "medium"
    structural: str = "low"
    domino_effect: str = "Possible: solvent storage 40 m east"
    spread_direction: str = "SE"
    wind: str = "From NW, 14 km/h"
    hazard_radius: float = 11.0


class IncidentCreate(BaseModel):
    type: Optional[str] = None
    incident_type: Optional[str] = None
    location: str
    severity: int = 5
    people_affected: int = 0
    chemical: Optional[str] = None
    fire: bool = False
    source: Optional[str] = "Manual report"
    confirmed: bool = True
    coords: Optional[List[float]] = [30.0, 65.0]


class IncidentResponse(BaseModel):
    id: str
    type: str
    location: str
    coords: List[float]
    severity: int
    severity_label: str
    people_affected: int
    status: str
    source: str
    reported_at: str
    confirmed: bool
    uncertain_fields: List[str] = []
    risk: RiskInfo

    class Config:
        from_attributes = True


class ResourceCreate(BaseModel):
    resource_type: str
    name: str
    location: str = "On site"
    available: bool = True
    position: Optional[List[float]] = [0.0, 0.0]


class ResourceResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    assigned_to: Optional[str] = None
    position: List[float]
    note: str = ""
    changed: bool = False

    class Config:
        from_attributes = True


class HospitalResponse(BaseModel):
    id: str
    name: str
    coords: List[float]
    capacity: int
    available_beds: int
    burn_unit: bool
    travel_min: int
    status: str


class RouteResponse(BaseModel):
    id: str
    name: str
    path: List[List[float]]
    status: str
    travel_min: int
    reason: str


class ZoneItem(BaseModel):
    id: str
    name: str
    action: str
    population: int
    bounds: List[float]


class ShelterItem(BaseModel):
    id: str
    name: str
    coords: List[float]
    capacity: int
    available: int
    status: str


class EvacuationResponse(BaseModel):
    incident_id: str
    affected_population: int
    zones: List[ZoneItem]
    shelters: List[ShelterItem]


class AlertResponse(BaseModel):
    time: str
    audience: str
    severity: str
    message: str


class ActionItem(BaseModel):
    category: str
    assignment: str
    reason: str


class StageItem(BaseModel):
    stage: str
    status: str


class ChangeItem(BaseModel):
    type: str
    message: str


class ResponsePlanResponse(BaseModel):
    incident_id: str
    version: int
    status: str
    generated_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    pipeline: List[StageItem]
    changes: List[ChangeItem]
    approval_items: List[str]
    previous: List[ActionItem]
    current: List[ActionItem]


class ReplanRequest(BaseModel):
    incident_id: Optional[str] = "INC-001"
    event: Optional[Dict[str, Any]] = None