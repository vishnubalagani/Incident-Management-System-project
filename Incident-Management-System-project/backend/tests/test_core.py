import pytest
from app.core.state_machine import validate_transition, InvalidTransitionError
from app.models.pg_models import WorkItemStatus
from app.core.alert_strategy import get_alert_strategy, RDBMSAlertStrategy, CacheAlertStrategy
from app.models.pg_models import ComponentType, AlertPriority


# ── State Machine Tests ───────────────────────────────────────────

def test_valid_transition_open_to_investigating():
    validate_transition(WorkItemStatus.OPEN, WorkItemStatus.INVESTIGATING)  # should not raise

def test_valid_transition_investigating_to_resolved():
    validate_transition(WorkItemStatus.INVESTIGATING, WorkItemStatus.RESOLVED)

def test_valid_transition_resolved_to_closed():
    validate_transition(WorkItemStatus.RESOLVED, WorkItemStatus.CLOSED)

def test_invalid_transition_open_to_closed():
    with pytest.raises(InvalidTransitionError):
        validate_transition(WorkItemStatus.OPEN, WorkItemStatus.CLOSED)

def test_invalid_transition_open_to_resolved():
    with pytest.raises(InvalidTransitionError):
        validate_transition(WorkItemStatus.OPEN, WorkItemStatus.RESOLVED)

def test_invalid_transition_closed_to_anything():
    with pytest.raises(InvalidTransitionError):
        validate_transition(WorkItemStatus.CLOSED, WorkItemStatus.OPEN)

def test_invalid_transition_skip_investigating():
    with pytest.raises(InvalidTransitionError):
        validate_transition(WorkItemStatus.INVESTIGATING, WorkItemStatus.CLOSED)


# ── Alert Strategy Tests ──────────────────────────────────────────

def test_rdbms_strategy_is_p0():
    strategy = get_alert_strategy(ComponentType.RDBMS)
    assert strategy.get_priority() == AlertPriority.P0

def test_cache_strategy_is_p2():
    strategy = get_alert_strategy(ComponentType.CACHE)
    assert strategy.get_priority() == AlertPriority.P2

def test_mcp_strategy_is_p0():
    strategy = get_alert_strategy(ComponentType.MCP)
    assert strategy.get_priority() == AlertPriority.P0

def test_api_strategy_is_p1():
    strategy = get_alert_strategy(ComponentType.API)
    assert strategy.get_priority() == AlertPriority.P1

def test_rdbms_title_contains_component_id():
    strategy = get_alert_strategy(ComponentType.RDBMS)
    title = strategy.get_title("PG_PRIMARY_01", "CONNECTION_REFUSED")
    assert "PG_PRIMARY_01" in title
    assert "P0" in title

def test_cache_title_contains_error_code():
    strategy = get_alert_strategy(ComponentType.CACHE)
    title = strategy.get_title("REDIS_01", "TIMEOUT")
    assert "TIMEOUT" in title


# ── RCA Validation Tests ──────────────────────────────────────────

from pydantic import ValidationError
from app.models.schemas import RCACreate
from datetime import datetime

def test_rca_valid():
    rca = RCACreate(
        incident_start=datetime(2026, 5, 1, 10, 0),
        incident_end=datetime(2026, 5, 1, 12, 0),
        root_cause_category="Infrastructure failure",
        fix_applied="Restarted the primary DB node and promoted replica.",
        prevention_steps="Add automated failover and improve health checks.",
    )
    assert rca.fix_applied is not None

def test_rca_missing_fix_applied():
    with pytest.raises(ValidationError):
        RCACreate(
            incident_start=datetime(2026, 5, 1, 10, 0),
            incident_end=datetime(2026, 5, 1, 12, 0),
            root_cause_category="Network",
            fix_applied="short",   # too short — min_length=10
            prevention_steps="Will monitor.",
        )
