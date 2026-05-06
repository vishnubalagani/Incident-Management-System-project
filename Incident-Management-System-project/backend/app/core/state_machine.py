"""
State Pattern — WorkItem lifecycle
OPEN → INVESTIGATING → RESOLVED → CLOSED (requires RCA)
"""
from abc import ABC, abstractmethod
from app.models.pg_models import WorkItemStatus


class InvalidTransitionError(Exception):
    pass


class State(ABC):
    @abstractmethod
    def next_status(self) -> WorkItemStatus:
        pass

    @abstractmethod
    def can_transition_to(self, target: WorkItemStatus) -> bool:
        pass


class OpenState(State):
    def next_status(self): return WorkItemStatus.INVESTIGATING
    def can_transition_to(self, target):
        return target == WorkItemStatus.INVESTIGATING


class InvestigatingState(State):
    def next_status(self): return WorkItemStatus.RESOLVED
    def can_transition_to(self, target):
        return target == WorkItemStatus.RESOLVED


class ResolvedState(State):
    def next_status(self): return WorkItemStatus.CLOSED
    def can_transition_to(self, target):
        return target == WorkItemStatus.CLOSED


class ClosedState(State):
    def next_status(self): return WorkItemStatus.CLOSED
    def can_transition_to(self, target): return False


_STATE_MAP: dict[WorkItemStatus, State] = {
    WorkItemStatus.OPEN: OpenState(),
    WorkItemStatus.INVESTIGATING: InvestigatingState(),
    WorkItemStatus.RESOLVED: ResolvedState(),
    WorkItemStatus.CLOSED: ClosedState(),
}


def get_state(status: WorkItemStatus) -> State:
    return _STATE_MAP[status]


def validate_transition(current: WorkItemStatus, target: WorkItemStatus) -> None:
    state = get_state(current)
    if not state.can_transition_to(target):
        raise InvalidTransitionError(
            f"Cannot transition from {current} to {target}. "
            f"Next allowed: {state.next_status()}"
        )
