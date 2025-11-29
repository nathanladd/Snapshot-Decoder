"""
Pop-out Chart Window

A standalone window that displays a chart with its own toolbar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy
import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Slider
import mplcursors

from domain.chart_config import ChartConfig
from ui.chart_renderer import ChartRenderer
from ui.custom_toolbar import CustomNavigationToolbar


class ChartPopupWindow(tk.Toplevel):
    """A pop-out window displaying a chart with toolbar."""
    
    def __init__(self, parent, config: ChartConfig, chart_cart=None):
        super().__init__(parent)
        
        # Deep copy config to make this window independent
        self.config = copy.deepcopy(config)
        self.chart_cart = chart_cart
        
        # Window setup
        self.title(self.config.title or "Chart")
        self.geometry("1000x600")
        
        # Interactivity controls
        self.enable_slider = tk.BooleanVar(value=False)
        self.enable_cursor = tk.BooleanVar(value=False)
        self.enable_slider.trace_add("write", self._on_interactivity_change)
        self.enable_cursor.trace_add("write", self._on_interactivity_change)
        
        # Interactivity state
        self.slider = None
        self.cursor_line = None
        self.mpl_cursor = None
        
        # Build the UI
        self._build_ui()
        
        # Render the chart
        self._render_chart()
    
    def _build_ui(self):
        """Build the window UI."""
        # Main frame
        main_frame = ttk.Frame(self, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create figure and canvas
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=main_frame)
        
        # Add custom toolbar with cursor/values toggles and add to cart
        self.toolbar = CustomNavigationToolbar(
            self.canvas, main_frame, pack_toolbar=False,
            chart_config=self.config,
            cursor_var=self.enable_slider,
            values_var=self.enable_cursor,
            add_to_cart_callback=self._add_to_cart if self.chart_cart else None
        )
        self.toolbar.update()
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Pack canvas
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
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
    
    def _on_interactivity_change(self, *args):
        """Callback when interactivity options change."""
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
        if self.enable_cursor.get():
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
        if self.enable_slider.get():
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
    
    def _add_to_cart(self):
        """Add a copy of this chart's config to the cart."""
        if not self.chart_cart:
            messagebox.showinfo("No cart", "Cart not available.")
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
