from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, WatchlistItem, Thesis
from app.schemas import ThesisCreate, ThesisOut

router = APIRouter(prefix="/thesis", tags=["thesis"])

@router.get("/", response_model=list[ThesisOut])
def list_theses(user_id: int = 1, db: Session = Depends(get_db)):
    """All watchlist items + their thesis for a user (for rendering the list)."""
    items = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user_id)
        .all()
    )
    out = []
    for item in items:
        if not item.thesis:
            continue
        out.append({
            "id": item.thesis.id,
            "stock_id": item.stock_id,
            "tags": item.thesis.tags,
            "free_text": item.thesis.free_text,
            "last_reviewed_at": item.thesis.last_reviewed_at,
        })
    return out


@router.post("/{thesis_id}/mark-reviewed", response_model=ThesisOut)
def mark_reviewed(thesis_id: int, db: Session = Depends(get_db)):
    """Reset last_reviewed_at to now — the digest's 'since you last checked' clock."""
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")

    thesis.last_reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(thesis)

    return {
        "id": thesis.id,
        "stock_id": thesis.watchlist_item.stock_id,
        "tags": thesis.tags,
        "free_text": thesis.free_text,
        "last_reviewed_at": thesis.last_reviewed_at,
    }


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