from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Thesis, RelevanceScore
from app.schemas import EventCreate
from app.services.tagging import tag_event
from app.services.relevance import calculate_relevance

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/ingest")
def ingest_event(raw: dict, db: Session = Depends(get_db)):
    """
    Accepts raw event → tags it → stores Event → runs relevance against all theses on that stock.
    """
    tagged = tag_event(raw)

    event = Event(**tagged)
    db.add(event)
    db.flush()

    # Find all theses watching this stock
    theses = (
        db.query(Thesis)
        .join(Thesis.watchlist_item)
        .filter(Thesis.watchlist_item.has(stock_id=event.stock_id))
        .all()
    )

    results = []
    for thesis in theses:
        rel = calculate_relevance(event, thesis)
        score_row = RelevanceScore(
            event_id=event.id,
            thesis_id=thesis.id,
            score=rel["score"],
            confidence=rel["confidence"],
            reason=rel["reason"]
        )
        db.add(score_row)
        results.append(rel)

    db.commit()
    return {"event_id": event.id, "type": event.type, "scored_against": len(results)}