from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgres import get_db
from app.db.mongo import get_signals_collection
from app.models.schemas import WorkItemOut, WorkItemStatusUpdate, RCACreate, RCAOut
from app.services.work_item_service import (
    list_work_items, get_work_item, transition_status,
    submit_rca, get_dashboard,
)
from app.core.state_machine import InvalidTransitionError

router = APIRouter(prefix="/work-items", tags=["work-items"])


@router.get("", response_model=list[WorkItemOut])
async def get_all_work_items(status: str = None, session: AsyncSession = Depends(get_db)):
    return await list_work_items(session, status)


@router.get("/dashboard")
async def dashboard(session: AsyncSession = Depends(get_db)):
    """Cached dashboard state — avoids hitting Postgres on every UI refresh."""
    return await get_dashboard(session)


@router.get("/{work_item_id}", response_model=WorkItemOut)
async def get_one(work_item_id: str, session: AsyncSession = Depends(get_db)):
    wi = await get_work_item(session, work_item_id)
    if not wi:
        raise HTTPException(status_code=404, detail="Work item not found")
    return wi


@router.get("/{work_item_id}/signals")
async def get_signals_for_item(work_item_id: str):
    """Fetch all raw signals (from MongoDB) linked to this work item."""
    col = get_signals_collection()
    cursor = col.find({"work_item_id": work_item_id}, {"_id": 0}).sort("timestamp", -1).limit(200)
    signals = await cursor.to_list(length=200)
    return {"signals": signals, "count": len(signals)}


@router.patch("/{work_item_id}/status", response_model=WorkItemOut)
async def update_status(
    work_item_id: str,
    update: WorkItemStatusUpdate,
    session: AsyncSession = Depends(get_db),
):
    try:
        return await transition_status(session, work_item_id, update)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{work_item_id}/rca", response_model=RCAOut)
async def create_rca(
    work_item_id: str,
    rca_data: RCACreate,
    session: AsyncSession = Depends(get_db),
):
    try:
        return await submit_rca(session, work_item_id, rca_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
