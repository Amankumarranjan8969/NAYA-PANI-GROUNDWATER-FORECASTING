from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from time import monotonic
from typing import Any


class WorkspaceStore:
    """Bounded in-memory cache for uploaded data and completed analyses."""

    def __init__(self, ttl_seconds: int = 24 * 60 * 60, max_workspaces: int = 16) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_workspaces = max_workspaces
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = RLock()

    def _remove_expired(self, now: float) -> None:
        expired = [
            key for key, (expires_at, _) in self._items.items()
            if expires_at <= now
        ]
        for key in expired:
            del self._items[key]

    def get(self, key: str) -> Any | None:
        with self._lock:
            now = monotonic()
            self._remove_expired(now)
            item = self._items.get(key)
            if item is None:
                return None
            _, value = item
            self._items[key] = (now + self._ttl_seconds, value)
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            now = monotonic()
            self._remove_expired(now)
            self._items[key] = (now + self._ttl_seconds, value)
            self._items.move_to_end(key)
            while len(self._items) > self._max_workspaces:
                self._items.popitem(last=False)

    def delete(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)


workspace_store = WorkspaceStore()
