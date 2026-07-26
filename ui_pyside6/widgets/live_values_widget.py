"""
Live Values Widget for PySide6

Displays PID values in color-coded cards that update as the time slider moves.
PySide6 implementation with modern styling.
"""

import numpy as np
import re
import math
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QScrollArea, QStyle, QStyleOption, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QFontMetrics, QPixmap
import time
import pandas as pd

from domain.chart_config import ChartConfig
from domain.pid_interpolator import PIDInterpolator
from domain.constants import (
    LIVE_METRIC_KEYS,
    LIVE_METRIC_PID_MAP,
    LIVE_METRIC_META,
    LIVE_METRIC_STATE_LABELS,
    UNIT_DISPLAY_DECIMALS,
)
from rendering.color_manager import ColorManager
from infrastructure import log_debug, log_error
from domain.pid_debug_config import get_pid_debug_setting, get_log_interval, get_log_on_stop, get_position_threshold
from utils import resource_path


class PIDCard(QFrame):
    """A single PID value card with color coding for PySide6."""
    
    def __init__(self, pid_name: str, color: str, initial_value: float = 0.0, decimals: int = 2, parent=None):
        super().__init__(parent)
        
        self.pid_name = pid_name
        self.color = QColor(color)
        self.value_label = None
        self.decimals = decimals
        
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
        self.value_label = QLabel(f"{initial_value:.{self.decimals}f}")
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
        
        # Keep standard PID cards compact.
        self.setFixedSize(120, 70)
    
    def update_value(self, value: float):
        """Update the displayed value."""
        if self.value_label:
            if np.isnan(value) or np.isinf(value):
                self.value_label.setText("--")
            else:
                self.value_label.setText(f"{value:.{self.decimals}f}")
    
    def _is_dark_color(self, color: QColor) -> bool:
        """Determine if a color is dark for text contrast."""
        # Calculate luminance
        rgb = color.getRgbF()[:3]  # Get RGB as floats 0-1
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
        return luminance < 0.5


