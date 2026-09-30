from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from ..schemas import IncidentCreate
from .. import crud


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents & Detection"]
)


@router.get("/", response_model=List[Dict[str, Any]])
def get_incidents(db: Session = Depends(get_db)):
    return crud.get_all_incidents(db)


@router.post("/")
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db)
):
    return crud.create_incident_with_agents(db, incident.model_dump())


@router.get("/{incident_id}")
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db)
):
    incidents = crud.get_all_incidents(db)
    for inc in incidents:
        if inc["id"] == incident_id:
            return inc
    return {"error": "Incident not found"}