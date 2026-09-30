from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from .. import crud

router = APIRouter(
    prefix="/alerts",
    tags=["Role Alerts & Feeds"]
)


@router.get("/{incident_id}", response_model=List[Dict[str, Any]])
def get_alerts(incident_id: str, db: Session = Depends(get_db)):
    return crud.get_alerts_data(db, incident_id)
