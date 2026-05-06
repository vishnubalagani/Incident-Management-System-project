import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.db.postgres import init_db
from app.db.mongo import connect_mongo, close_mongo
from app.db.redis_client import connect_redis, close_redis
from app.api import signals, work_items, health
from app.services.signal_processor import signal_worker, metrics_reporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    logger.info("Starting Incident Management System...")
    await connect_mongo()
    await connect_redis()
    await init_db()

    # Spawn background workers (non-blocking)
    worker_tasks = [
        asyncio.create_task(signal_worker(), name="signal_worker"),
        asyncio.create_task(metrics_reporter(), name="metrics_reporter"),
    ]
    logger.info("Background workers started")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("Shutting down...")
    for t in worker_tasks:
        t.cancel()
    await close_mongo()
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(signals.router, prefix="/api")
app.include_router(work_items.router, prefix="/api")
app.include_router(health.router)


@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "running", "docs": "/docs"}
