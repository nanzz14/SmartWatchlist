"""
Live data ingestion endpoint.

Pulls real-time price data from Yahoo Finance and news from RSS feeds
for all watchlisted stocks, then runs each event through the existing
tag → relevance pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event, RelevanceScore, Thesis, WatchlistItem
from app.services.market_data import fetch_price_events, fetch_stock_info
from app.services.news_feed import fetch_news_events
from app.services.relevance import calculate_relevance
from app.services.tagging import tag_event

router = APIRouter(prefix="/ingest", tags=["ingestion"])


def _process_raw_events(raw_events: list, db: Session) -> list:
    """Tag, store, and score a batch of raw event dicts."""
    results = []
    for raw in raw_events:
        # Convert ISO timestamp strings back to datetime objects
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            try:
                raw["timestamp"] = datetime.fromisoformat(ts)
            except ValueError:
                raw["timestamp"] = datetime.now(timezone.utc)

        tagged = tag_event(raw)
        event = Event(**tagged)
        db.add(event)
        db.flush()

        # Score against all theses watching this stock
        theses = (
            db.query(Thesis)
            .join(WatchlistItem)
            .filter(WatchlistItem.stock_id == event.stock_id)
            .all()
        )

        scored = 0
        for thesis in theses:
            rel = calculate_relevance(event, thesis)
            db.add(RelevanceScore(
                event_id=event.id,
                thesis_id=thesis.id,
                score=rel["score"],
                confidence=rel["confidence"],
                reason=rel["reason"],
            ))
            scored += 1

        results.append({
            "event_id": event.id,
            "stock_id": event.stock_id,
            "type": event.type,
            "source": event.source,
            "scored_against": scored,
        })

    db.commit()
    return results


@router.post("/run")
def run_ingestion(db: Session = Depends(get_db)):
    """
    Trigger a full ingestion cycle:
    1. Find all unique stocks in the watchlist
    2. Fetch price events from Yahoo Finance
    3. Fetch news from RSS feeds
    4. Tag + score every event
    """
    # Get all unique watchlisted stock IDs
    stock_ids = [
        row[0]
        for row in db.query(WatchlistItem.stock_id).distinct().all()
    ]

    if not stock_ids:
        return {"status": "no_watchlist", "message": "No stocks in watchlist"}

    all_raw: list = []
    stock_info_map: dict = {}

    for sid in stock_ids:
        # Price events from yfinance
        price_events = fetch_price_events(sid, period="5d")
        all_raw.extend(price_events)

        # News events from RSS
        news_events = fetch_news_events(sid, max_items=5)
        all_raw.extend(news_events)

        # Grab stock info for the response
        stock_info_map[sid] = fetch_stock_info(sid)

    results = _process_raw_events(all_raw, db)

    return {
        "status": "ok",
        "stocks_scanned": stock_ids,
        "stock_info": stock_info_map,
        "events_ingested": len(results),
        "details": results,
    }


@router.post("/stock/{stock_id}")
def ingest_single_stock(stock_id: str, db: Session = Depends(get_db)):
    """Ingest data for a single stock (on-demand)."""
    stock_id = stock_id.upper()

    price_events = fetch_price_events(stock_id, period="5d")
    news_events = fetch_news_events(stock_id, max_items=5)
    all_raw = price_events + news_events

    if not all_raw:
        return {
            "status": "no_data",
            "stock_id": stock_id,
            "message": "No events found from Yahoo Finance or RSS",
        }

    results = _process_raw_events(all_raw, db)
    info = fetch_stock_info(stock_id)

    return {
        "status": "ok",
        "stock_id": stock_id,
        "stock_info": info,
        "events_ingested": len(results),
        "details": results,
    }
