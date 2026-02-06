"""
Pop-out Chart Window

A standalone window that displays a chart with its own toolbar.
"""

import copy
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction

from matplotlib.figure import Figure
from matplotlib.widgets import Slider
import mplcursors

from domain.chart_config import ChartConfig
from ui.chart_renderer import ChartRenderer
from ui_pyside6.widgets.custom_toolbar import CustomNavigationToolbar


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
        
        self.slider_checkbox = QCheckBox("Time Slider")
        self.slider_checkbox.stateChanged.connect(self._on_interactivity_change)
        controls_layout.addWidget(self.slider_checkbox)
        
        self.cursor_checkbox = QCheckBox("Hover Cursor")
        self.cursor_checkbox.stateChanged.connect(self._on_interactivity_change)
        controls_layout.addWidget(self.cursor_checkbox)
        
        controls_layout.addStretch()
        
        if self.chart_cart:
            add_to_cart_btn = QPushButton("Add to Cart")
            add_to_cart_btn.clicked.connect(self._add_to_cart)
            controls_layout.addWidget(add_to_cart_btn)
        
        main_layout.addLayout(controls_layout)
        
        # Create figure and canvas
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()
        
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        self.canvas = FigureCanvas(self.figure)
        
        # Add custom toolbar
        self.toolbar = CustomNavigationToolbar(self.canvas, self)
        main_layout.addWidget(self.toolbar)
        
        # Pack canvas
        main_layout.addWidget(self.canvas, stretch=1)
    
    def _setup_menu(self):
        """Set up the window menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        close_action = QAction("&Close", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
    
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
    
    @Slot(int)
    def _on_interactivity_change(self, state):
        """Callback when interactivity options change."""
        self.enable_slider = self.slider_checkbox.isChecked()
        self.enable_cursor = self.cursor_checkbox.isChecked()
        
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
            import pandas as pd
            df = self.config.data.copy()
            x_col = self.config.get_x_column()
            
            if pd.api.types.is_timedelta64_dtype(df.get("Time")):
                df["Time"] = df["Time"].dt.total_seconds()
            elif pd.api.types.is_timedelta64_dtype(df.get("Time (MM:SS)")):
                df["Time (MM:SS)"] = df["Time (MM:SS)"].dt.total_seconds()
            
            if x_col and x_col in df.columns:
                x_data = df[x_col]
            else:
                x_data = df.index
            
            min_val = float(x_data.min())
            max_val = float(x_data.max())
            
            self.figure.subplots_adjust(bottom=0.2)
            ax_slider = self.figure.add_axes([0.15, 0.05, 0.7, 0.03])
            
            self.slider = Slider(
                ax=ax_slider,
                label=x_col if x_col else "Index",
                valmin=min_val,
                valmax=max_val,
                valinit=min_val,
            )
            
            self.cursor_line = self.ax_left.axvline(x=min_val, color='red', alpha=0.5, linestyle='--')
            
            def update(val):
                self.cursor_line.set_xdata([val, val])
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
