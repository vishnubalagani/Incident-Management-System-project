import time
from fastapi import APIRouter
from app.db.mongo import get_mongo_client
from app.db.redis_client import get_redis
from app.db.postgres import engine
from app.services.signal_processor import signal_queue, _processed_count, _last_metric_time
from app.models.schemas import HealthOut
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health():
    # Postgres
    pg_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        pg_status = "error"

    # MongoDB
    mongo_status = "ok"
    try:
        client = get_mongo_client()
        await client.admin.command("ping")
    except Exception:
        mongo_status = "error"

    # Redis
    redis_status = "ok"
    try:
        r = get_redis()
        await r.ping()
    except Exception:
        redis_status = "error"

    elapsed = time.monotonic() - _last_metric_time
    rate = _processed_count / elapsed if elapsed > 0 else 0.0

    return HealthOut(
        status="ok" if all(s == "ok" for s in [pg_status, mongo_status, redis_status]) else "degraded",
        postgres=pg_status,
        mongo=mongo_status,
        redis=redis_status,
        queue_depth=signal_queue.qsize(),
        signals_per_sec=round(rate, 2),
    )
