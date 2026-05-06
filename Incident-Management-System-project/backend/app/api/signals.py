import asyncio
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import SignalPayload, SignalResponse
from app.services.signal_processor import enqueue_signal, signal_queue

router = APIRouter(prefix="/signals", tags=["signals"])
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=SignalResponse)
@limiter.limit("600/minute")
async def ingest_signal(request: Request, payload: SignalPayload):
    """
    Ingest a single signal. Non-blocking — drops into asyncio.Queue.
    Rate limited to 600 req/min per client IP.
    """
    try:
        signal_id = await enqueue_signal(payload)
    except asyncio.QueueFull:
        raise HTTPException(status_code=429, detail="Signal queue full — system under backpressure")

    return SignalResponse(
        signal_id=signal_id,
        work_item_id="pending",   # actual ID assigned by worker asynchronously
        debounced=False,
        message="Signal enqueued for processing",
    )


@router.post("/batch", tags=["signals"])
@limiter.limit("60/minute")
async def ingest_batch(request: Request, payloads: list[SignalPayload]):
    """Ingest up to 100 signals in one call."""
    if len(payloads) > 100:
        raise HTTPException(status_code=400, detail="Max 100 signals per batch")
    results = []
    for payload in payloads:
        try:
            sid = await enqueue_signal(payload)
            results.append({"signal_id": sid, "status": "queued"})
        except asyncio.QueueFull:
            results.append({"signal_id": None, "status": "dropped"})
    return {"results": results, "queue_depth": signal_queue.qsize()}
