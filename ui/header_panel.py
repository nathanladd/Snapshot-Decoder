# header_panel.py
# Simple, dependable 2-column header panel + parser for your Snapshot Reader.


from tkinter import ttk
# import pandas as pd
from domain.snaptypes import SnapType
from ui.tool_tip import ToolTip
from domain.constants import BUTTONS_BY_TYPE





class HeaderPanel(ttk.Frame):
    """
    Minimal two-column label panel for showing header key/value pairs.
    Usage:
        panel = SimpleHeaderPanel(parent)
        panel.set_rows([("Engine Model","X"), ("ECU Map Version","Y")])
    """
    

    def __init__(self, master, on_action=None):
        super().__init__(master)
        self.on_action = on_action
        self._initialize_header()

    def _initialize_header(self):
        # Properties
        self._row_start = 1
        self._rows = []  # track widgets so we can clear

        self._button_widgets: list[ttk.Button] = []
        

        self._snaptype: SnapType | None = None

        # Snapshot Information Frame
        self.snap_info_frame = ttk.Labelframe(self, text="Snapshot Information")
        self.snap_info_frame.pack(side="left", fill="y", expand=False, pady=(4,6), padx=(4,0))

        #Add a 3rd column to make white space between header and PID info
        self.snap_info_frame.columnconfigure(2,minsize=30)     
        
        # Snapshot Quick Chart Buttons
        self.button_frame = ttk.Labelframe(self, text="Quick Chart Buttons")
        self.button_frame.pack(side="left", fill="y", expand=False, pady=(4,6), padx=(4,4))
       
    def clear_header_panel(self):
        """Completely rebuild panel if structure may have changed."""
        for widget in self.winfo_children():
            widget.destroy()
        self._initialize_header()


    #Accept SnapType and set correct label information
    def set_snaptype_info(self, snaptype: SnapType):
        self._snaptype = snaptype
        engine_version = ttk.Label(self.snap_info_frame, text="Snapshot Type:", font=("Segoe UI", 9, "bold"))
        engine_version.grid(row=1, column=3, sticky="ne", pady=(0, 3))
        st_lbl = ttk.Label(self.snap_info_frame, text=snaptype, justify="left", anchor="w",)
        st_lbl.grid(row=1, column=4, sticky="w", padx=(0, 3), pady=1)

        for b in self._button_widgets:
            b.destroy()
        self._button_widgets.clear()

        if snaptype is SnapType.UNKNOWN:
            return

        specs = BUTTONS_BY_TYPE.get(snaptype, [])
        # Create buttons in a flowing grid: 4 per row looks tidy; adjust as you like
        max_per_row = 4
        for i, (text, action_id, _tip) in enumerate(specs):
            btn = ttk.Button(self.button_frame, text=text,
                             command=lambda a=action_id: self._handle_click(a))
            r, c = divmod(i, max_per_row)
            ToolTip(btn, _tip)
            btn.grid(row=r, column=c, padx=(0, 6), pady=(0, 6), sticky="w")
            self._button_widgets.append(btn)

    # Event handler that handles the button presses 
    def _handle_click(self, action_id: str):
        if callable(self.on_action):
            self.on_action(action_id, self._snaptype)


    #Accept PID info and fill the correct header labels
    def set_pid_info(self, total_pids="", frames_found=""):
        '''Number of PIDS, and Frames'''
        pids_found = ttk.Label(self.snap_info_frame, text="PIDs:", font=("Segoe UI", 9, "bold"))
        pids_found.grid(row=2, column=3, sticky="ne", pady=(0, 3))
        pids_lbl = ttk.Label(self.snap_info_frame, text=total_pids, justify="left", anchor="w",)
        pids_lbl.grid(row=2, column=4, sticky="w", padx=(0, 3), pady=1)
        self.frames_found = ttk.Label(self.snap_info_frame, text="Frames:", font=("Segoe UI", 9, "bold"))
        self.frames_found.grid(row=3, column=3, sticky="ne", pady=(0, 3))
        frames_lbl = ttk.Label(self.snap_info_frame, text=frames_found, justify="left", anchor="w",)
        frames_lbl.grid(row=3, column=4, sticky="w", padx=(0, 3), pady=1)

    def clear(self):
        for w in self._rows:
            w.destroy()
        self._rows.clear()

    def set_rows(self, pairs):
        """
        pairs: iterable of (key, value)
        """
        self.clear()
        r = self._row_start
        # Show known keys in a friendly order first, then the rest
        priority = ["Engine Model", "ECU Map Version", "Program SW Version", "Data Logging", "Engine No"]
        used = set()

        def add_row(k, v):
            k_lbl = ttk.Label(self.snap_info_frame, text=f"{k}:", font=("Segoe UI", 9, "bold"))
            v_lbl = ttk.Label(self.snap_info_frame, text=v, justify="left", anchor="w",)
            k_lbl.grid(row=r_dict["r"], column=0, sticky="ne", padx=(0, 5), pady=1)
            v_lbl.grid(row=r_dict["r"], column=1, sticky="w", pady=1)
            self._rows.extend([k_lbl, v_lbl])
            r_dict["r"] += 1

        r_dict = {"r": r}
        # priority pass
        for want in priority:
            for k, v in pairs:
                if k == want and (k, v) not in used:
                    add_row(k, v)
                    used.add((k, v))
        # remaining
        for k, v in pairs:
            if (k, v) not in used:
                add_row(k, v)
