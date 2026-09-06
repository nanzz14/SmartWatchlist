from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.models import WatchlistItem, Thesis, Event, RelevanceScore
from app.config import settings

def generate_digest(db: Session, user_id: int, stock_id: str | None = None):
    query = db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id)
    if stock_id:
        query = query.filter(WatchlistItem.stock_id == stock_id)

    items = query.all()
    results = []

    for item in items:
        thesis = item.thesis
        if not thesis:
            continue

        # Events since last review
        scores = (
            db.query(RelevanceScore)
            .join(Event)
            .filter(
                RelevanceScore.thesis_id == thesis.id,
                Event.timestamp >= thesis.last_reviewed_at
            )
            .all()
        )

        materially = []
        not_relevant = []

        for s in scores:
            out = {
                "event_id": s.event_id,
                "score": s.score,
                "confidence": s.confidence,
                "reason": s.reason,
                "event_type": s.event.type,
                "event_timestamp": s.event.timestamp,
                "payload": s.event.payload
            }
            if s.score >= settings.RELEVANT_SCORE_THRESHOLD:
                materially.append(out)
            else:
                not_relevant.append(out)

        results.append({
            "stock_id": item.stock_id,
            "materially_relevant": sorted(materially, key=lambda x: x["score"], reverse=True),
            "changed_but_not_relevant": not_relevant,
            "quiet": len(materially) == 0 and len(not_relevant) == 0,
            "last_reviewed_at": thesis.last_reviewed_at
        })

    return results