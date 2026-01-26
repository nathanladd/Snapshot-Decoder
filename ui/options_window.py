"""
Options Window for Snapshot Decoder

Provides a dialog for configuring chart settings and other application preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from domain.chart_settings import chart_settings


class OptionsWindow(tk.Toplevel):
    """
    Options window for configuring chart settings and application preferences.
    """
    
    def __init__(self, parent: tk.Tk, on_settings_changed: Optional[Callable] = None):
        """
        Initialize the options window.
        
        Args:
            parent: Parent window
            on_settings_changed: Optional callback when settings are changed
        """
        super().__init__(parent)
        self.parent = parent
        self.on_settings_changed = on_settings_changed
        
        # Store original values for cancel functionality
        self.original_settings = chart_settings.get_all_settings().copy()
        
        # Setup window
        self.title("Options")
        self.geometry("500x500")
        self.resizable(True, True)
        
        # Center window on parent
        self._center_window()
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        # Build UI
        self._build_ui()
        
        # Load current settings
        self._load_current_settings()
        
        # Focus on window
        self.focus_set()
    
    def _center_window(self):
        """Center the window on the parent window."""
        self.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get our window size (use requested geometry if actual is 0)
        window_width = self.winfo_width() if self.winfo_width() > 1 else 500
        window_height = self.winfo_height() if self.winfo_height() > 1 else 500
        
        # Calculate center position
        x = parent_x + (parent_width // 2) - (window_width // 2)
        y = parent_y + (parent_height // 2) - (window_height // 2)
        
        # Ensure window is visible on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        self.geometry(f"+{x}+{y}")
    
    def _build_ui(self):
        """Build the options window UI."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Chart Settings", 
                                font=("Segoe UI", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Chart Appearance tab
        chart_frame = ttk.Frame(notebook)
        notebook.add(chart_frame, text="Chart Appearance")
        self._build_chart_settings(chart_frame)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Buttons
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Reset to Defaults", command=self._on_reset).pack(side=tk.LEFT)
    
    def _build_chart_settings(self, parent):
        """Build chart settings controls."""
        # Container for settings
        settings_container = ttk.Frame(parent, padding="15")
        settings_container.pack(fill=tk.BOTH, expand=True)
        
        # Legend Font Size
        legend_frame = ttk.Frame(settings_container)
        legend_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(legend_frame, text="Legend Font Size:").pack(side=tk.LEFT)
        self.legend_font_size_var = tk.IntVar()
        legend_spinbox = ttk.Spinbox(legend_frame, from_=6, to=20, width=10,
                                     textvariable=self.legend_font_size_var)
        legend_spinbox.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add description
        ttk.Label(settings_container, text="Font size for chart legends (6-20 points)",
                 font=("Segoe UI", 9), foreground="gray").pack(anchor=tk.W, pady=(0, 10))
        
        # Line Width
        line_frame = ttk.Frame(settings_container)
        line_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(line_frame, text="Line Width:").pack(side=tk.LEFT)
        self.line_width_var = tk.DoubleVar()
        line_spinbox = ttk.Spinbox(line_frame, from_=0.5, to=5.0, increment=0.5, width=10,
                                   textvariable=self.line_width_var)
        line_spinbox.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add description
        ttk.Label(settings_container, text="Thickness of chart lines (0.5-5.0)",
                 font=("Segoe UI", 9), foreground="gray").pack(anchor=tk.W, pady=(0, 10))
        
        # Grid Line Width
        grid_frame = ttk.Frame(settings_container)
        grid_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(grid_frame, text="Grid Line Width:").pack(side=tk.LEFT)
        self.grid_linewidth_var = tk.DoubleVar()
        grid_spinbox = ttk.Spinbox(grid_frame, from_=0.1, to=2.0, increment=0.1, width=10,
                                   textvariable=self.grid_linewidth_var)
        grid_spinbox.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add description
        ttk.Label(settings_container, text="Thickness of grid lines (0.1-2.0)",
                 font=("Segoe UI", 9), foreground="gray").pack(anchor=tk.W, pady=(0, 10))
        
        # Marker Size
        marker_frame = ttk.Frame(settings_container)
        marker_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(marker_frame, text="Marker Size:").pack(side=tk.LEFT)
        self.marker_size_var = tk.DoubleVar()
        marker_spinbox = ttk.Spinbox(marker_frame, from_=2.0, to=15.0, increment=0.5, width=10,
                                     textvariable=self.marker_size_var)
        marker_spinbox.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add description
        ttk.Label(settings_container, text="Size of data point markers (2.0-15.0)",
                 font=("Segoe UI", 9), foreground="gray").pack(anchor=tk.W)
    
    def _load_current_settings(self):
        """Load current settings into the UI controls."""
        self.legend_font_size_var.set(chart_settings.legend_font_size)
        self.line_width_var.set(chart_settings.line_width)
        self.grid_linewidth_var.set(chart_settings.grid_linewidth)
        self.marker_size_var.set(chart_settings.marker_size)
    
    def _apply_settings(self):
        """Apply settings from UI to the chart settings."""
        try:
            # Validate values
            legend_size = self.legend_font_size_var.get()
            line_width = self.line_width_var.get()
            grid_width = self.grid_linewidth_var.get()
            marker_size = self.marker_size_var.get()
            
            # Apply to settings
            chart_settings.legend_font_size = legend_size
            chart_settings.line_width = line_width
            chart_settings.grid_linewidth = grid_width
            chart_settings.marker_size = marker_size
            
            # Save settings
            chart_settings.save_settings()
            
            # Notify parent of changes
            if self.on_settings_changed:
                self.on_settings_changed()
                
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
            return False
    
    def _on_ok(self):
        """Handle OK button click."""
        if self._apply_settings():
            self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        # Restore original settings
        for key, value in self.original_settings.items():
            chart_settings.set_setting(key, value)
        self.destroy()
    
    def _on_reset(self):
        """Handle Reset to Defaults button click."""
        result = messagebox.askyesno("Reset Settings", 
                                     "Are you sure you want to reset all chart settings to their default values?")
        if result:
            # Reset to defaults
            chart_settings.reset_to_defaults()
            # Update UI
            self._load_current_settings()
            # Show confirmation
            messagebox.showinfo("Settings Reset", "Chart settings have been reset to default values.")
