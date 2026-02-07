"""
Live Values Widget for PySide6

Displays PID values in color-coded cards that update as the time slider moves.
PySide6 implementation with modern styling.
"""

import numpy as np
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QScrollArea, QStyle, QStyleOption
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor
import time

from domain.chart_config import ChartConfig
from domain.pid_interpolator import PIDInterpolator
from ui.color_manager import ColorManager
from infrastructure import debug, error
from pid_debug_config import get_pid_debug_setting, get_log_interval, get_log_on_stop, get_position_threshold


class PIDCard(QFrame):
    """A single PID value card with color coding for PySide6."""
    
    def __init__(self, pid_name: str, color: str, initial_value: float = 0.0, parent=None):
        super().__init__(parent)
        
        self.pid_name = pid_name
        self.color = QColor(color)
        self.value_label = None
        
        self._build_card(initial_value)
    
    def _build_card(self, initial_value: float):
        """Build the card layout with PID name and value."""
        # Set frame properties
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
                margin: 2px;
            }}
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # PID name label with colored background
        name_label = QLabel(self.pid_name)
        name_label.setFont(QFont("Segoe UI", 8, QFont.Bold))  # Smaller font for longer names
        
        # Determine text color based on background
        text_color = "white" if self._is_dark_color(self.color) else "black"
        name_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.color.name()};
                color: {text_color};
                padding: 2px 4px;
                border-radius: 2px;
                font-weight: bold;
            }}
        """)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)  # Allow word wrap for long names
        layout.addWidget(name_label)
        
        # Value label with clean background
        self.value_label = QLabel(f"{initial_value:.2f}")
        self.value_label.setFont(QFont("Segoe UI", 9, QFont.Bold))  # Slightly smaller font
        self.value_label.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                padding: 2px 4px;
                border-radius: 2px;
                font-weight: bold;
            }
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Set fixed size for consistency - make cards bigger for better text display
        self.setFixedSize(120, 70)
    
    def update_value(self, value: float):
        """Update the displayed value."""
        if self.value_label:
            if np.isnan(value) or np.isinf(value):
                self.value_label.setText("--")
            else:
                self.value_label.setText(f"{value:.2f}")
    
    def _is_dark_color(self, color: QColor) -> bool:
        """Determine if a color is dark for text contrast."""
        # Calculate luminance
        rgb = color.getRgbF()[:3]  # Get RGB as floats 0-1
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
        return luminance < 0.5


class LiveValuesWidget(QWidget):
    """Widget displaying live PID values in color-coded cards for PySide6."""
    
    # Signal emitted when values are updated (for potential debugging)
    values_updated = Signal(float, dict)  # position, values_dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.chart_config: Optional[ChartConfig] = None
        self.interpolator = PIDInterpolator()  # Uses config file setting
        self.cards = {}  # pid_name -> PIDCard
        self.current_x_position = 0.0
        self._debug_logging = get_pid_debug_setting()
        
        # Rate limiting for debug logs
        self._last_log_time = 0
        self._log_interval = get_log_interval()
        self._last_position = None
        self._log_on_stop = get_log_on_stop()
        self._position_threshold = get_position_threshold()
        
        self._build_ui()
        self.hide()  # Initially hidden
    
    def set_debug_logging(self, enabled: bool):
        """Enable or disable debug logging for live values updates."""
        self._debug_logging = enabled
        self.interpolator.set_debug_logging(enabled)
    
    def _should_log(self, x_position: float) -> bool:
        """Check if we should log based on rate limiting and position changes."""
        if not self._debug_logging:
            return False
        
        current_time = time.time()
        
        # Always log if this is the first time or position changed significantly
        if self._last_position is None:
            self._last_position = x_position
            self._last_log_time = current_time
            return True
        
        # Check if position changed (slider is moving)
        position_changed = abs(x_position - self._last_position) > self._position_threshold
        self._last_position = x_position
        
        # Log if:
        # 1. Enough time has passed since last log, OR
        # 2. Position changed and we want to log on stop
        time_elapsed = current_time - self._last_log_time
        
        if time_elapsed >= self._log_interval:
            self._last_log_time = current_time
            return True
        
        # If slider stopped moving (no significant change), log the final value
        if not position_changed and self._log_on_stop and time_elapsed >= 0.1:
            self._last_log_time = current_time
            return True
        
        return False
    
    def _build_ui(self):
        """Build the display widget."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title label
        self.title_label = QLabel("PID Values at Current Position")
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                padding: 2px 0px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(90)  # Limit height - increased for larger cards
        layout.addWidget(self.scroll_area)
        
        # Cards container
        self.cards_widget = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(4)
        self.cards_layout.addStretch()  # Push cards to the left
        
        self.scroll_area.setWidget(self.cards_widget)
    
    def update_chart_config(self, config: Optional[ChartConfig]):
        """Update the chart configuration and rebuild cards."""
        self.chart_config = config
        self._rebuild_cards()
    
    def update_values(self, x_position: float):
        """Update displayed values for the current slider position."""
        if not self.chart_config or self.chart_config.data.empty:
            return
        
        self.current_x_position = x_position
        
        # Get interpolated values
        values = self.interpolator.interpolate_values(self.chart_config, x_position)
        
        should_log = self._should_log(x_position)
        
        if should_log:
            debug(f"=== Live Values Update Debug ===")
            debug(f"Position: {x_position:.3f}")
            debug(f"Interpolated values: {list(values.keys())}")
            debug(f"Available cards: {list(self.cards.keys())}")
        
        # Update cards
        updated_count = 0
        for pid_name, value in values.items():
            if pid_name in self.cards:
                self.cards[pid_name].update_value(value)
                updated_count += 1
                if should_log:
                    debug(f"  ✓ Updated {pid_name}: {value}")
            else:
                if should_log:
                    debug(f"  ✗ No card found for {pid_name}")
                error(f"Live values: No card found for PID {pid_name} but interpolation succeeded")
        
        # Check for cards that didn't get updated
        if should_log:
            for pid_name in self.cards:
                if pid_name not in values:
                    debug(f"  ⚠ No interpolated value for {pid_name}")
                    error(f"Live values: Card exists for PID {pid_name} but no interpolated value available")
            
            debug(f"Updated {updated_count}/{len(self.cards)} cards")
            debug(f"=== Live Values Update Complete ===")
            debug("")  # Empty line for spacing
        
        # Update title with position
        self._update_title(x_position)
        
        # Emit signal for debugging
        self.values_updated.emit(x_position, values)
    
    def _rebuild_cards(self):
        """Rebuild all cards based on current chart configuration."""
        # Clear existing cards
        for card in self.cards.values():
            card.deleteLater()
        self.cards.clear()
        
        if not self.chart_config:
            self.title_label.setText("PID Values at Current Position")
            return
        
        # Get all PIDs from both axes
        all_pids = []
        all_pids.extend(self.chart_config.primary_axis.series)
        all_pids.extend(self.chart_config.secondary_axis.series)
        
        if not all_pids:
            self.title_label.setText("PID Values at Current Position")
            return
        
        # Create cards
        for pid_name in all_pids:
            # Determine color and axis
            is_secondary = pid_name in self.chart_config.secondary_axis.series
            series_index = (self.chart_config.secondary_axis.series.index(pid_name) 
                          if is_secondary 
                          else self.chart_config.primary_axis.series.index(pid_name))
            
            color = ColorManager.get_series_color(
                pid_name, is_secondary, series_index, self.chart_config.series_styles
            )
            
            # Create card
            card = PIDCard(pid_name, color, 0.0, self.cards_widget)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)  # Insert before stretch
            
            # Store reference
            self.cards[pid_name] = card
        
        # Update canvas scroll region
        self.cards_widget.update()
        self.scroll_area.ensureVisible(0, 0)
    
    def _update_title(self, x_position: float):
        """Update title with current position information."""
        if not self.chart_config:
            return
        
        x_col = self.chart_config.get_x_column()
        if x_col in ["Time", "Time (MM:SS)"]:
            minutes = int(x_position // 60)
            seconds = int(x_position % 60)
            position_str = f"{minutes:02d}:{seconds:02d}"
        else:
            position_str = f"{x_position:.2f}"
        
        self.title_label.setText(f"PID Values at {position_str}")
    
    def show_widget(self):
        """Show the display widget."""
        self.show()
    
    def hide_widget(self):
        """Hide the display widget."""
        self.hide()
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get interpolator cache information."""
        return self.interpolator.get_cache_info()
    
    def clear_cache(self):
        """Clear the interpolator cache."""
        self.interpolator.clear_cache()
