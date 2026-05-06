"""
Async signal processor:
- Reads from asyncio.Queue (backpressure buffer)
- Persists raw signal to MongoDB
- Creates/merges WorkItem in PostgreSQL via debounce logic
- Updates Redis dashboard cache
"""
import asyncio
import uuid
import time
from datetime import datetime
from app.config import settings
from app.db.mongo import get_signals_collection
from app.db.postgres import AsyncSessionLocal
from app.db.redis_client import get_redis
from app.models.pg_models import WorkItem, ComponentType
from app.models.schemas import SignalPayload
from app.core.alert_strategy import get_alert_strategy
from app.services.debounce import debounce_service
import json
import logging

logger = logging.getLogger(__name__)

# Global queue — this is the backpressure buffer
signal_queue: asyncio.Queue = asyncio.Queue(maxsize=50_000)

# Throughput tracking
_processed_count = 0
_last_metric_time = time.monotonic()


async def enqueue_signal(payload: SignalPayload) -> str:
    """Non-blocking enqueue. Raises QueueFull if overwhelmed."""
    signal_id = str(uuid.uuid4())
    item = {"signal_id": signal_id, "payload": payload, "timestamp": datetime.utcnow()}
    try:
        signal_queue.put_nowait(item)
    except asyncio.QueueFull:
        logger.warning("Signal queue full — dropping signal for %s", payload.component_id)
        raise
    return signal_id


async def _create_work_item(payload: SignalPayload) -> str:
    strategy = get_alert_strategy(ComponentType(payload.component_type))
    async with AsyncSessionLocal() as session:
        wi = WorkItem(
            component_id=payload.component_id,
            component_type=payload.component_type,
            priority=strategy.get_priority(),
            title=strategy.get_title(payload.component_id, payload.error_code),
        )
        session.add(wi)
        await session.commit()
        await session.refresh(wi)
        return wi.id


async def _process_one(item: dict):
    global _processed_count
    payload: SignalPayload = item["payload"]
    signal_id: str = item["signal_id"]
    timestamp: datetime = item["timestamp"]

    # 1. Debounce → get/create work item
    work_item_id, debounced = await debounce_service.get_or_create_work_item_id(
        payload.component_id,
        lambda: _create_work_item(payload),
    )

    # 2. Persist raw signal to MongoDB
    signals_col = get_signals_collection()
    await signals_col.insert_one({
        "signal_id": signal_id,
        "work_item_id": work_item_id,
        "component_id": payload.component_id,
        "component_type": payload.component_type,
        "error_code": payload.error_code,
        "message": payload.message,
        "latency_ms": payload.latency_ms,
        "metadata": payload.metadata,
        "timestamp": timestamp,
        "debounced": debounced,
    })

    # 3. If debounced, increment signal_count on WorkItem
    if debounced:
        async with AsyncSessionLocal() as session:
            wi = await session.get(WorkItem, work_item_id)
            if wi:
                wi.signal_count += 1
                await session.commit()

    # 4. Update Redis dashboard cache
    redis = get_redis()
    if redis:
        await redis.setex(
            f"wi:{work_item_id}:signal_count",
            300,
            debounce_service.get_window_count(payload.component_id),
        )

    _processed_count += 1
    return work_item_id


async def signal_worker():
    """Long-running async worker — drains the queue continuously."""
    logger.info("Signal worker started")
    while True:
        try:
            item = await asyncio.wait_for(signal_queue.get(), timeout=1.0)
            await _process_one(item)
            signal_queue.task_done()
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.exception("Error processing signal: %s", e)


async def metrics_reporter():
    """Logs throughput every N seconds to console."""
    global _processed_count, _last_metric_time
    while True:
        await asyncio.sleep(settings.metrics_interval_seconds)
        now = time.monotonic()
        elapsed = now - _last_metric_time
        rate = _processed_count / elapsed if elapsed > 0 else 0
        logger.info(
            "[METRICS] signals/sec=%.1f | queue_depth=%d | total_processed=%d",
            rate, signal_queue.qsize(), _processed_count,
        )
        _processed_count = 0
        _last_metric_time = now
