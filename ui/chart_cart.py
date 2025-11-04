# Chart cart UI component for managing chart configurations
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ChartCart:
    """Manages a list of chart configurations with thumbnail display."""

    def __init__(self):
        self.configs = []
        self.items = []  # list of (config, frame) tuples

    def add_config(self, config):
        """Add a new chart config and update UI."""
        self.configs.append(config)
        if hasattr(self, 'container'):
            self._add_item(config)

    def remove_config(self, index):
        """Remove config at index."""
        if 0 <= index < len(self.configs):
            del self.configs[index]
            if hasattr(self, 'container'):
                self._rebuild_ui()

    def reorder_configs(self, from_idx, to_idx):
        """Move config from from_idx to to_idx."""
        if 0 <= from_idx < len(self.configs) and 0 <= to_idx < len(self.configs):
            config = self.configs.pop(from_idx)
            self.configs.insert(to_idx, config)
            if hasattr(self, 'container'):
                self._rebuild_ui()

    def build_ui(self, parent):
        """Build the UI in the parent frame."""
        self.parent = parent
        self.container = ttk.Frame(parent)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Scrollable frame for thumbnails
        self.scrollbar = tk.Scrollbar(self.container, orient="vertical", width=20)
        self.canvas = tk.Canvas(self.container)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollbar.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Populate existing configs
        for config in self.configs:
            self._add_item(config)

    def _add_item(self, config):
        """Add a single item to the UI."""
        # Import here to avoid circular imports
        from ui.chart_renderer import ChartRenderer
        
        item_frame = ttk.Frame(self.scrollable_frame, relief="raised", borderwidth=1)
        item_frame.pack(fill=tk.X, padx=2, pady=2)

        # Thumbnail
        renderer = ChartRenderer(config)
        fig = renderer.render_thumbnail()
        canvas = FigureCanvasTkAgg(fig, master=item_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.TOP, padx=2, pady=2)

        # Title
        ttk.Label(item_frame, text=config.title, font=("Segoe UI", 8)).pack(side=tk.TOP, padx=2, pady=(0,2))

        # Buttons
        btn_frame = ttk.Frame(item_frame)
        btn_frame.pack(side=tk.TOP, padx=2, pady=2)

        idx = len(self.items)
        ttk.Button(btn_frame, text="↑", width=2, command=lambda: self._move_up(idx)).pack(side=tk.LEFT, padx=(0,1))
        ttk.Button(btn_frame, text="↓", width=2, command=lambda: self._move_down(idx)).pack(side=tk.LEFT, padx=(1,1))
        ttk.Button(btn_frame, text="X", width=2, command=lambda: self.remove_config(idx)).pack(side=tk.LEFT, padx=(1,0))

        self.items.append((config, item_frame))

    def _move_up(self, idx):
        if idx > 0:
            self.reorder_configs(idx, idx - 1)

    def _move_down(self, idx):
        if idx < len(self.configs) - 1:
            self.reorder_configs(idx, idx + 1)

    def _rebuild_ui(self):
        """Rebuild the entire UI."""
        for _, frame in self.items:
            frame.destroy()
        self.items = []
        for config in self.configs:
            self._add_item(config)
