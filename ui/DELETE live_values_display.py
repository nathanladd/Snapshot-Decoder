"""
Live Values Display Widget

Shows current PID values in color-coded cards that update as the time slider moves.
Integrates with both main window and popout windows.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from typing import Dict, Optional, List
from domain.chart_config import ChartConfig
from domain.pid_interpolator import PIDInterpolator
from ui.color_manager import ColorManager


class PIDCard(ttk.Frame):
    """A single PID value card with color coding."""
    
    def __init__(self, parent, pid_name: str, color: str, initial_value: float = 0.0):
        super().__init__(parent, relief="raised", borderwidth=1)
        
        self.pid_name = pid_name
        self.color = color
        self.value_label = None
        
        self._build_card(initial_value)
    
    def _build_card(self, initial_value: float):
        """Build the card layout with PID name and value."""
        # Configure card style
        style = ttk.Style()
        
        # Create card frame with subtle styling
        self.configure(padding=2)
        
        # PID name label with colored background
        name_style = f"PIDCard.Name.{self.color.replace('#', '')}"
        style.configure(
            name_style,
            background=self.color,
            foreground="white" if self._is_dark_color(self.color) else "black",
            font=("Segoe UI", 9, "bold")
        )
        
        name_label = ttk.Label(self, text=self.pid_name, style=name_style)
        name_label.pack(fill="x", padx=1, pady=(1, 0))
        
        # Value label with clean background
        value_style = "PIDCard.Value"
        style.configure(
            value_style,
            background="white",
            foreground="black",
            font=("Segoe UI", 10, "bold")
        )
        
        self.value_label = ttk.Label(
            self, 
            text=f"{initial_value:.2f}", 
            style=value_style
        )
        self.value_label.pack(fill="x", padx=1, pady=(0, 1))
    
    def update_value(self, value: float):
        """Update the displayed value."""
        if self.value_label:
            if np.isnan(value) or np.isinf(value):
                self.value_label.config(text="--")
            else:
                self.value_label.config(text=f"{value:.2f}")
    
    def _is_dark_color(self, color: str) -> bool:
        """Determine if a color is dark for text contrast."""
        # Simple luminance calculation
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return luminance < 0.5


class LiveValuesDisplay(ttk.Frame):
    """Widget displaying live PID values in color-coded cards."""
    
    def __init__(self, parent, chart_config: Optional[ChartConfig] = None):
        super().__init__(parent)
        
        self.chart_config = chart_config
        self.interpolator = PIDInterpolator()
        self.cards = {}  # pid_name -> PIDCard
        self.current_x_position = 0.0
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the display widget."""
        # Title label
        self.title_label = ttk.Label(
            self, 
            text="PID Values at Current Position", 
            font=("Segoe UI", 10, "bold")
        )
        self.title_label.pack(fill="x", padx=5, pady=(5, 2))
        
        # Cards container with scrollable frame
        self._build_scrollable_container()
    
    def _build_scrollable_container(self):
        """Build scrollable container for cards."""
        # Main container frame
        container_frame = ttk.Frame(self)
        container_frame.pack(fill="both", expand=True, padx=5, pady=2)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(container_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container_frame, orient="horizontal", command=self.canvas.xview)
        self.cards_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling
        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")
        
        # Bind mouse wheel for horizontal scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)  # Linux
        self.canvas.bind("<Button-5>", self._on_mousewheel)  # Linux
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        # Get current scroll position
        scroll_start = self.canvas.xview()[0]
        scroll_end = self.canvas.xview()[1]
        scroll_range = scroll_end - scroll_start
        
        if scroll_range > 0:
            # Calculate scroll amount
            if event.delta:  # Windows
                scroll_amount = -1 * (event.delta / 120) * 0.1
            else:  # Linux
                scroll_amount = -1 * event.delta * 0.1
            
            # Apply scroll
            new_position = max(0, min(1, scroll_start + scroll_amount))
            self.canvas.xview_moveto(new_position)
    
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
        
        # Update cards
        for pid_name, value in values.items():
            if pid_name in self.cards:
                self.cards[pid_name].update_value(value)
        
        # Update title with position
        self._update_title(x_position)
    
    def _rebuild_cards(self):
        """Rebuild all cards based on current chart configuration."""
        # Clear existing cards
        for card in self.cards.values():
            card.destroy()
        self.cards.clear()
        
        if not self.chart_config:
            self.title_label.config(text="PID Values at Current Position")
            return
        
        # Get all PIDs from both axes
        all_pids = []
        all_pids.extend(self.chart_config.primary_axis.series)
        all_pids.extend(self.chart_config.secondary_axis.series)
        
        if not all_pids:
            self.title_label.config(text="PID Values at Current Position")
            return
        
        # Create cards in grid layout
        cols_per_row = 6  # Adjust based on available space
        for i, pid_name in enumerate(all_pids):
            # Determine color and axis
            is_secondary = pid_name in self.chart_config.secondary_axis.series
            series_index = (self.chart_config.secondary_axis.series.index(pid_name) 
                          if is_secondary 
                          else self.chart_config.primary_axis.series.index(pid_name))
            
            color = ColorManager.get_series_color(
                pid_name, is_secondary, series_index, self.chart_config.series_styles
            )
            
            # Create card
            card = PIDCard(self.cards_frame, pid_name, color)
            
            # Position in grid
            row = i // cols_per_row
            col = i % cols_per_row
            card.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            
            # Store reference
            self.cards[pid_name] = card
        
        # Configure grid weights
        for col in range(cols_per_row):
            self.cards_frame.columnconfigure(col, weight=1)
        
        # Update canvas scroll region
        self.cards_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
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
        
        self.title_label.config(text=f"PID Values at {position_str}")
    
    def show(self):
        """Show the display widget."""
        self.pack(fill="both", expand=True)
    
    def hide(self):
        """Hide the display widget."""
        self.pack_forget()
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get interpolator cache information."""
        return self.interpolator.get_cache_info()
    
    def clear_cache(self):
        """Clear the interpolator cache."""
        self.interpolator.clear_cache()
