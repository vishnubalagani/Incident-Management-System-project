from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.pg_models import WorkItemStatus, AlertPriority, ComponentType


# ── Signal Ingestion ──────────────────────────────────────────────
class SignalPayload(BaseModel):
    component_id: str = Field(..., example="CACHE_CLUSTER_01")
    component_type: ComponentType
    error_code: str = Field(..., example="CONNECTION_TIMEOUT")
    message: str
    latency_ms: Optional[float] = None
    metadata: Optional[dict] = None

class SignalResponse(BaseModel):
    signal_id: str
    work_item_id: str
    debounced: bool
    message: str


# ── Work Item ─────────────────────────────────────────────────────
class WorkItemOut(BaseModel):
    id: str
    component_id: str
    component_type: str
    status: WorkItemStatus
    priority: AlertPriority
    title: str
    signal_count: int
    start_time: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    mttr_seconds: Optional[float]

    class Config:
        from_attributes = True

class WorkItemStatusUpdate(BaseModel):
    status: WorkItemStatus


# ── RCA ───────────────────────────────────────────────────────────
class RCACreate(BaseModel):
    incident_start: datetime
    incident_end: datetime
    root_cause_category: str = Field(..., example="Infrastructure failure")
    fix_applied: str = Field(..., min_length=10)
    prevention_steps: str = Field(..., min_length=10)

class RCAOut(BaseModel):
    id: str
    work_item_id: str
    incident_start: datetime
    incident_end: datetime
    root_cause_category: str
    fix_applied: str
    prevention_steps: str
    submitted_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────
class DashboardItem(BaseModel):
    id: str
    component_id: str
    status: str
    priority: str
    title: str
    signal_count: int
    start_time: datetime

class SignalOut(BaseModel):
    signal_id: str
    component_id: str
    error_code: str
    message: str
    timestamp: datetime
    work_item_id: Optional[str]

class HealthOut(BaseModel):
    status: str
    postgres: str
    mongo: str
    redis: str
    queue_depth: int
    signals_per_sec: float
