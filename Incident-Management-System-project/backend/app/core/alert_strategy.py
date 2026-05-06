"""
Strategy Pattern — Alert priority per component type
P0 = critical (RDBMS, MCP)
P1 = high     (API, QUEUE)
P2 = medium   (NOSQL)
P3 = low      (CACHE)
"""
from abc import ABC, abstractmethod
from app.models.pg_models import AlertPriority, ComponentType


class AlertStrategy(ABC):
    @abstractmethod
    def get_priority(self) -> AlertPriority:
        pass

    @abstractmethod
    def get_title(self, component_id: str, error_code: str) -> str:
        pass


class RDBMSAlertStrategy(AlertStrategy):
    def get_priority(self): return AlertPriority.P0
    def get_title(self, component_id, error_code):
        return f"[P0] RDBMS failure on {component_id}: {error_code}"


class MCPAlertStrategy(AlertStrategy):
    def get_priority(self): return AlertPriority.P0
    def get_title(self, component_id, error_code):
        return f"[P0] MCP host failure on {component_id}: {error_code}"


class APIAlertStrategy(AlertStrategy):
    def get_priority(self): return AlertPriority.P1
    def get_title(self, component_id, error_code):
        return f"[P1] API degraded on {component_id}: {error_code}"


class QueueAlertStrategy(AlertStrategy):
    def get_priority(self): return AlertPriority.P1
    def get_title(self, component_id, error_code):
        return f"[P1] Queue failure on {component_id}: {error_code}"


class NoSQLAlertStrategy(AlertStrategy):
    def get_priority(self): return AlertPriority.P2
    def get_title(self, component_id, error_code):
        return f"[P2] NoSQL issue on {component_id}: {error_code}"


class CacheAlertStrategy(AlertStrategy):
    def get_priority(self): return AlertPriority.P2
    def get_title(self, component_id, error_code):
        return f"[P2] Cache failure on {component_id}: {error_code}"


_STRATEGY_MAP: dict[ComponentType, AlertStrategy] = {
    ComponentType.RDBMS: RDBMSAlertStrategy(),
    ComponentType.MCP: MCPAlertStrategy(),
    ComponentType.API: APIAlertStrategy(),
    ComponentType.QUEUE: QueueAlertStrategy(),
    ComponentType.NOSQL: NoSQLAlertStrategy(),
    ComponentType.CACHE: CacheAlertStrategy(),
}


def get_alert_strategy(component_type: ComponentType) -> AlertStrategy:
    return _STRATEGY_MAP.get(component_type, APIAlertStrategy())
