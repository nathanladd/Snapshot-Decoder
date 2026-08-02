"""
My Charts — user-authored chart templates.

JSON-backed singleton store for user-saved line charts, mirroring the
AppSettings persistence pattern (per-user JSON, graceful degradation on
corrupt/missing files). Lives at %APPDATA%\\SnapshotDecoder\\my_charts.json.

A UserChartDef is never added to QUICK_CHART_REGISTRY (that dict is a
module-global built once from the shipped definition files). Instead,
chart_widget.plot_quick_chart() falls back to UserChartStore.get() when an
action_id isn't a built-in, so a stored def rides the same
build/render/PDF-export pipeline as a built-in QuickChartDef.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from domain.quick_charts import QUICK_CHART_REGISTRY, QuickChartDef, slugify_chart_title
from domain.snaptypes import SnapType
from domain.user_paths import user_data_file, backup_corrupt_file
from infrastructure import log_error

_SCHEMA_VERSION = 1


def _range_to_list(value: Optional[Tuple[float, float]]) -> Optional[List[float]]:
    return list(value) if value is not None else None


def _range_from_list(value: Optional[List[float]]) -> Optional[Tuple[float, float]]:
    return tuple(value) if value is not None else None


@dataclass
class UserChartDef:
    """A user-saved chart template (v1: line charts only)."""

    action_id: str
    title: str
    primary_pids: List[str]
    secondary_pids: List[str] = field(default_factory=list)
    primary_range: Optional[Tuple[float, float]] = None
    secondary_range: Optional[Tuple[float, float]] = None
    chart_type: str = "line"
    snapshot_type: str = ""  # SnapType.name, e.g. "ECU_V1" -> which panel it shows in
    created: str = ""
    modified: str = ""
    schema_version: int = 1

    def to_quick_chart_def(self) -> QuickChartDef:
        """Produce the plain QuickChartDef the builder/renderer consume."""
        return QuickChartDef(
            action_id=self.action_id,
            title=self.title,
            primary_pids=list(self.primary_pids),
            secondary_pids=list(self.secondary_pids),
            primary_range=self.primary_range,
            secondary_range=self.secondary_range,
            chart_type=self.chart_type,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "title": self.title,
            "primary_pids": list(self.primary_pids),
            "secondary_pids": list(self.secondary_pids),
            "primary_range": _range_to_list(self.primary_range),
            "secondary_range": _range_to_list(self.secondary_range),
            "chart_type": self.chart_type,
            "snapshot_type": self.snapshot_type,
            "created": self.created,
            "modified": self.modified,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserChartDef":
        return cls(
            action_id=data["action_id"],
            title=data.get("title", ""),
            primary_pids=list(data.get("primary_pids", [])),
            secondary_pids=list(data.get("secondary_pids", [])),
            primary_range=_range_from_list(data.get("primary_range")),
            secondary_range=_range_from_list(data.get("secondary_range")),
            chart_type=data.get("chart_type", "line"),
            snapshot_type=data.get("snapshot_type", ""),
            created=data.get("created", ""),
            modified=data.get("modified", ""),
            schema_version=data.get("schema_version", 1),
        )


class UserChartStore:
    """Singleton CRUD store for UserChartDef, backed by my_charts.json.

    "CRUD" = Create, Read, Update, Delete — the four operations below
    (add/all·get/update/delete) cover the full lifecycle of a saved chart
    def, mirroring the same verbs a database table's API would expose.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._charts: List[UserChartDef] = []
            cls._instance._loaded = False
        return cls._instance

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _file_path(self) -> str:
        return user_data_file("my_charts.json")

    def load(self):
        """Load charts from JSON (or degrade to an empty list)."""
        path = self._file_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._charts = [UserChartDef.from_dict(d) for d in data.get("charts", [])]
        except FileNotFoundError:
            self._charts = []
        except Exception as exc:
            log_error(f"Corrupt My Charts file at {path}, resetting to empty: {exc}")
            backup_corrupt_file(path)
            self._charts = []
        self._loaded = True

    def save(self):
        """Persist all charts to JSON."""
        path = self._file_path()
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "charts": [c.to_dict() for c in self._charts],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
        except Exception as exc:
            log_error(f"Could not save My Charts to {path}: {exc}")

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def all(self) -> List[UserChartDef]:
        self._ensure_loaded()
        return list(self._charts)

    def for_type(self, snapshot_type: SnapType) -> List[UserChartDef]:
        """Charts saved against this snapshot type — the panel's population query."""
        self._ensure_loaded()
        type_name = snapshot_type.name if isinstance(snapshot_type, SnapType) else snapshot_type
        return [c for c in self._charts if c.snapshot_type == type_name]

    def get(self, action_id: str) -> Optional[UserChartDef]:
        self._ensure_loaded()
        for c in self._charts:
            if c.action_id == action_id:
                return c
        return None

    def is_title_available(self, title: str, exclude_id: Optional[str] = None) -> bool:
        """Reject titles that slugify to a built-in or existing user-chart slug."""
        self._ensure_loaded()
        slug = slugify_chart_title(title)
        if not slug:
            return False

        reserved = {slugify_chart_title(d.title) for d in QUICK_CHART_REGISTRY.values()}
        if slug in reserved:
            return False

        for c in self._charts:
            if c.action_id == exclude_id:
                continue
            if slugify_chart_title(c.title) == slug:
                return False

        return True

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def add(self, chart_def: UserChartDef):
        self._ensure_loaded()
        self._charts.append(chart_def)
        self.save()

    def update(self, chart_def: UserChartDef):
        self._ensure_loaded()
        for i, c in enumerate(self._charts):
            if c.action_id == chart_def.action_id:
                self._charts[i] = chart_def
                break
        self.save()

    def delete(self, action_id: str):
        self._ensure_loaded()
        self._charts = [c for c in self._charts if c.action_id != action_id]
        self.save()
