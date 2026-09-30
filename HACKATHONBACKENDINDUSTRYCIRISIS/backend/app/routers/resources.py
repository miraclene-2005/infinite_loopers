from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from ..schemas import ResourceCreate
from .. import crud


router = APIRouter(
    prefix="/resources",
    tags=["Resources & Emergency Teams"]
)


@router.get("/", response_model=List[Dict[str, Any]])
def get_resources(db: Session = Depends(get_db)):
    return crud.get_all_resources(db)


@router.post("/")
def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db)
):
    # Quick creation helper if needed
    return crud.get_all_resources(db)