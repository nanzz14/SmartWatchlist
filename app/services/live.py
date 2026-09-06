"""
In-process live hub: background ingest loop + SSE subscribers.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

_subscribers: List[asyncio.Queue] = []
_last_run: Dict[str, Any] = {
    "status": "starting",
    "at": None,
    "events_ingested": 0,
    "stock_info": {},
}


def last_run() -> Dict[str, Any]:
    return dict(_last_run)


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=32)
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    if q in _subscribers:
        _subscribers.remove(q)


async def publish(payload: Dict[str, Any]) -> None:
    dead = []
    for q in _subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        unsubscribe(q)


def _run_cycle() -> Dict[str, Any]:
    from app.api.routes.ingestion import run_ingestion_cycle

    db = SessionLocal()
    try:
        result = run_ingestion_cycle(db)
        return result
    finally:
        db.close()


async def ingest_loop() -> None:
    await asyncio.sleep(3)
    while True:
        try:
            result = await asyncio.to_thread(_run_cycle)
            _last_run.update({
                "status": result.get("status", "ok"),
                "at": datetime.now(timezone.utc).isoformat(),
                "events_ingested": result.get("events_ingested", 0),
                "stocks_scanned": result.get("stocks_scanned", []),
                "stock_info": result.get("stock_info", {}),
            })
            await publish({"type": "ingest", **_last_run})
            logger.info(
                "Live ingest: %s (%s new events)",
                _last_run["status"],
                _last_run["events_ingested"],
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Live ingest failed: %s", exc)
            _last_run.update({
                "status": "error",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            })
            await publish({"type": "ingest", **_last_run})

        await asyncio.sleep(settings.INGEST_INTERVAL_SECONDS)
