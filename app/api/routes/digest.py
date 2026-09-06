from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.digest import generate_digest

router = APIRouter(prefix="/digest", tags=["digest"])

@router.get("/")
def get_digest(user_id: int = 1, stock_id: str | None = None, db: Session = Depends(get_db)):
    return generate_digest(db, user_id, stock_id)