"""
Application Settings Manager

JSON-backed singleton for all user-configurable settings.
Manages chart appearance and debug logging preferences with
automatic persistence to a settings.json file.
"""

import json
import os
import sys
from typing import Any, Dict


# Default settings values
_DEFAULTS: Dict[str, Any] = {
    # Chart Appearance
    "legend_font_size": 9,
    "line_width": 1.0,
    "grid_linewidth": 0.6,
    "marker_size": 6.0,
    
    # Updates
    "auto_check_updates": True,

    # Debug / Logging
    "enable_pid_debug": False,
    "log_interval": 1.0,
    "log_on_stop": True,
    "position_threshold": 0.01,
}


def _settings_file_path() -> str:
    """Return the path to the settings JSON file next to the executable / project root."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "settings.json")


class AppSettings:
    """
    Singleton settings manager backed by a JSON file.

    Usage:
        from domain.app_settings import app_settings
        print(app_settings.line_width)
        app_settings.line_width = 2.0
        app_settings.save()
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data: Dict[str, Any] = {}
            cls._instance._loaded = False
        return cls._instance

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def load(self):
        """Load settings from the JSON file (or use defaults)."""
        path = _settings_file_path()
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                # Merge with defaults so new keys are always present
                self._data = {**_DEFAULTS, **stored}
            except Exception:
                self._data = dict(_DEFAULTS)
        else:
            self._data = dict(_DEFAULTS)
        self._loaded = True

    def save(self):
        """Persist current settings to JSON."""
        path = _settings_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4)
        except Exception as exc:
            print(f"Warning: Could not save settings: {exc}")

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    # ------------------------------------------------------------------
    # Bulk access
    # ------------------------------------------------------------------
    def get_all(self) -> Dict[str, Any]:
        """Return a copy of all settings."""
        self._ensure_loaded()
        return dict(self._data)

    def set_many(self, values: Dict[str, Any]):
        """Update multiple settings at once (does NOT auto-save)."""
        self._ensure_loaded()
        self._data.update(values)

    def reset_to_defaults(self):
        """Reset all settings to their default values and save."""
        self._data = dict(_DEFAULTS)
        self.save()

    # ------------------------------------------------------------------
    # Chart Appearance properties
    # ------------------------------------------------------------------
    @property
    def legend_font_size(self) -> int:
        self._ensure_loaded()
        return int(self._data["legend_font_size"])

    @legend_font_size.setter
    def legend_font_size(self, value: int):
        self._ensure_loaded()
        self._data["legend_font_size"] = int(value)

    @property
    def line_width(self) -> float:
        self._ensure_loaded()
        return float(self._data["line_width"])

    @line_width.setter
    def line_width(self, value: float):
        self._ensure_loaded()
        self._data["line_width"] = float(value)

    @property
    def grid_linewidth(self) -> float:
        self._ensure_loaded()
        return float(self._data["grid_linewidth"])

    @grid_linewidth.setter
    def grid_linewidth(self, value: float):
        self._ensure_loaded()
        self._data["grid_linewidth"] = float(value)

    @property
    def marker_size(self) -> float:
        self._ensure_loaded()
        return float(self._data["marker_size"])

    @marker_size.setter
    def marker_size(self, value: float):
        self._ensure_loaded()
        self._data["marker_size"] = float(value)

    # ------------------------------------------------------------------
    # Debug / Logging properties
    # ------------------------------------------------------------------
    @property
    def enable_pid_debug(self) -> bool:
        self._ensure_loaded()
        return bool(self._data["enable_pid_debug"])

    @enable_pid_debug.setter
    def enable_pid_debug(self, value: bool):
        self._ensure_loaded()
        self._data["enable_pid_debug"] = bool(value)

    @property
    def log_interval(self) -> float:
        self._ensure_loaded()
        return float(self._data["log_interval"])

    @log_interval.setter
    def log_interval(self, value: float):
        self._ensure_loaded()
        self._data["log_interval"] = float(value)

    @property
    def log_on_stop(self) -> bool:
        self._ensure_loaded()
        return bool(self._data["log_on_stop"])

    @log_on_stop.setter
    def log_on_stop(self, value: bool):
        self._ensure_loaded()
        self._data["log_on_stop"] = bool(value)

    @property
    def position_threshold(self) -> float:
        self._ensure_loaded()
        return float(self._data["position_threshold"])

    @position_threshold.setter
    def position_threshold(self, value: float):
        self._ensure_loaded()
        self._data["position_threshold"] = float(value)


# Singleton instance
app_settings = AppSettings()
