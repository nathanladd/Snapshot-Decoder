"""
Pop-out Chart Window

A standalone window that displays a chart with its own toolbar.
"""

import copy
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction

from matplotlib.figure import Figure
from matplotlib.widgets import Slider
import mplcursors

from domain.chart_config import ChartConfig
from ui.chart_renderer import ChartRenderer
from ui_pyside6.widgets.custom_toolbar import CustomNavigationToolbar
from ui_pyside6.widgets.live_values_widget import LiveValuesWidget
from ui_pyside6.widgets.debug_settings_dialog import DebugSettingsDialog


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
        self.slider = None
        self.cursor_line = None
        self.mpl_cursor = None
        
        # Live values display
        self.live_values_widget = None
        
        # Build the UI
        self._setup_ui()
        self._setup_menu()
        
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
        
        # Live values display (initially hidden)
        self.live_values_widget = LiveValuesWidget(self)
        main_layout.addWidget(self.live_values_widget)
    
    def _setup_menu(self):
        """Set up the window menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        close_action = QAction("&Close", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Debug menu
        debug_menu = menubar.addMenu("&Debug")
        
        debug_settings_action = QAction("&Debug Settings...", self)
        debug_settings_action.triggered.connect(self._on_show_debug_settings)
        debug_menu.addAction(debug_settings_action)
    
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
        if self.slider:
            try:
                self.slider.ax.remove()
                self.figure.subplots_adjust(bottom=0.1)
            except Exception:
                pass
            self.slider = None
        
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
            # Get the current x-axis limits from the chart
            if self.ax_left:
                xlim = self.ax_left.get_xlim()
                min_val = float(xlim[0])
                max_val = float(xlim[1])
                
                # Make room for slider
                try:
                    self.figure.subplots_adjust(bottom=0.2)
                except Exception:
                    pass
                
                # Create slider with the same range as the chart x-axis
                self.slider = Slider(
                    self.figure.add_axes([0.2, 0.1, 0.6, 0.03]),
                    'Time', min_val, max_val,
                    valinit=min_val
                )
                
                self.cursor_line = self.ax_left.axvline(x=min_val, color='red', alpha=0.5, linestyle='--')
                
                def update(val):
                    self.cursor_line.set_xdata([val, val])
                    
                    # Update live values display
                    if self.live_values_widget and self.live_values_widget.isVisible():
                        self.live_values_widget.update_values(val)
                    
                    self.canvas.draw_idle()
                
                self.slider.on_changed(update)
    
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
    def _on_show_debug_settings(self):
        """Show the debug settings dialog."""
        dialog = DebugSettingsDialog(self)
        
        # Get current settings before dialog
        from pid_debug_config import get_pid_debug_setting, get_log_interval, get_log_on_stop, get_position_threshold
        original_settings = {
            'enable': get_pid_debug_setting(),
            'interval': get_log_interval(),
            'log_on_stop': get_log_on_stop(),
            'threshold': get_position_threshold()
        }
        
        if dialog.exec():
            # Settings were applied - update running instances
            new_settings = {
                'enable': get_pid_debug_setting(),
                'interval': get_log_interval(),
                'log_on_stop': get_log_on_stop(),
                'threshold': get_position_threshold()
            }
            
            # Update live values widget if settings changed
            if original_settings != new_settings and self.live_values_widget:
                self.live_values_widget.set_debug_logging(new_settings['enable'])
