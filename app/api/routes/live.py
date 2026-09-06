from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.live import last_run, subscribe, unsubscribe

router = APIRouter(prefix="/live", tags=["live"])


@router.get("/status")
def live_status():
    return last_run()


@router.get("/stream")
async def live_stream():
    queue = subscribe()

    async def events():
        try:
            yield f"data: {json.dumps({'type': 'hello', **last_run()})}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                yield f"data: {json.dumps(payload)}\n\n"
        finally:
            unsubscribe(queue)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
