# header_panel.py
# Simple, dependable 2-column header panel + parser for your Snapshot Reader.

import tkinter as tk
from tkinter import ttk
import pandas as pd
from domain.snaptypes import SnapType

#Dictionary variable
# Standardize the labels found in the header. - labels we expect in row 0..3, col 0, with values in col 1.
CANON_LABELS = {
    "engine model": "Engine Model",
    "ecu map version": "ECU Map Version",
    "program sw version": "Program SW Version",
    "data logging": "Data Logging"
}

_BUTTONS_BY_TYPE: dict[SnapType, list[tuple[str, str, str]]] = {
    SnapType.ECU_V1: [
        ("Battery Test", "battery_test", "Plot battery V vs RPM"),
        ("Rail Pressure", "rail_pressure", "Demand vs Actual + Gap"),
        ("IMV Test", "imv_test", "Demand vs Feedback"),
        ("Injector Balance", "inj_balance", "Delta speed per cylinder"),
        ("Start Health", "start_health", "Cranking RPM, V, rail build"),
    ],
    SnapType.ECU_V2: [
        ("Start Health", "start_health", "Cranking RPM, V, rail build"),
        ("Boost Check", "boost_check", "MAP vs Atmosphere"),
        ("EGR Position", "egr_position", "Cmd vs Feedback"),
    ],
    SnapType.DCU_V1: [
        ("Usage Summary", "usage_summary", "Key hours, PTO, load"),
        ("Min/Max Chart", "minmax_chart", "Voltage & RPM extremes"),
    ],
    SnapType.EUD_V1: [
        ("I/O Monitor", "io_monitor", "Digital/analog channels"),
        ("Fault Timeline", "fault_timeline", "DTCs over time"),
    ],
}

# Tool Tip Class
class ToolTip:
    """Attach a tooltip to any Tkinter widget."""

    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # milliseconds before showing
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)

    def _schedule(self, event=None):
        self._unschedule()
        self.id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def _show(self):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # remove window borders
        tw.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(
            tw, text=self.text, justify="left",
            background="#ffffe0", relief="solid", borderwidth=1,
            padding=(5, 3)
        )
        label.pack(ipadx=1)

    def _hide(self, event=None):
        self._unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


def _normalize_label(text: str) -> str:
    """
    Normalize a label to a canonical display name if recognized.
    Loosened matching: exact, case-insensitive; also allows minor spacing/punctuation differences.
    """
    if not text:
        return ""
    raw = text.strip().lower()
    # quick exact lookup
    if raw in CANON_LABELS:
        return CANON_LABELS[raw]

    # light fuzzy: remove punctuation/spaces to catch 'Program SW Version' vs 'Program SW-Version'
    squished = "".join(ch for ch in raw if ch.isalnum())
    for k, v in CANON_LABELS.items():
        k_squished = "".join(ch for ch in k if ch.isalnum())
        if squished == k_squished:
            return v

    # fall back to original as-is if unknown
    return text.strip()

def parse_simple_header(df: pd.DataFrame, max_rows: int = 4):
    """
    Parse up to the first `max_rows` rows as 2-column key/value pairs.
    - Column 0: label (string)
    - Column 1: value (string)
    - Stops early if Column 0 == 'Frame' (table header reached).
    Returns: ordered list of (key, value).
    """
    results = []
    if df is None or df.empty:
        return results

    nrows = min(max_rows, df.shape[0])
    for r in range(nrows):
        # Stop if we hit the actual table header row
        try:
            k_raw = str(df.iat[r, 0]).strip()
        except Exception:
            k_raw = ""
        if k_raw and k_raw.lower() == "frame":
            break

        # Pull the value column
        try:
            v_raw = str(df.iat[r, 1]).strip()
        except Exception:
            v_raw = ""

        # Skip truly empty/NaN-ish rows
        if not k_raw or k_raw.lower() == "nan":
            continue
        if not v_raw or v_raw.lower() == "nan":
            # Keep keys without values? For this app, we skip them.
            continue

        key = _normalize_label(k_raw)
        value = v_raw
        results.append((key, value))

    return results


class SimpleHeaderPanel(ttk.Frame):
    """
    Minimal two-column label panel for showing header key/value pairs.
    Usage:
        panel = SimpleHeaderPanel(parent)
        panel.set_rows([("Engine Model","X"), ("ECU Map Version","Y")])
    """
    

    def __init__(self, master, on_action=None):
        super().__init__(master)
        # Properties
        self._row_start = 1
        self._rows = []  # track widgets so we can clear

        self._button_widgets: list[ttk.Button] = []
        self.on_action = on_action

        self._snaptype: SnapType | None = None

        # Snapshot Information Frame
        self.snap_info_frame = ttk.Labelframe(self, text="Snapshot Information")
        self.snap_info_frame.pack(side="left", fill="y", expand=False, pady=(4,6), padx=(4,0))

        #Add a 3rd column to make white space between header and PID info
        self.snap_info_frame.columnconfigure(2,minsize=30)     
        
        # Snapshot Quick Chart Buttons
        self.button_frame = ttk.Labelframe(self, text="Quick Chart Buttons")
        self.button_frame.pack(side="left", fill="y", expand=False, pady=(4,6), padx=(4,4))
        #ttk.Label(self.button_frame, text="Test Button Label").pack(padx=10, pady=10)
       

    #Accept SnapType and set correct lable information
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

        specs = _BUTTONS_BY_TYPE.get(snaptype, [])
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
