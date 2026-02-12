"""
Pop-out Chart Window

A standalone window that displays a chart with its own toolbar.
"""

import copy
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMessageBox, QSlider, QLabel, QLineEdit
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction

from matplotlib.figure import Figure
import mplcursors

from domain.chart_config import ChartConfig
from ui.chart_renderer import ChartRenderer
from ui_pyside6.widgets.custom_toolbar import CustomNavigationToolbar
from ui_pyside6.widgets.live_values_widget import LiveValuesWidget


class ChartPopoutWindow(QMainWindow):
    """A pop-out window displaying a chart with toolbar."""
    
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
        self.toolbar.value_display_changed.connect(self._on_value_display_changed)
        self.toolbar.time_slider_changed.connect(self._on_time_slider_changed)
        main_layout.addWidget(self.toolbar)
        
        # Pack canvas
        main_layout.addWidget(self.canvas, stretch=1)
        
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
        
        # Live values display (initially hidden)
        self.live_values_widget = LiveValuesWidget(self)
        main_layout.addWidget(self.live_values_widget)
    
    def _render_chart(self):
        """Render the chart using ChartRenderer."""
        try:
            renderer = ChartRenderer(self.config)
            self.ax_left, self.ax_right = renderer.render(self.figure, self.canvas)
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
    
