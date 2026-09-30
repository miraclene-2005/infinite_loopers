from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from .. import crud

router = APIRouter(
    prefix="/evacuation",
    tags=["Evacuation & Shelters"]
)


@router.get("/{incident_id}", response_model=Dict[str, Any])
def get_evacuation(incident_id: str, db: Session = Depends(get_db)):
    return crud.get_evacuation_data(db, incident_id)
