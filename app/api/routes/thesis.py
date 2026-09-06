from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, WatchlistItem, Thesis
from app.schemas import ThesisCreate, ThesisOut

router = APIRouter(prefix="/thesis", tags=["thesis"])

@router.post("/", response_model=ThesisOut)
def create_thesis(data: ThesisCreate, user_id: int = 1, db: Session = Depends(get_db)):
    # For demo we hard-code user_id=1. In real app take from auth.
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name="Demo User")
        db.add(user)
        db.commit()

    item = WatchlistItem(user_id=user_id, stock_id=data.stock_id.upper())
    db.add(item)
    db.flush()

    thesis = Thesis(
        watchlist_item_id=item.id,
        tags=data.tags,
        free_text=data.free_text
    )
    db.add(thesis)
    db.commit()
    db.refresh(thesis)

    return {
        "id": thesis.id,
        "stock_id": item.stock_id,
        "tags": thesis.tags,
        "free_text": thesis.free_text,
        "last_reviewed_at": thesis.last_reviewed_at
    }