import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pg_models import WorkItem, RCA, WorkItemStatus
from app.models.schemas import RCACreate, WorkItemStatusUpdate
from app.core.state_machine import validate_transition, InvalidTransitionError
from app.db.redis_client import get_redis
import logging

logger = logging.getLogger(__name__)


async def list_work_items(session: AsyncSession, status: str = None) -> list[WorkItem]:
    q = select(WorkItem).order_by(WorkItem.start_time.desc())
    if status:
        q = q.where(WorkItem.status == status)
    result = await session.execute(q)
    return result.scalars().all()


async def get_work_item(session: AsyncSession, work_item_id: str) -> WorkItem | None:
    return await session.get(WorkItem, work_item_id)


async def transition_status(
    session: AsyncSession,
    work_item_id: str,
    update: WorkItemStatusUpdate,
) -> WorkItem:
    wi = await session.get(WorkItem, work_item_id)
    if not wi:
        raise ValueError("Work item not found")

    validate_transition(wi.status, update.status)

    # Block CLOSED if RCA is missing
    if update.status == WorkItemStatus.CLOSED:
        rca = await session.get(RCA, wi.id)
        if not rca:
            # Try by work_item_id
            res = await session.execute(select(RCA).where(RCA.work_item_id == work_item_id))
            rca = res.scalar_one_or_none()
        if not rca:
            raise ValueError("Cannot close work item: RCA is missing or incomplete.")

        wi.closed_at = datetime.utcnow()
        wi.mttr_seconds = (wi.closed_at - wi.start_time).total_seconds()

    wi.status = update.status
    wi.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(wi)

    # Invalidate Redis cache for this item
    redis = get_redis()
    if redis:
        await redis.delete(f"dashboard:all")

    return wi


async def submit_rca(session: AsyncSession, work_item_id: str, rca_data: RCACreate) -> RCA:
    wi = await session.get(WorkItem, work_item_id)
    if not wi:
        raise ValueError("Work item not found")

    # Check if RCA already exists
    res = await session.execute(select(RCA).where(RCA.work_item_id == work_item_id))
    existing = res.scalar_one_or_none()
    if existing:
        raise ValueError("RCA already submitted for this work item")

    # 🔥 ADD THESE TWO LINES (THIS IS YOUR FIX)
    incident_start = rca_data.incident_start.replace(tzinfo=None)
    incident_end = rca_data.incident_end.replace(tzinfo=None)

    # use fixed values
    rca = RCA(
        work_item_id=work_item_id,
        incident_start=incident_start,
        incident_end=incident_end,
        root_cause_category=rca_data.root_cause_category,
        fix_applied=rca_data.fix_applied,
        prevention_steps=rca_data.prevention_steps,
    )

    session.add(rca)
    await session.commit()
    await session.refresh(rca)
    return rca


async def get_dashboard(session: AsyncSession) -> list[dict]:
    """Returns cached dashboard or queries Postgres."""
    redis = get_redis()
    if redis:
        cached = await redis.get("dashboard:all")
        if cached:
            return json.loads(cached)

    items = await list_work_items(session)
    data = [
        {
            "id": wi.id,
            "component_id": wi.component_id,
            "component_type": wi.component_type,
            "status": wi.status,
            "priority": wi.priority,
            "title": wi.title,
            "signal_count": wi.signal_count,
            "start_time": wi.start_time.isoformat(),
            "mttr_seconds": wi.mttr_seconds,
        }
        for wi in items
    ]

    if redis:
        await redis.setex("dashboard:all", 10, json.dumps(data))

    return data
