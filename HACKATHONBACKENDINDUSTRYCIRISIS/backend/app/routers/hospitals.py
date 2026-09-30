from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from .. import crud

router = APIRouter(
    prefix="/hospitals",
    tags=["Hospitals & Medical"]
)


@router.get("/", response_model=List[Dict[str, Any]])
def get_hospitals(db: Session = Depends(get_db)):
    return crud.get_all_hospitals(db)
