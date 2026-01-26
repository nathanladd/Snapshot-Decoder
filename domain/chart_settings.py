"""
Global Chart Settings

Manages global settings for chart appearance including legend font size,
line width, and other configurable chart parameters.
"""

import json
import os
from typing import Dict, Any
from utils import resource_path


class ChartSettings:
    """
    Global chart settings manager.
    
    Provides centralized configuration for chart appearance with
    persistence to JSON file for user preferences.
    """
    
    # Default settings
    DEFAULT_SETTINGS = {
        "legend_font_size": 9,
        "line_width": 1.5,
        "grid_linewidth": 0.6,
        "marker_size": 6.0
    }
    
    def __init__(self):
        self.settings_file = resource_path("chart_settings.json")
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def load_settings(self):
        """Load settings from JSON file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                self._settings.update(loaded_settings)
        except Exception as e:
            print(f"Error loading chart settings: {e}")
            # Use defaults if loading fails
            self._settings = self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        """Save current settings to JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            print(f"Error saving chart settings: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        self._settings[key] = value
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings."""
        return self._settings.copy()
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self._settings = self.DEFAULT_SETTINGS.copy()
    
    @property
    def legend_font_size(self) -> int:
        """Get the legend font size."""
        return self.get_setting("legend_font_size", self.DEFAULT_SETTINGS["legend_font_size"])
    
    @legend_font_size.setter
    def legend_font_size(self, value: int):
        """Set the legend font size."""
        self.set_setting("legend_font_size", value)
    
    @property
    def line_width(self) -> float:
        """Get the line width for charts."""
        return self.get_setting("line_width", self.DEFAULT_SETTINGS["line_width"])
    
    @line_width.setter
    def line_width(self, value: float):
        """Set the line width for charts."""
        self.set_setting("line_width", value)
    
    @property
    def grid_linewidth(self) -> float:
        """Get the grid line width."""
        return self.get_setting("grid_linewidth", self.DEFAULT_SETTINGS["grid_linewidth"])
    
    @grid_linewidth.setter
    def grid_linewidth(self, value: float):
        """Set the grid line width."""
        self.set_setting("grid_linewidth", value)
    
    @property
    def marker_size(self) -> float:
        """Get the marker size."""
        return self.get_setting("marker_size", self.DEFAULT_SETTINGS["marker_size"])
    
    @marker_size.setter
    def marker_size(self, value: float):
        """Set the marker size."""
        self.set_setting("marker_size", value)


# Global instance
chart_settings = ChartSettings()
