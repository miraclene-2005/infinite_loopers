from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from ..database import get_db
from ..schemas import ReplanRequest
from .. import crud

router = APIRouter(
    tags=["Command, Response Plan & Replanning"]
)


@router.get("/response-plan/{incident_id}")
def get_response_plan(incident_id: str, db: Session = Depends(get_db)):
    return crud.get_response_plan_data(db, incident_id)


@router.post("/response-plan/{incident_id}/approve")
def approve_plan(
    incident_id: str,
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db)
):
    operator = payload.get("operator", "Control room operator") if payload else "Control room operator"
    return crud.approve_response_plan(db, incident_id, operator=operator)


@router.post("/replan")
def replan_root(
    payload: Optional[ReplanRequest] = None,
    db: Session = Depends(get_db)
):
    iid = payload.incident_id if payload and payload.incident_id else "INC-001"
    evt = payload.event if payload else {"type": "manual"}
    return crud.trigger_replanning_workflow(db, iid, evt)


@router.post("/replan/{incident_id}")
def replan_by_id(
    incident_id: str,
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db)
):
    evt = payload or {"type": "manual"}
    return crud.trigger_replanning_workflow(db, incident_id, evt)


@router.post("/replan/simulate-change/{incident_id}")
def simulate_change(
    incident_id: str,
    db: Session = Depends(get_db)
):
    return crud.trigger_replanning_workflow(db, incident_id, {"type": "scenario"})


@router.post("/reset")
def reset_db(db: Session = Depends(get_db)):
    return crud.reset_crisis_state(db)