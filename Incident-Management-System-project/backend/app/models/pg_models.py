import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.postgres import Base
import enum

class WorkItemStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class AlertPriority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

class ComponentType(str, enum.Enum):
    RDBMS = "RDBMS"
    NOSQL = "NOSQL"
    CACHE = "CACHE"
    API = "API"
    QUEUE = "QUEUE"
    MCP = "MCP"

class WorkItem(Base):
    __tablename__ = "work_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    component_type: Mapped[str] = mapped_column(SAEnum(ComponentType), nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(WorkItemStatus), default=WorkItemStatus.OPEN, nullable=False)
    priority: Mapped[str] = mapped_column(SAEnum(AlertPriority), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    signal_count: Mapped[int] = mapped_column(default=1)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    mttr_seconds: Mapped[float] = mapped_column(Float, nullable=True)

    rca: Mapped["RCA"] = relationship("RCA", back_populates="work_item", uselist=False, cascade="all, delete-orphan")

class RCA(Base):
    __tablename__ = "rcas"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    work_item_id: Mapped[str] = mapped_column(String, ForeignKey("work_items.id"), nullable=False, unique=True)
    incident_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    incident_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    root_cause_category: Mapped[str] = mapped_column(String(100), nullable=False)
    fix_applied: Mapped[str] = mapped_column(Text, nullable=False)
    prevention_steps: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    work_item: Mapped["WorkItem"] = relationship("WorkItem", back_populates="rca")
