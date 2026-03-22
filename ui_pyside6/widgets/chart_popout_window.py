"""
Pop-out Chart Window

A standalone window that displays a chart with its own toolbar.
"""

import copy
import os
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMessageBox, QSlider, QLabel, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QPixmap

from matplotlib.figure import Figure
import mplcursors

from domain.chart_config import ChartConfig
from ui.color_manager import ColorManager
from ui.chart_renderer import ChartRenderer
from infrastructure import log_debug
from utils import resource_path
from ui_pyside6.widgets.custom_toolbar import CustomNavigationToolbar
from ui_pyside6.widgets.live_values_widget import LiveValuesWidget


class ChartPopoutWindow(QMainWindow):
    """A pop-out window displaying a chart with toolbar."""

    # Signal emitted when Quick IQ is requested from pop-out toolbar
    quick_iq_requested = Signal(str)
    
    def __init__(self, parent, config: ChartConfig, chart_cart=None):
        super().__init__(parent)
        
        # Deep copy config to make this window independent
        self.config = copy.deepcopy(config)
        self.chart_cart = chart_cart
        
        # Window setup
        self.setWindowTitle(self.config.title or "Chart")
        self.setGeometry(100, 100, 1000, 600)
        
        # Interactivity controls
        self.enable_slider = False
        self.enable_cursor = False
        
        # Interactivity state
        self.cursor_line = None
        self.mpl_cursor = None
        
        # Slider data range
        self._slider_min_val = 0.0
        self._slider_max_val = 1.0
        
        # Live values display
        self.live_values_widget = None

        # Horizontal Y-ruler state
        self._y_ruler_values: List[float] = []
        self._y_ruler_lines = []
        self._y_ruler_handles = []
        self._y_ruler_value_labels = []
        self._dragging_ruler = False
        self._active_ruler_index: Optional[int] = None
        
        # Build the UI
        self._setup_ui()
        # Render the chart
        self._render_chart()
    
    def _setup_ui(self):
        """Build the window UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Interactivity controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addStretch()
        
        main_layout.addLayout(controls_layout)
        
        # Create figure and canvas
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()
        
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        self.canvas = FigureCanvas(self.figure)
        
        # Add custom toolbar (no pop-out button in pop-out windows)
        self.toolbar = CustomNavigationToolbar(self.canvas, self, show_popout=False)
        self.toolbar.add_to_cart_requested.connect(self._add_to_cart)
        self.toolbar.quick_iq_requested.connect(self._on_quick_iq_requested)
        self.toolbar.value_display_changed.connect(self._on_value_display_changed)
        self.toolbar.time_slider_changed.connect(self._on_time_slider_changed)
        main_layout.addWidget(self.toolbar)
        
        # Canvas + Y-ruler controls row
        canvas_row = QHBoxLayout()
        canvas_row.setContentsMargins(0, 0, 0, 0)
        canvas_row.setSpacing(4)

        self._y_ruler_controls = QWidget(self)
        ruler_layout = QVBoxLayout(self._y_ruler_controls)
        ruler_layout.setContentsMargins(0, 4, 0, 4)
        ruler_layout.setSpacing(4)

        self._add_ruler_btn = QPushButton("+")
        self._add_ruler_btn.setFixedSize(22, 22)
        self._add_ruler_btn.setToolTip("Add horizontal ruler at the middle of the Y axis")
        self._add_ruler_btn.clicked.connect(self._on_add_y_ruler)

        self._remove_ruler_btn = QPushButton("-")
        self._remove_ruler_btn.setFixedSize(22, 22)
        self._remove_ruler_btn.setToolTip("Remove selected ruler (or last if none selected)")
        self._remove_ruler_btn.clicked.connect(self._on_remove_last_y_ruler)

        self._clear_rulers_btn = QPushButton("x")
        self._clear_rulers_btn.setFixedSize(22, 22)
        self._clear_rulers_btn.setToolTip("Clear all horizontal rulers")
        self._clear_rulers_btn.clicked.connect(self._on_clear_y_rulers)

        self._ruler_icon_label = QLabel()
        self._ruler_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ruler_icon_label.setToolTip("Y-axis ruler controls")
        ruler_icon_path = resource_path('data/images/ruler.png')
        if os.path.exists(ruler_icon_path):
            icon_pixmap = QPixmap(ruler_icon_path).scaled(
                16,
                16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._ruler_icon_label.setPixmap(icon_pixmap)
        else:
            self._ruler_icon_label.setText("Y")

        ruler_btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                background-color: #F6F6F6;
                font-weight: bold;
                color: #444;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #EAEAEA;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #DDDDDD;
            }
            QPushButton:disabled {
                color: #AAA;
                background-color: #F9F9F9;
            }
        """
        self._add_ruler_btn.setStyleSheet(ruler_btn_style)
        self._remove_ruler_btn.setStyleSheet(ruler_btn_style)
        self._clear_rulers_btn.setStyleSheet(ruler_btn_style)

        ruler_layout.addStretch(1)
        ruler_layout.addWidget(self._ruler_icon_label)
        ruler_layout.addSpacing(2)
        ruler_layout.addWidget(self._add_ruler_btn)
        ruler_layout.addWidget(self._remove_ruler_btn)
        ruler_layout.addWidget(self._clear_rulers_btn)
        ruler_layout.addStretch(1)

        canvas_row.addWidget(self._y_ruler_controls)
        canvas_row.addWidget(self.canvas, stretch=1)
        main_layout.addLayout(canvas_row, stretch=1)
        
        # Qt-based time slider widget (hidden by default)
        self._slider_widget = QWidget(self)
        sl = QHBoxLayout(self._slider_widget)
        sl.setContentsMargins(8, 2, 8, 2)
        sl.setSpacing(6)
        self._slider_label_left = QLabel("00:00")
        self._slider_label_left.setStyleSheet("font-size: 11px; color: #555;")
        self._qt_slider = QSlider(Qt.Orientation.Horizontal)
        self._qt_slider.setMinimum(0)
        self._qt_slider.setMaximum(1000)
        self._qt_slider.setValue(0)
        self._qt_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ccc;
                height: 6px;
                background: #e0e0e0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: red;
                border: 2px solid darkred;
                width: 16px;
                margin: -6px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal:hover {
                background: #ff4444;
            }
        """)
        self._slider_label_right = QLabel("00:00")
        self._slider_label_right.setStyleSheet("font-size: 11px; color: #555;")
        self._slider_time_entry = QLineEdit("00:00")
        self._slider_time_entry.setFixedWidth(60)
        self._slider_time_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._slider_time_entry.setStyleSheet("""
            QLineEdit {
                font-size: 11px;
                font-weight: bold;
                color: darkred;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 1px 4px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid darkred;
            }
        """)
        self._slider_time_entry.setToolTip("Current time (MM:SS) \u2014 type a value and press Enter to jump")
        self._slider_time_entry.returnPressed.connect(self._on_time_entry)
        sl.addWidget(self._slider_label_left)
        sl.addWidget(self._qt_slider, stretch=1)
        sl.addWidget(self._slider_label_right)
        sl.addWidget(self._slider_time_entry)
        self._slider_widget.hide()
        main_layout.addWidget(self._slider_widget)
        
        # Connect Qt slider signal
        self._qt_slider.valueChanged.connect(self._on_qt_slider_changed)

        # Track mouse interactions for Y-rulers
        self.canvas.mpl_connect("motion_notify_event", self._on_chart_mouse_move)
        self.canvas.mpl_connect("button_press_event", self._on_chart_mouse_press)
        self.canvas.mpl_connect("button_release_event", self._on_chart_mouse_release)
        
        # Live values display (initially hidden)
        self.live_values_widget = LiveValuesWidget(self)
        main_layout.addWidget(self.live_values_widget)

    def _event_to_primary_y(self, event) -> Optional[float]:
        """Convert a matplotlib mouse event to primary-axis Y data coordinates."""
        if self.ax_left is None:
            return None
        if event.x is None or event.y is None:
            return None

        try:
            return float(self.ax_left.transData.inverted().transform((event.x, event.y))[1])
        except Exception:
            return None

    def _find_ruler_near_y(self, y_val: float) -> Optional[int]:
        """Find the index of the ruler nearest the given y-value."""
        if not self._y_ruler_values or self.ax_left is None:
            return None

        y_min, y_max = self.ax_left.get_ylim()
        tolerance = abs(y_max - y_min) * 0.03
        if tolerance == 0:
            tolerance = 1.0

        closest_idx = None
        closest_dist = None
        for i, ruler_y in enumerate(self._y_ruler_values):
            dist = abs(ruler_y - y_val)
            if closest_dist is None or dist < closest_dist:
                closest_idx = i
                closest_dist = dist

        if closest_dist is not None and closest_dist <= tolerance:
            return closest_idx
        return None

    def _on_chart_mouse_move(self, event):
        """Update dragged ruler position while mouse moves."""
        y_val = self._event_to_primary_y(event)
        if y_val is None:
            return

        if self._dragging_ruler and self._active_ruler_index is not None:
            self._y_ruler_values[self._active_ruler_index] = y_val
            self._redraw_y_rulers()

    def _on_chart_mouse_press(self, event):
        """Start ruler drag when clicking near a ruler."""
        if self.ax_left is None or event.inaxes is None or event.button != 1:
            return

        y_val = self._event_to_primary_y(event)
        if y_val is None:
            return

        nearest_idx = self._find_ruler_near_y(y_val)
        self._active_ruler_index = nearest_idx
        if nearest_idx is not None:
            self._dragging_ruler = True
            self._y_ruler_values[nearest_idx] = y_val
        self._redraw_y_rulers()

    def _on_chart_mouse_release(self, event):
        """End ruler drag operation."""
        self._dragging_ruler = False

    def _on_add_y_ruler(self):
        """Add a horizontal ruler at the midpoint of the primary Y-axis."""
        if self.ax_left is None:
            return

        y_min, y_max = self.ax_left.get_ylim()
        y_mid = float((y_min + y_max) / 2.0)

        self._y_ruler_values.append(y_mid)
        self._active_ruler_index = len(self._y_ruler_values) - 1
        self._redraw_y_rulers()

    def _on_remove_last_y_ruler(self):
        """Remove selected ruler, or the last one if none is selected."""
        if not self._y_ruler_values:
            return

        if self._active_ruler_index is not None and 0 <= self._active_ruler_index < len(self._y_ruler_values):
            self._y_ruler_values.pop(self._active_ruler_index)
            self._active_ruler_index = None
        else:
            self._y_ruler_values.pop()
        self._redraw_y_rulers()

    def _on_clear_y_rulers(self):
        """Remove all horizontal rulers."""
        if not self._y_ruler_values and not self._y_ruler_lines:
            return
        self._y_ruler_values.clear()
        self._active_ruler_index = None
        self._redraw_y_rulers()

    def _redraw_y_rulers(self):
        """Redraw all horizontal rulers on the primary axis."""
        x_limits = None
        y_limits = None
        if self.ax_left is not None:
            x_limits = self.ax_left.get_xlim()
            y_limits = self.ax_left.get_ylim()

        for line in self._y_ruler_lines:
            try:
                line.remove()
            except Exception:
                pass
        self._y_ruler_lines.clear()

        for handle in self._y_ruler_handles:
            try:
                handle.remove()
            except Exception:
                pass
        self._y_ruler_handles.clear()

        for text_obj in self._y_ruler_value_labels:
            try:
                text_obj.remove()
            except Exception:
                pass
        self._y_ruler_value_labels.clear()

        if self.ax_left is not None:
            x_min, x_max = self.ax_left.get_xlim()
            x_span = x_max - x_min
            handle_x = x_min + (0.015 * x_span if x_span != 0 else 0.0)

            for i, y_val in enumerate(self._y_ruler_values):
                is_active = i == self._active_ruler_index
                line = self.ax_left.axhline(
                    y=y_val,
                    color="#ff7a00" if not is_active else "#d94f00",
                    linestyle=":",
                    linewidth=1.4 if is_active else 1.2,
                    alpha=0.8,
                    zorder=3,
                    label=f"Y Ruler {i + 1}",
                )
                self._y_ruler_lines.append(line)

                handle = self.ax_left.plot(
                    [handle_x], [y_val],
                    marker="s",
                    markersize=6 if is_active else 5,
                    markeredgewidth=1.0,
                    markerfacecolor="#ff7a00" if not is_active else "#d94f00",
                    markeredgecolor="white",
                    linestyle="None",
                    zorder=4,
                )[0]
                self._y_ruler_handles.append(handle)

                value_label = self.ax_left.text(
                    handle_x,
                    y_val,
                    f" {y_val:.2f}",
                    va="center",
                    ha="left",
                    fontsize=8,
                    color="#d94f00" if is_active else "#ff7a00",
                    zorder=5,
                    bbox={
                        "boxstyle": "round,pad=0.15",
                        "facecolor": "white",
                        "edgecolor": "#dddddd",
                        "alpha": 0.75,
                    },
                )
                self._y_ruler_value_labels.append(value_label)

            # Keep chart scaling fixed while rulers are added/moved.
            if x_limits is not None and y_limits is not None:
                self.ax_left.set_xlim(x_limits)
                self.ax_left.set_ylim(y_limits)

        self._remove_ruler_btn.setEnabled(bool(self._y_ruler_values))
        self._clear_rulers_btn.setEnabled(bool(self._y_ruler_values))
        self.canvas.draw_idle()
    
    def _render_chart(self):
        """Render the chart using ChartRenderer."""
        try:
            renderer = ChartRenderer(self.config)
            self.ax_left, self.ax_right = renderer.render(self.figure, self.canvas)
            self._redraw_y_rulers()
        except Exception as e:
            # Show error on the chart
            self.ax_left.clear()
            self.ax_left.text(0.5, 0.5, f"Error: {str(e)}", 
                            ha='center', va='center', transform=self.ax_left.transAxes)
            self.canvas.draw()
    
        
    @Slot(bool)
    def _on_value_display_changed(self, enabled: bool):
        """Handle value display toggle change from toolbar."""
        self.enable_cursor = enabled
        
        self._clear_interactivity()
        self._add_interactivity()
        self.canvas.draw()
    
    @Slot(bool)
    def _on_time_slider_changed(self, enabled: bool):
        """Handle time slider toggle change from toolbar."""
        self.enable_slider = enabled
        
        # Show/hide live values display
        if self.live_values_widget:
            if enabled and self.config:
                self.live_values_widget.update_chart_config(self.config)
                self.live_values_widget.show_widget()
            else:
                self.live_values_widget.hide_widget()
        
        self._clear_interactivity()
        self._add_interactivity()
        self.canvas.draw()
    
    def _clear_interactivity(self):
        """Remove existing slider and cursors."""
        # Hide the Qt slider widget
        self._slider_widget.hide()
        
        if self.cursor_line:
            try:
                self.cursor_line.remove()
            except Exception:
                pass
            self.cursor_line = None
        
        if self.mpl_cursor:
            try:
                self.mpl_cursor.remove()
            except Exception:
                pass
            self.mpl_cursor = None
    
    def _add_interactivity(self):
        """Add time slider and hover cursors to the chart."""
        if not self.config or self.config.data.empty:
            return
        
        # --- Add Hover Cursors ---
        if self.enable_cursor:
            artists = []
            if self.ax_left:
                artists.extend(self.ax_left.lines)
                artists.extend(self.ax_left.containers)
                artists.extend(self.ax_left.collections)
            if self.ax_right:
                artists.extend(self.ax_right.lines)
                artists.extend(self.ax_right.containers)
                artists.extend(self.ax_right.collections)
            
            if artists:
                self.mpl_cursor = mplcursors.cursor(artists, hover=True)
                
                @self.mpl_cursor.connect("add")
                def on_add(sel):
                    try:
                        label = sel.artist.get_label()
                        x, y = sel.target
                        
                        x_col = self.config.get_x_column()
                        if x_col in ["Time", "Time (MM:SS)"]:
                            minutes = int(x // 60)
                            seconds = int(x % 60)
                            x_str = f"{minutes:02d}:{seconds:02d}"
                        else:
                            x_str = f"{x:.2f}"
                        
                        sel.annotation.set_text(f"{label}\ntime: {x_str}\nvalue: {y:.2f}")
                        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
                    except Exception:
                        pass
        
        # --- Add Time Slider ---
        if self.enable_slider:
            if self.ax_left:
                xlim = self.ax_left.get_xlim()
                self._slider_min_val = float(xlim[0])
                self._slider_max_val = float(xlim[1])
                
                # Update slider labels
                self._slider_label_left.setText(self._format_slider_time(self._slider_min_val))
                self._slider_label_right.setText(self._format_slider_time(self._slider_max_val))
                
                # Reset slider to start
                self._qt_slider.blockSignals(True)
                self._qt_slider.setValue(0)
                self._qt_slider.blockSignals(False)
                self._slider_time_entry.setText(self._format_slider_time(self._slider_min_val))
                
                # Show the Qt slider widget
                self._slider_widget.show()
                
                # Create vertical cursor line on the matplotlib chart
                self.cursor_line = self.ax_left.axvline(
                    x=self._slider_min_val, color='red', alpha=0.5, linestyle='--'
                )
    
    def _format_slider_time(self, seconds):
        """Format seconds as MM:SS for slider labels."""
        if seconds < 0:
            seconds = 0
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def _on_time_entry(self):
        """Handle manual time entry — parse MM:SS and jump the slider."""
        text = self._slider_time_entry.text().strip()
        try:
            parts = text.split(":")
            if len(parts) == 2:
                mins, secs = int(parts[0]), int(parts[1])
                target_seconds = mins * 60 + secs
            elif len(parts) == 1:
                target_seconds = float(parts[0])
            else:
                return
            
            target_seconds = max(self._slider_min_val, min(self._slider_max_val, target_seconds))
            
            data_range = self._slider_max_val - self._slider_min_val
            if data_range > 0:
                frac = (target_seconds - self._slider_min_val) / data_range
                self._qt_slider.setValue(int(frac * 1000))
            
            self._slider_time_entry.setText(self._format_slider_time(target_seconds))
            self._slider_time_entry.clearFocus()
        except (ValueError, IndexError):
            frac = self._qt_slider.value() / 1000.0
            val = self._slider_min_val + frac * (self._slider_max_val - self._slider_min_val)
            self._slider_time_entry.setText(self._format_slider_time(val))
    
    def _on_qt_slider_changed(self, int_val):
        """Handle Qt slider value changes — update cursor line and live values."""
        frac = int_val / 1000.0
        val = self._slider_min_val + frac * (self._slider_max_val - self._slider_min_val)
        
        # Update time display (only when not focused, to avoid overwriting user typing)
        if not self._slider_time_entry.hasFocus():
            self._slider_time_entry.setText(self._format_slider_time(val))
        
        # Update vertical cursor line on the chart
        if self.cursor_line:
            self.cursor_line.set_xdata([val, val])
            self.canvas.draw_idle()
        
        # Update live values display
        if self.live_values_widget and self.live_values_widget.isVisible():
            self.live_values_widget.update_values(val)
    
    @Slot()
    def _add_to_cart(self):
        """Add a copy of this chart's config to the cart."""
        if not self.chart_cart:
            QMessageBox.information(self, "No cart", "Cart not available.")
            return
        
        # Capture current axis limits
        if hasattr(self, 'ax_left') and self.ax_left:
            ymin_primary, ymax_primary = self.ax_left.get_ylim()
            self.config.primary_axis.min_value = ymin_primary
            self.config.primary_axis.max_value = ymax_primary
            self.config.primary_axis.auto_scale = False
        
        if hasattr(self, 'ax_right') and self.ax_right:
            ymin_secondary, ymax_secondary = self.ax_right.get_ylim()
            self.config.secondary_axis.min_value = ymin_secondary
            self.config.secondary_axis.max_value = ymax_secondary
            self.config.secondary_axis.auto_scale = False
        
        config_copy = copy.deepcopy(self.config)
        self.chart_cart.add_config(config_copy)

    @Slot()
    def _on_quick_iq_requested(self):
        """Forward Quick IQ request to main window with this chart title."""
        title = self.config.title if self.config and self.config.title else ""
        self.quick_iq_requested.emit(title)
    