class MiniGaugeCard(QFrame):
    """Compact arc-style gauge card sized similarly to PID cards."""

    def __init__(
        self,
        label: str,
        unit: str,
        min_value: float,
        max_value: float,
        decimals: int = 0,
        bands: Optional[list[tuple[float, float, str]]] = None,
        tick_values: Optional[list[float]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.metric_label = label
        self.unit = unit
        self.min_value = float(min_value)
        self.max_value = float(max_value)
        self.decimals = int(decimals)
        self.current_value: Optional[float] = None
        self.bands = list(bands or [])
        self.tick_values = list(tick_values or [])

        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet(
            """
            QFrame {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
                margin: 2px;
            }
            """
        )
        self.setFixedSize(117, 108)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)

        self.name_label = QLabel(self.metric_label, self)
        self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.name_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.name_label.setStyleSheet("QLabel { color: #333; }")
        self.name_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.name_label.raise_()

        layout.addStretch(1)

        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.value_label.setStyleSheet("QLabel { color: #111; }")
        layout.addWidget(self.value_label)

        self._position_name_label()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_name_label()

    def _position_name_label(self):
        """Pin metric label to top-left with slight card-edge overlap."""
        if not hasattr(self, "name_label") or self.name_label is None:
            return
        self.name_label.adjustSize()
        self.name_label.move(-3, -3)

    def update_value(self, value: Optional[float]):
        """Update value text and needle position."""
        if value is None or np.isnan(value) or np.isinf(value):
            self.current_value = None
            self.value_label.setText("--")
            self.update()
            return

        self.current_value = float(value)
        if self.unit:
            fmt = f"{{:.{self.decimals}f}}"
            self.value_label.setText(f"{fmt.format(self.current_value)} {self.unit}")
        else:
            fmt = f"{{:.{self.decimals}f}}"
            self.value_label.setText(fmt.format(self.current_value))
        self.update()

    def _to_ratio(self) -> Optional[float]:
        if self.current_value is None:
            return None
        value_span = self.max_value - self.min_value
        if value_span <= 0:
            return 0.0
        ratio = (self.current_value - self.min_value) / value_span
        return max(0.0, min(1.0, ratio))

    def _value_to_angle(self, value: float, start_deg: float, span_deg: float) -> float:
        """Map a value in gauge range to an arc angle."""
        span = self.max_value - self.min_value
        if span <= 0:
            return start_deg
        ratio = (value - self.min_value) / span
        ratio = max(0.0, min(1.0, ratio))
        return start_deg + (span_deg * ratio)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        sweep_bounds = self.rect().adjusted(10, 22, -10, -22)
        sweep_size = min(sweep_bounds.width(), sweep_bounds.height())
        sweep_center = sweep_bounds.center()
        needle_rect = QRect(
            int(sweep_center.x() - (sweep_size / 2)),
            int(sweep_center.y() - (sweep_size / 2)),
            int(sweep_size),
            int(sweep_size),
        )
        band_inset = 14
        band_rect = needle_rect.adjusted(band_inset, band_inset, -band_inset, -band_inset)
        start_deg = 210
        span_deg = -240

        band_pen = QPen(QColor("#C8C8C8"), 2)
        painter.setPen(band_pen)
        painter.drawArc(band_rect, start_deg * 16, span_deg * 16)

        # Draw configured threshold color bands, or fallback defaults.
        band_width = 4
        if self.bands:
            for band_start, band_end, band_color in self.bands:
                start_angle = self._value_to_angle(float(band_start), start_deg, span_deg)
                end_angle = self._value_to_angle(float(band_end), start_deg, span_deg)
                band_span = end_angle - start_angle
                painter.setPen(QPen(QColor(band_color), band_width))
                painter.drawArc(band_rect, int(start_angle * 16), int(band_span * 16))
        else:
            painter.setPen(QPen(QColor("#4CAF50"), band_width))
            painter.drawArc(band_rect, 210 * 16, -144 * 16)
            painter.setPen(QPen(QColor("#FFC107"), band_width))
            painter.drawArc(band_rect, 66 * 16, -60 * 16)
            painter.setPen(QPen(QColor("#E53935"), band_width))
            painter.drawArc(band_rect, 6 * 16, -36 * 16)

        # Optional tick labels for key thresholds.
        if self.tick_values:
            tick_font = QFont("Segoe UI", 7)
            painter.setFont(tick_font)
            painter.setPen(QPen(QColor("#555555"), 1))
            cx = band_rect.center().x()
            cy = band_rect.center().y()
            base_radius = max(8, min(band_rect.width(), band_rect.height()) // 2 - 2)
            # Keep numeric scale outside the colored arc band.
            label_radius = base_radius + band_width + 8
            for tick in self.tick_values:
                angle_deg = self._value_to_angle(float(tick), start_deg, span_deg)
                angle_rad = math.radians(angle_deg)
                tx = cx + label_radius * math.cos(angle_rad)
                ty = cy - label_radius * math.sin(angle_rad)

                text = str(int(round(tick)))
                text_w = 28
                text_h = 10
                cos_v = math.cos(angle_rad)

                if cos_v > 0.25:
                    # Right side: anchor left edge at the radial point.
                    text_rect_x = int(tx + 1)
                    text_align = Qt.AlignLeft | Qt.AlignVCenter
                elif cos_v < -0.25:
                    # Left side: anchor right edge at the radial point.
                    text_rect_x = int(tx - text_w - 1)
                    text_align = Qt.AlignRight | Qt.AlignVCenter
                else:
                    # Top/near-vertical: keep centered.
                    text_rect_x = int(tx - text_w / 2)
                    text_align = Qt.AlignHCenter | Qt.AlignVCenter

                painter.drawText(text_rect_x, int(ty - text_h / 2), text_w, text_h, text_align, text)

        ratio = self._to_ratio()
        if ratio is None:
            return

        angle_deg = start_deg + (span_deg * ratio)
        angle_rad = math.radians(angle_deg)

        cx = needle_rect.center().x()
        cy = needle_rect.center().y()
        radius = max(8, min(needle_rect.width(), needle_rect.height()) // 2 - 2)

        nx = cx + radius * math.cos(angle_rad)
        ny = cy - radius * math.sin(angle_rad)

        painter.setPen(QPen(QColor("#333333"), 2))
        painter.drawLine(int(cx), int(cy), int(nx), int(ny))
        painter.setBrush(QColor("#333333"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - 2), int(cy - 2), 4, 4)


class LiveValuesWidget(QWidget):
    """Widget displaying live PID values in color-coded cards for PySide6."""
    
    # Signal emitted when values are updated (for potential debugging)
    values_updated = Signal(float, dict)  # position, values_dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.chart_config: Optional[ChartConfig] = None
        self.interpolator = PIDInterpolator()  # Uses config file setting
        self.cards = {}  # pid_name -> PIDCard
        self.live_metric_gauges: Dict[str, MiniGaugeCard] = {}
        self.live_state_chip_groups: Dict[str, Dict[int, QLabel]] = {}
        self.cam_crank_chips: Dict[str, QFrame] = {}
        self._resolved_live_metric_pids: Dict[str, str] = {}
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

    def update_settings(self, settings: dict):
        """Update debug/logging settings from the settings dialog."""
        self.set_debug_logging(settings.get('enable', self._debug_logging))
        self._log_interval = settings.get('interval', self._log_interval)
        self._log_on_stop = settings.get('log_on_stop', self._log_on_stop)
        self._position_threshold = settings.get('threshold', self._position_threshold)
    
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

        # Compact key live metrics row (strictly opt-in by snapshot type)
        self.key_live_widget = QWidget(self)
        self.key_live_layout = QHBoxLayout(self.key_live_widget)
        self.key_live_layout.setContentsMargins(0, 0, 0, 0)
        self.key_live_layout.setSpacing(2)
        self.key_live_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.key_live_widget.hide()
        layout.addWidget(self.key_live_widget)
        
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
        self.interpolator.clear_cache()
        if self._debug_logging:
            snap_type = config.snapshot_type if config else None
            data_cols = list(config.data.columns) if config and config.data is not None else []
            log_debug("=== Live Values Config Update ===")
            log_debug(f"Snapshot type: {snap_type}")
            log_debug(f"Chart data columns ({len(data_cols)}): {data_cols}")
        self._rebuild_compact_live_metrics()
        self._rebuild_cards()
    
    def update_values(self, x_position: float):
        """Update displayed values for the current slider position."""
        if not self.chart_config or self.chart_config.data.empty:
            return
        
        self.current_x_position = x_position
        should_log = self._should_log(x_position)

        # Get interpolated values
        extra_metric_pids = list(dict.fromkeys(self._resolved_live_metric_pids.values()))
        extra_metric_pid_set = set(extra_metric_pids)
        interp_started = time.perf_counter()
        values = self.interpolator.interpolate_values(
            self.chart_config,
            x_position,
            extra_pids=extra_metric_pids,
        )
        interp_elapsed_ms = (time.perf_counter() - interp_started) * 1000.0

        # Update compact live metrics first
        self._update_compact_live_metrics(values, x_position, should_log)
        
        if should_log:
            log_debug(f"=== Live Values Update Debug ===")
            log_debug(f"Position: {x_position:.3f}")
            log_debug(f"Interpolation elapsed: {interp_elapsed_ms:.3f} ms")
            log_debug(f"Interpolated values: {list(values.keys())}")
            log_debug(f"Available cards: {list(self.cards.keys())}")
        
        # Update cards
        updated_count = 0
        for pid_name, value in values.items():
            if pid_name in self.cards:
                self.cards[pid_name].update_value(value)
                updated_count += 1
                if should_log:
                    log_debug(f"  ✓ Updated {pid_name}: {value}")
            else:
                if pid_name in extra_metric_pid_set:
                    # Compact gauges/chips consume these values directly; no standalone card is expected.
                    if should_log:
                        log_debug(f"  • Compact-only PID (no card expected): {pid_name}")
                    continue
                if should_log:
                    log_debug(f"  ✗ No card found for {pid_name}")
                log_error(f"Live values: No card found for PID {pid_name} but interpolation succeeded")
        
        # Check for cards that didn't get updated
        if should_log:
            for pid_name in self.cards:
                if pid_name not in values:
                    log_debug(f"  ⚠ No interpolated value for {pid_name}")
                    log_error(f"Live values: Card exists for PID {pid_name} but no interpolated value available")
            
            log_debug(f"Updated {updated_count}/{len(self.cards)} cards")
            log_debug(f"=== Live Values Update Complete ===")
            log_debug("")  # Empty line for spacing
        
        # Update title with position
        self._update_title(x_position)
        
        # Emit signal for debugging
        self.values_updated.emit(x_position, values)

    def _clear_layout_widgets(self, layout: QHBoxLayout):
        """Remove all widgets/items from a horizontal layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _resolve_live_metric_pids(self) -> Dict[str, str]:
        """Resolve canonical live metrics to available PID columns for current config."""
        if not self.chart_config or self.chart_config.data is None or self.chart_config.data.empty:
            if self._debug_logging:
                log_debug("Live metrics: no chart data available; compact row hidden")
            return {}

        snap_type = self.chart_config.snapshot_type
        if snap_type is None:
            if self._debug_logging:
                log_debug("Live metrics: snapshot_type is None; compact row hidden")
            return {}

        metric_aliases = LIVE_METRIC_PID_MAP.get(snap_type)
        if not metric_aliases:
            # Strict opt-in: undefined snaptypes should not show gauges/chips.
            if self._debug_logging:
                log_debug(f"Live metrics: no LIVE_METRIC_PID_MAP entry for {snap_type}; compact row hidden")
            return {}

        available_cols = set(self.chart_config.data.columns)
        available_cols_cf = {str(col).casefold(): str(col) for col in self.chart_config.data.columns}
        resolved: Dict[str, str] = {}
        if self._debug_logging:
            log_debug(f"Live metrics: resolving aliases for {snap_type}")
            log_debug(f"Live metrics: available columns = {sorted(available_cols)}")
        for key in LIVE_METRIC_KEYS:
            aliases = metric_aliases.get(key, [])
            if self._debug_logging:
                log_debug(f"  {key}: aliases={aliases}")
            for alias in aliases:
                actual_col = alias if alias in available_cols else available_cols_cf.get(alias.casefold())
                if actual_col:
                    resolved[key] = actual_col
                    if self._debug_logging:
                        if actual_col == alias:
                            log_debug(f"    -> resolved to {actual_col}")
                        else:
                            log_debug(f"    -> resolved alias {alias} to actual column {actual_col}")
                    break
            if self._debug_logging and key not in resolved:
                log_error(f"    -> no matching column for {key}")

        if self._debug_logging:
            log_debug(f"Live metrics: resolved map = {resolved}")
        return resolved

    def _parse_state_labels_from_unit(self, pid_name: str) -> Dict[int, str]:
        """Parse [0]Off [1]Running style labels from pid_info Unit text."""
        if not self.chart_config or not self.chart_config.pid_info:
            return {}
        info = self.chart_config.pid_info.get(pid_name)
        if info is None:
            pid_cf = pid_name.casefold()
            for key, value in self.chart_config.pid_info.items():
                if str(key).casefold() == pid_cf:
                    info = value
                    break
        info = info or {}
        unit_text = str(info.get("Unit", ""))
        matches = re.findall(r"\[(\d+)\]\s*([^\[]+)", unit_text)
        parsed: Dict[int, str] = {}
        for code_str, label in matches:
            parsed[int(code_str)] = label.strip()
        return parsed

    def _set_chip_active(self, label: QLabel, active: bool):
        if active:
            label.setStyleSheet(
                """
                QLabel {
                    background-color: #00AA00;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 9px;
                    border: 1px solid #00DD00;
                    border-radius: 4px;
                    padding: 0px 4px;
                }
                """
            )
        else:
            label.setStyleSheet(
                """
                QLabel {
                    background-color: #D0D0D0;
                    color: #888888;
                    font-weight: normal;
                    font-size: 9px;
                    border: 1px solid #B0B0B0;
                    border-radius: 4px;
                    padding: 0px 4px;
                }
                """
            )

    def _set_sync_chip_state(self, label: QLabel, state_code: int, is_active: bool):
        """Apply state-specific styling for Crank/Cam Sync chips."""
        if not is_active:
            label.setStyleSheet(
                """
                QLabel {
                    background-color: #E0E0E0;
                    color: #616161;
                    font-weight: bold;
                    font-size: 9px;
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                    padding: 0px 4px;
                }
                """
            )
            return

        # 0 = NO_SYNC -> red, 30 = FULL_SYNC -> green, others -> yellow
        sync_styles = {
            0:  ("#E53935", "#FFFFFF", "#C62828"),   # NO_SYNC  - red
            10: ("#F9A825", "#5D4A00", "#F57F17"),   # ALE_SYNC - yellow
            20: ("#F9A825", "#5D4A00", "#F57F17"),   # CAS_SYNC - yellow
            21: ("#F9A825", "#5D4A00", "#F57F17"),   # DIRSTALE - yellow
            30: ("#2E7D32", "#FFFFFF", "#1B5E20"),   # FULL_SYNC - green
        }
        bg, fg, border = sync_styles.get(state_code, ("#F9A825", "#5D4A00", "#F57F17"))
        label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-weight: bold;
                font-size: 9px;
                border: 1px solid {border};
                border-radius: 4px;
                padding: 0px 4px;
            }}
            """
        )

    def _set_engine_state_chip_state(self, label: QLabel, metric_key: str, state_code: int, is_active: bool):
        """Apply state-specific styling for Engine State/Status chips."""
        if not is_active:
            label.setStyleSheet(
                """
                QLabel {
                    background-color: #E0E0E0;
                    color: #616161;
                    font-weight: bold;
                    font-size: 9px;
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                    padding: 0px 4px;
                }
                """
            )
            return

        # Separate styling for V1 ENGINE_STATE vs V2 ENGINE_STATUS
        if metric_key == "ENGINE_STATE":  # V1: 0=Stopped, 1=Cranking, 2=Running, 3=Stalling
            state_styles = {
                0: ("#F5F5F5", "#000000", "#9E9E9E"),  # Stopped
                1: ("#FFF59D", "#5D4A00", "#FDD835"),  # Cranking
                2: ("#2E7D32", "#FFFFFF", "#1B5E20"),  # Running
                3: ("#E53935", "#FFFFFF", "#C62828"),  # Stalling
            }
        else:  # ENGINE_STATUS (V2): 0=STANDBY, 1=READY, 2=CRANKING, 3=RUNNING, 4=STOPPING, 5=FINISH
            state_styles = {
                0: ("#F5F5F5", "#000000", "#9E9E9E"),  # STANDBY
                1: ("#F5F5F5", "#000000", "#9E9E9E"),  # READY
                2: ("#FFF59D", "#5D4A00", "#FDD835"),  # CRANKING
                3: ("#2E7D32", "#FFFFFF", "#1B5E20"),  # RUNNING
                4: ("#E53935", "#FFFFFF", "#C62828"),  # STOPPING
                5: ("#F5F5F5", "#000000", "#9E9E9E"),  # FINISH
            }
        bg, fg, border = state_styles.get(state_code, ("#E0E0E0", "#111111", "#BDBDBD"))
        label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-weight: bold;
                font-size: 9px;
                border: 1px solid {border};
                border-radius: 4px;
                padding: 0px 4px;
            }}
            """
        )

    def _set_binary_chip_state(
        self,
        label: QLabel,
        is_on: bool,
        on_bg: str,
        on_text: str,
        on_border: str,
    ):
        """Apply styling for a single binary indicator chip."""
        if is_on:
            label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {on_bg};
                    color: {on_text};
                    font-weight: bold;
                    font-size: 9px;
                    border: 1px solid {on_border};
                    border-radius: 4px;
                    padding: 0px 4px;
                }}
                """
            )
        else:
            label.setStyleSheet(
                """
                QLabel {
                    background-color: #E0E0E0;
                    color: #616161;
                    font-weight: bold;
                    font-size: 9px;
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                    padding: 0px 4px;
                }
                """
            )

    def _rebuild_compact_live_metrics(self):
        """Build compact gauge/chip row based on strict snaptype mappings."""
        self._clear_layout_widgets(self.key_live_layout)
        self.live_metric_gauges.clear()
        self.live_state_chip_groups.clear()
        self.cam_crank_chips.clear()
        self._resolved_live_metric_pids = self._resolve_live_metric_pids()

        if not self._resolved_live_metric_pids:
            if self._debug_logging:
                log_debug("Live metrics: nothing resolved; compact row hidden")
            self.key_live_widget.hide()
            return

        # Prioritize gauges first for constrained widths; keep RPM first on the left.
        for metric_key in ("ENGINE_SPEED", "OIL_TEMP", "OIL_PRESSURE", "COOLANT_TEMP"):
            pid_name = self._resolved_live_metric_pids.get(metric_key)
            if not pid_name:
                continue
            meta = LIVE_METRIC_META.get(metric_key, {})
            min_value = float(meta.get("min", 0.0))
            max_value = float(meta.get("max", 100.0))
            gauge_unit = str(meta.get("unit", ""))
            gauge_bands: list[tuple[float, float, str]] = []
            gauge_ticks: list[float] = []

            if metric_key == "ENGINE_SPEED":
                # Requested RPM scale and threshold colors.
                min_value = 0.0
                max_value = 2900.0
                gauge_unit = "RPM"
            elif metric_key == "OIL_PRESSURE":
                # Requested PSI scale and threshold colors.
                min_value = 0.0
                max_value = 120.0
                gauge_unit = "PSI"
            elif metric_key == "COOLANT_TEMP":
                # Requested Fahrenheit scale and threshold colors.
                min_value = 0.0
                max_value = 250.0
                gauge_unit = "°F"
                gauge_bands = [
                    (0.0, 185.0, "#1E88E5"),
                    (186.0, 205.0, "#2E7D32"),
                    (206.0, 220.0, "#F9A825"),
                    (220.0, 250.0, "#E53935"),
                ]
                gauge_ticks = [0.0, 185.0, 205.0, 220.0, 250.0]
            elif metric_key == "OIL_TEMP":
                # Requested Fahrenheit scale and threshold colors.
                min_value = 0.0
                max_value = 280.0
                gauge_unit = "°F"

            if (
                metric_key != "COOLANT_TEMP"
                and self.chart_config
                and self.chart_config.data is not None
                and pid_name in self.chart_config.data.columns
            ):
                series = pd.to_numeric(self.chart_config.data[pid_name], errors="coerce")
                if not series.empty:
                    data_min = float(series.min(skipna=True)) if series.notna().any() else None
                    data_max = float(series.max(skipna=True)) if series.notna().any() else None
                    if data_min is not None and data_max is not None:
                        if data_min < min_value or data_max > max_value:
                            min_value = min(min_value, data_min)
                            max_value = max(max_value, data_max)
                            if abs(max_value - min_value) < 1e-9:
                                max_value = min_value + 1.0
                            if self._debug_logging:
                                log_debug(
                                    f"Live metrics: expanded range for {metric_key} ({pid_name}) "
                                    f"to [{min_value:.3f}, {max_value:.3f}] from data"
                                )

            if metric_key == "OIL_TEMP":
                oil_band_max = max(max_value, 240.0)
                gauge_bands = [
                    (0.0, 130.0, "#1E88E5"),
                    (131.0, 230.0, "#2E7D32"),
                    (231.0, 240.0, "#F9A825"),
                    (241.0, oil_band_max, "#E53935"),
                ]
                gauge_ticks = [0.0, 130.0, 230.0, 240.0, oil_band_max]
            elif metric_key == "ENGINE_SPEED":
                rpm_band_max = max(max_value, 2900.0)
                gauge_bands = [
                    (0.0, 1000.0, "#F9A825"),
                    (1001.0, 2500.0, "#2E7D32"),
                    (2501.0, rpm_band_max, "#E53935"),
                ]
                gauge_ticks = [0.0, 1000.0, 2500.0, rpm_band_max]
            elif metric_key == "OIL_PRESSURE":
                pressure_band_max = max(max_value, 120.0)
                gauge_bands = [
                    (0.0, 25.0, "#E53935"),
                    (26.0, 94.0, "#2E7D32"),
                    (95.0, pressure_band_max, "#F9A825"),
                ]
                gauge_ticks = [0.0, 25.0, 95.0, pressure_band_max]

            gauge = MiniGaugeCard(
                label=str(meta.get("label", metric_key)),
                unit=gauge_unit,
                min_value=min_value,
                max_value=max_value,
                decimals=int(meta.get("decimals", 0)),
                bands=gauge_bands,
                tick_values=gauge_ticks,
                parent=self.key_live_widget,
            )
            self.live_metric_gauges[metric_key] = gauge
            self.key_live_layout.addWidget(gauge)
            if self._debug_logging:
                log_debug(f"Live metrics: created gauge {metric_key} from PID {pid_name}")

        snap_type = self.chart_config.snapshot_type if self.chart_config else None
        state_map = LIVE_METRIC_STATE_LABELS.get(snap_type, {}) if snap_type else {}
        chip_font = QFont("Segoe UI", 9, QFont.Bold)
        chip_width = max(
            QFontMetrics(chip_font).horizontalAdvance("Check Engine"),
            QFontMetrics(chip_font).horizontalAdvance("COENG_CRANKING"),
        ) + 8
        sync_chip_width = QFontMetrics(chip_font).horizontalAdvance("EPM_DIRSTALE_SYNC") + 12

        for metric_key in ("ENGINE_STATE", "ENGINE_STATUS"):
            pid_name = self._resolved_live_metric_pids.get(metric_key)
            if not pid_name:
                continue

            labels_by_value = dict(state_map.get(metric_key, {}))
            if not labels_by_value and metric_key in ("ENGINE_STATE", "ENGINE_STATUS"):
                labels_by_value = self._parse_state_labels_from_unit(pid_name)

            if not labels_by_value:
                if self._debug_logging:
                    log_debug(f"Live metrics: skipping chips for {metric_key}; no state labels")
                continue

            state_stack_widget = QWidget(self.key_live_widget)
            state_stack_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            state_stack_layout = QVBoxLayout(state_stack_widget)
            state_stack_layout.setContentsMargins(0, 0, 0, 0)
            state_stack_layout.setSpacing(2)
            state_stack_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            metric_chip_map: Dict[int, QLabel] = {}
            for state_val in sorted(labels_by_value.keys()):
                chip = QLabel(labels_by_value[state_val], state_stack_widget)
                chip.setAlignment(Qt.AlignCenter)
                chip.setFixedHeight(20)
                chip.setFixedWidth(chip_width)
                if metric_key in ("ENGINE_STATE", "ENGINE_STATUS"):
                    self._set_engine_state_chip_state(chip, metric_key, state_val, False)
                else:
                    self._set_chip_active(chip, False)
                metric_chip_map[state_val] = chip
                state_stack_layout.addWidget(chip, 0, Qt.AlignLeft)

            self.live_state_chip_groups[metric_key] = metric_chip_map
            self.key_live_layout.addWidget(state_stack_widget, 0, Qt.AlignLeft | Qt.AlignTop)
            if self._debug_logging:
                log_debug(
                    f"Live metrics: created chips for {metric_key} from PID {pid_name} "
                    f"states={sorted(metric_chip_map.keys())}"
                )

        # Sync status chips (stacked vertically next to engine status)
        sync_pid_name = self._resolved_live_metric_pids.get("SYNC_STATUS")
        if sync_pid_name:
            sync_labels = dict(state_map.get("SYNC_STATUS", {}))
            if sync_labels:
                sync_stack_widget = QWidget(self.key_live_widget)
                sync_stack_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
                sync_stack_layout = QVBoxLayout(sync_stack_widget)
                sync_stack_layout.setContentsMargins(0, 0, 0, 0)
                sync_stack_layout.setSpacing(2)
                sync_stack_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                sync_chip_map: Dict[int, QLabel] = {}
                for state_val in sorted(sync_labels.keys()):
                    chip = QLabel(sync_labels[state_val], sync_stack_widget)
                    chip.setAlignment(Qt.AlignCenter)
                    chip.setFixedHeight(20)
                    chip.setFixedWidth(sync_chip_width)
                    self._set_sync_chip_state(chip, state_val, False)
                    sync_chip_map[state_val] = chip
                    sync_stack_layout.addWidget(chip, 0, Qt.AlignLeft)

                self.live_state_chip_groups["SYNC_STATUS"] = sync_chip_map
                self.key_live_layout.addWidget(sync_stack_widget, 0, Qt.AlignLeft | Qt.AlignTop)
                if self._debug_logging:
                    log_debug(
                        f"Live metrics: created sync chips from PID {sync_pid_name} "
                        f"states={sorted(sync_chip_map.keys())}"
                    )

        binary_stack_widget = QWidget(self.key_live_widget)
        binary_stack_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        binary_stack_layout = QVBoxLayout(binary_stack_widget)
        binary_stack_layout.setContentsMargins(0, 0, 0, 0)
        binary_stack_layout.setSpacing(2)
        binary_stack_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        binary_stack_added = False

        for metric_key in ("START_AID", "SMOKE_LIMIT", "OIL_PRESSURE_LAMP", "CHECK_ENGINE"):
            pid_name = self._resolved_live_metric_pids.get(metric_key)
            if not pid_name:
                continue

            chip = QLabel(
                str(LIVE_METRIC_META.get(metric_key, {}).get("label", metric_key.replace("_", " ").title())),
                binary_stack_widget,
            )
            chip.setAlignment(Qt.AlignCenter)
            chip.setFixedHeight(20)
            chip.setFixedWidth(chip_width)
            is_red_binary = metric_key in ("CHECK_ENGINE", "SMOKE_LIMIT", "OIL_PRESSURE_LAMP")
            self._set_binary_chip_state(
                chip,
                is_on=False,
                on_bg="#E53935" if is_red_binary else "#2E7D32",
                on_text="#FFFFFF",
                on_border="#C62828" if is_red_binary else "#1B5E20",
            )
            binary_stack_layout.addWidget(chip, 0, Qt.AlignLeft)
            self.live_state_chip_groups[metric_key] = {-1: chip}
            binary_stack_added = True
            if self._debug_logging:
                log_debug(f"Live metrics: created single chip for {metric_key} from PID {pid_name}")

        if binary_stack_added:
            self.key_live_layout.addWidget(binary_stack_widget, 0, Qt.AlignLeft | Qt.AlignTop)

        # Cam / Sync / Crank image chips (horizontal, to the right of all other indicators)
        _CAM_CRANK_CHIP_DEFS = [
            ("CAM_VALID", "camshaft.png"),
            ("SYNC_TASKS", "cam-crank-sync.png"),
            ("CRANK_VALID", "crankshaft.png"),
        ]
        any_cam_crank = False
        for metric_key, image_file in _CAM_CRANK_CHIP_DEFS:
            pid_name = self._resolved_live_metric_pids.get(metric_key)
            if not pid_name:
                continue
            # Cam and Crank get gauge-sized cards; Sync stays small
            is_large = metric_key in ("CAM_VALID", "CRANK_VALID")
            chip_size = (117, 108) if is_large else (52, 52)
            icon_size = 80 if is_large else 32
            chip_frame = QFrame(self.key_live_widget)
            chip_frame.setFixedSize(*chip_size)
            chip_frame.setStyleSheet(
                "QFrame { background-color: #FFCDD2; border: 1px solid #EF9A9A; border-radius: 6px; }"
            )
            chip_inner = QVBoxLayout(chip_frame)
            chip_inner.setContentsMargins(4, 4, 4, 4)
            chip_inner.setSpacing(0)
            icon_label = QLabel(chip_frame)
            icon_label.setAlignment(Qt.AlignCenter)
            pix = QPixmap(resource_path(f"data/app_images/{image_file}"))
            if not pix.isNull():
                pix = pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pix)
            icon_label.setStyleSheet("QLabel { background: transparent; border: none; }")
            chip_inner.addWidget(icon_label)
            self.cam_crank_chips[metric_key] = chip_frame
            self.key_live_layout.addWidget(chip_frame, 0, Qt.AlignLeft | Qt.AlignVCenter)
            any_cam_crank = True
            if self._debug_logging:
                log_debug(f"Live metrics: created image chip for {metric_key} from PID {pid_name}")

        # Keep all compact metric widgets packed to the left with spare room on the right.
        self.key_live_layout.addStretch(1)

        should_show = bool(self.live_metric_gauges or self.live_state_chip_groups or self.cam_crank_chips)
        self.key_live_widget.setVisible(should_show)
        if self._debug_logging:
            log_debug(
                "Live metrics: rebuild complete "
                f"visible={should_show}, gauges={list(self.live_metric_gauges.keys())}, "
                f"chips={list(self.live_state_chip_groups.keys())}"
            )

    def _interpolate_metric_value(self, pid_name: str, x_position: float) -> Optional[float]:
        """Interpolate a single PID value via the shared PIDInterpolator.

        Used as a fallback when a resolved metric PID wasn't already covered
        by the batched interpolate_values() call in _update_live_values.
        """
        if not self.chart_config or self.chart_config.data is None or self.chart_config.data.empty:
            return None

        values = self.interpolator.interpolate_values(self.chart_config, x_position, extra_pids=[pid_name])
        return values.get(pid_name)

    def _update_compact_live_metrics(self, interpolated_values: Dict[str, float], x_position: float, should_log: bool = False):
        """Update compact gauges/chips from interpolated values."""
        if not self.key_live_widget.isVisible() or not self._resolved_live_metric_pids:
            if should_log:
                log_debug(
                    "Live metrics: update skipped "
                    f"visible={self.key_live_widget.isVisible()} resolved={bool(self._resolved_live_metric_pids)}"
                )
            return

        for metric_key, gauge in self.live_metric_gauges.items():
            pid_name = self._resolved_live_metric_pids.get(metric_key)
            if not pid_name:
                gauge.update_value(None)
                continue
            value = interpolated_values.get(pid_name)
            if value is None:
                value = self._interpolate_metric_value(pid_name, x_position)

            gauge.update_value(value)
            if should_log:
                log_debug(f"Live metrics: gauge {metric_key} pid={pid_name} value={value}")

        for metric_key, chip_map in self.live_state_chip_groups.items():
            pid_name = self._resolved_live_metric_pids.get(metric_key)
            state_val = None
            raw = None
            if pid_name:
                raw = interpolated_values.get(pid_name)
                if raw is None:
                    raw = self._interpolate_metric_value(pid_name, x_position)
                if raw is not None and not np.isnan(raw) and not np.isinf(raw):
                    state_val = int(round(raw))

            if metric_key in ("CHECK_ENGINE", "START_AID", "SMOKE_LIMIT", "OIL_PRESSURE_LAMP"):
                binary_chip = chip_map.get(-1)
                if binary_chip is not None:
                    is_on = bool(state_val) if state_val is not None else False
                    is_red_binary = metric_key in ("CHECK_ENGINE", "SMOKE_LIMIT", "OIL_PRESSURE_LAMP")
                    self._set_binary_chip_state(
                        binary_chip,
                        is_on=is_on,
                        on_bg="#E53935" if is_red_binary else "#2E7D32",
                        on_text="#FFFFFF",
                        on_border="#C62828" if is_red_binary else "#1B5E20",
                    )
                if should_log:
                    log_debug(f"Live metrics: binary chip {metric_key} pid={pid_name} raw={raw} rounded={state_val}")
                continue

            for val, chip in chip_map.items():
                if metric_key in ("ENGINE_STATE", "ENGINE_STATUS"):
                    self._set_engine_state_chip_state(chip, metric_key, val, state_val == val)
                elif metric_key == "SYNC_STATUS":
                    self._set_sync_chip_state(chip, val, state_val == val)
                else:
                    self._set_chip_active(chip, state_val == val)
            if should_log:
                log_debug(f"Live metrics: chips {metric_key} pid={pid_name} active_state={state_val}")

        # Update cam / sync / crank image chips
        for metric_key, chip_frame in self.cam_crank_chips.items():
            pid_name = self._resolved_live_metric_pids.get(metric_key)
            raw = None
            if pid_name:
                raw = interpolated_values.get(pid_name)
                if raw is None:
                    raw = self._interpolate_metric_value(pid_name, x_position)
            is_true = False
            if raw is not None and not np.isnan(raw) and not np.isinf(raw):
                is_true = bool(int(round(raw)))
            if is_true:
                chip_frame.setStyleSheet(
                    "QFrame { background-color: #C8E6C9; border: 1px solid #81C784; border-radius: 6px; }"
                )
            else:
                chip_frame.setStyleSheet(
                    "QFrame { background-color: #FFCDD2; border: 1px solid #EF9A9A; border-radius: 6px; }"
                )
            if should_log:
                log_debug(f"Live metrics: image chip {metric_key} pid={pid_name} raw={raw} is_true={is_true}")

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
            
            # Determine display decimals from PID unit
            decimals = 2
            if self.chart_config.pid_info:
                pid_meta = self.chart_config.pid_info.get(pid_name, {})
                unit = pid_meta.get("Unit", "")
                decimals = UNIT_DISPLAY_DECIMALS.get(unit, 2)
            
            # Create card
            card = PIDCard(pid_name, color, 0.0, decimals=decimals, parent=self.cards_widget)
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
