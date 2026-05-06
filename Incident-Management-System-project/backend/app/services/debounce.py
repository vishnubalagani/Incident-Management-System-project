"""
Debounce engine:
- Tracks signals per component_id in a time window
- If threshold reached → reuse existing work_item_id
- Thread-safe via asyncio.Lock per component
"""
import asyncio
import time
from dataclasses import dataclass, field
from app.config import settings


@dataclass
class ComponentWindow:
    work_item_id: str
    count: int = 1
    window_start: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class DebounceService:
    def __init__(self):
        self._windows: dict[str, ComponentWindow] = {}
        self._global_lock = asyncio.Lock()

    async def get_or_create_work_item_id(
        self,
        component_id: str,
        create_fn,  # async callable that creates a new WorkItem and returns its id
    ) -> tuple[str, bool]:
        """
        Returns (work_item_id, is_debounced).
        is_debounced=True means this signal was merged into an existing work item.
        """
        async with self._global_lock:
            window = self._windows.get(component_id)
            now = time.monotonic()

            if window is not None:
                elapsed = now - window.window_start
                if elapsed <= settings.debounce_window_seconds:
                    window.count += 1
                    return window.work_item_id, True
                else:
                    # Window expired — start fresh
                    del self._windows[component_id]

            # New window: create a work item
            work_item_id = await create_fn()
            self._windows[component_id] = ComponentWindow(work_item_id=work_item_id)
            return work_item_id, False

    def get_window_count(self, component_id: str) -> int:
        w = self._windows.get(component_id)
        return w.count if w else 0


debounce_service = DebounceService()
