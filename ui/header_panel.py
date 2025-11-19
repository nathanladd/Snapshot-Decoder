
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys

from domain.snaptypes import SnapType
from ui.tool_tip import ToolTip
from domain.constants import BUTTONS_BY_TYPE


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    # Check if running as PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Intended to be used as a child of the main window
# First label frame shows snapshot information
# Second label frame shows quick chart buttons
# SnapType is used to determine which buttons to show

class HeaderPanel(ttk.Frame):
    """Header Panel for Snapshot Reader"""    

    def __init__(self, master, on_action=None):
        super().__init__(master)
        self.on_action = on_action
        self._initialize_header()

    def _initialize_header(self):
        # Properties
        self._row_start = 1
        self._rows = []
        self._snaptype: SnapType | None = None

        # Logo graphic to the right side of the header panel
        try:
            logo_path = resource_path("logo.png")
            if os.path.exists(logo_path):
                image = Image.open(logo_path)
                photo = ImageTk.PhotoImage(image)
                label = ttk.Label(self, image=photo)
                label.image = photo
                label.pack(side="right", padx=(4, 4), pady=(4, 6))
        except Exception:
            pass  # If logo fails to load, continue without it
       
    def clear_header_panel(self):
        """Completely clear the header panel"""
        for widget in self.winfo_children():
            widget.destroy()
        self._initialize_header()


    #Accept SnapType and set correct label information
    def set_header_snaptype(self, snaptype: SnapType):
        if snaptype:
            self._snaptype = snaptype

    def build_quick_chart(self):
        if self._snaptype is SnapType.EMPTY:
            return

        # Property to track widgets so we can clear them later
        self._button_widgets: list[ttk.Button] = []

        # Clear existing buttons, if any
        for b in self._button_widgets:
            b.destroy()
        self._button_widgets.clear()

        # Snapshot Quick Chart Buttons frame
        self.button_frame = ttk.Labelframe(self, text="Quick Charts")
        self.button_frame.pack(side="left", fill="y", expand=False, pady=(4,6), padx=(4,4))

        # Create buttons in a flowing grid
        specs = BUTTONS_BY_TYPE.get(self._snaptype, [])
        max_per_row = 5
        for i, (text, action_id, _tip) in enumerate(specs):
            btn = ttk.Button(self.button_frame, text=text,
                             command=lambda a=action_id: self._handle_click(a))
            r, c = divmod(i, max_per_row)
            ToolTip(btn, _tip)
            btn.grid(row=r, column=c, padx=(0, 6), pady=(0, 6), sticky="w")
            # Add new button to wigit list
            self._button_widgets.append(btn)

    # Event handler that handles the button presses 
    def _handle_click(self, action_id: str):
        if callable(self.on_action):
            self.on_action(action_id, self._snaptype)

    # Helper function for build_quick_header to clear all rows
    def clear(self):
        for w in self._rows:
            w.destroy()
        self._rows.clear()

    # Build the header panel with the given information
    def build_quick_header(self, file_name: str, header_list: list[tuple[str, str]], 
    hours: float, mdp_success_rate: float, total_pids: int, frames_found: int):
        """
        header list: iterable of (label, value). 
        hours: float
        mdp_success_rate: float
        total_pids: int
        frames_found: int
        """
        self.clear()
        r = self._row_start

        # Create custom label for the frame with bold larger font
        label = ttk.Label(self, text=file_name, font=("Segoe UI", 12, "bold"))

        # Snapshot Information Frame
        self.snap_info_frame = ttk.Labelframe(self, labelwidget=label)
        self.snap_info_frame.pack(side="left", fill="y", expand=False, pady=(4,6), padx=(4,0))
        
        # Show known labels in a friendly order first, then the rest
        priority = ["Snapshot Type", "Date / Time", "Engine Model", "ECU Map Version", 
        "Program SW Version", "Data Logging", "Engine No"]
        used = set()

        def add_row(k, v):
            k_lbl = ttk.Label(self.snap_info_frame, text=f"{k}:", font=("Segoe UI", 9, "bold"))
            v_lbl = ttk.Label(self.snap_info_frame, text=v, justify="left", anchor="w",)
            k_lbl.grid(row=r_dict["r"], column=0, sticky="ne", padx=(0, 5), pady=1)
            v_lbl.grid(row=r_dict["r"], column=1, sticky="w", pady=1)
            self._rows.extend([k_lbl, v_lbl])
            r_dict["r"] += 1

        r_dict = {"r": r}

        # append snapshot type to the top of the list
        add_row("Snapshot Type", self._snaptype)

        # priority pass
        for want in priority:
            for k, v in header_list:
                if k == want and (k, v) not in used:
                    add_row(k, v)
                    used.add((k, v))
        # remaining
        for k, v in header_list:
            if (k, v) not in used:
                add_row(k, v)
        
        # append other information
        if total_pids > 0:
            add_row("Total PIDs", total_pids)
        if frames_found > 0:
            add_row("Frames Found", frames_found)
        if hours > 0:
            add_row("Engine Hours", hours)
        if mdp_success_rate > 0:
            add_row("MDP Success %", mdp_success_rate)

