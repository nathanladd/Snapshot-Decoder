"""
Chart usage tracking — how often each chart is actually opened.

The quick-chart panel shows one row per family with a trailing overflow menu,
so order decides what stays visible. Sorting most-used first means the overflow
menu only ever holds the charts this user ignores.

Keyed by action_id, the same join key the rest of the chart system runs on, so
built-ins and My Charts share one mechanism and one file. Mirrors the
UserChartStore persistence pattern: per-user JSON at
%APPDATA%\\SnapshotDecoder\\chart_usage.json, graceful degradation on
corrupt/missing files.
"""

import json
from datetime import datetime
from typing import Any, Dict, Tuple

from domain.user_paths import user_data_file

_SCHEMA_VERSION = 1


class ChartUsageStore:
    """Singleton click-count store used to order the quick-chart rows."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._counts: Dict[str, int] = {}
            cls._instance._last_used: Dict[str, str] = {}
            cls._instance._loaded = False
        return cls._instance

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _file_path(self) -> str:
        return user_data_file("chart_usage.json")

    def load(self):
        """Load counts from JSON (or degrade to empty)."""
        path = self._file_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._counts = {
                str(k): int(v)
                for k, v in (data.get("counts") or {}).items()
                if isinstance(v, (int, float))
            }
            self._last_used = {
                str(k): str(v) for k, v in (data.get("last_used") or {}).items()
            }
        except FileNotFoundError:
            self._counts = {}
            self._last_used = {}
        except Exception:
            self._counts = {}
            self._last_used = {}
        self._loaded = True

    def save(self):
        """Persist counts to JSON."""
        payload: Dict[str, Any] = {
            "schema_version": _SCHEMA_VERSION,
            "counts": dict(self._counts),
            "last_used": dict(self._last_used),
        }
        try:
            with open(self._file_path(), "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
        except Exception as exc:
            print(f"Warning: Could not save chart usage: {exc}")

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    # ------------------------------------------------------------------
    # Queries / updates
    # ------------------------------------------------------------------
    def record(self, action_id: str):
        """Count one use of a chart and persist it."""
        if not action_id:
            return
        self._ensure_loaded()
        self._counts[action_id] = self._counts.get(action_id, 0) + 1
        self._last_used[action_id] = datetime.now().isoformat()
        self.save()

    def count(self, action_id: str) -> int:
        self._ensure_loaded()
        return self._counts.get(action_id, 0)

    def last_used(self, action_id: str) -> str:
        self._ensure_loaded()
        return self._last_used.get(action_id, "")

    def order_key(self, action_id: str, declared_index: int) -> Tuple[int, int]:
        """Sort key for a chart button: most-used first, declared order breaks ties.

        With no history every count is 0, so the row renders in exactly its
        declared order — personalization emerges with use rather than
        rearranging the panel for a first-time user.
        """
        return (-self.count(action_id), declared_index)

    def forget(self, action_id: str):
        """Drop a chart's history (e.g. a deleted My Chart)."""
        self._ensure_loaded()
        changed = self._counts.pop(action_id, None) is not None
        changed = self._last_used.pop(action_id, None) is not None or changed
        if changed:
            self.save()
