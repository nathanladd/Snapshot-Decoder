'''
Main Window

'''

from __future__ import annotations
import sys
import os

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict, Callable, Tuple

import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from domain.snaptypes import SnapType
from file_io.reader_excel import load_xls, load_xlsx
from services.parse_header import parse_header
from services.parse_snapshot import id_snapshot, find_pid_names, extract_pid_descriptions, scrub_snapshot
from domain.constants import APP_TITLE, APP_VERSION, BUTTONS_BY_TYPE

# Class to manage Snapshot header information
from ui.header_panel import HeaderPanel





class SnapshotDecoderApp(tk.Tk):

    #__init__ is a special built-in method name in Python. 
    # When you create (or “instantiate”) an object from a class, 
    # Python automatically calls this method. 
    # It’s where you set up the initial state of the object — 
    # like its variables, default values, 
    # or anything else that needs to happen right when it’s born.

    def __init__(self):
        # super().__init__() says: “Run whatever setup the parent class 
        # normally does before I do my own stuff.” 
        # It’s like calling your parent’s __init__ before adding 
        # your own custom initialization steps.
        super().__init__()
        self.state("zoomed")
        self._initialize_state()
        self._build_ui()


    def _initialize_state(self):
        '''initialize or reset all app-level parameters'''        
        self.snapshot: Optional[pd.DataFrame] = None
        self.raw_snapshot: Optional[pd.DataFrame] = None
        self.pid_info: dict[str, dict[str, str]] = {}
        self.snapshot_path: str = None
        self.snapshot_type = SnapType.EMPTY

        # Lists to hold PIDs charted on Primary and Secondary Axis'
        self.primary_series: List[str] = []
        self.secondary_series: List[str] = []
    
        # Axis limits state
        self.primary_min = tk.StringVar()
        self.primary_max = tk.StringVar()
        self.secondary_min = tk.StringVar()
        self.secondary_max = tk.StringVar()

        self.primary_ymin = tk.StringVar(value="")
        self.primary_ymax = tk.StringVar(value="")
        self.secondary_ymin = tk.StringVar(value="")
        self.secondary_ymax = tk.StringVar(value="")
        self.primary_auto = tk.BooleanVar(value=True)
        self.secondary_auto = tk.BooleanVar(value=True)
        
    def _build_ui(self):
        self._set_window_title()
        self._build_menu()
        self._build_layout()          # uses the variables above
        self._build_plot_area()       # may call _toggle_* which also needs them
        self._update_controls_state(enabled=False)

    def _clear_ui(self):
        """Reset all data and UI components to blank/default."""
        self._initialize_state()
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

#---------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------- UI Construction ----------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------

    def _set_window_title(self):
        '''Update the window title
        If a Snapshot is open, include its name and path'''
        if self.snapshot_path:
            self.title(f"{APP_TITLE} : {os.path.basename(self.snapshot_path)}")
        else:
            self.title(APP_TITLE)
   
    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Snapshot…", command=self.open_file)
        file_menu.add_command(label="Close Snapshot", command=self._clear_ui)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Raw Data...", command=lambda: self.open_data_table(self.raw_snapshot))
        view_menu.add_command(label="Snapshot Table...", command=lambda: self.open_data_table(self.snapshot))
        view_menu.add_command(label="PID Descriptions...", command=self.show_pid_info)
        menubar.add_cascade(label="Data", menu=view_menu)

        plot_menu = tk.Menu(menubar, tearoff=0)
        plot_menu.add_command(label="Combo Line Chart", command=self.plot_combo_chart)
        menubar.add_cascade(label="Plot", menu=plot_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(f"{APP_TITLE} {APP_VERSION} ",  
            "Written by Nate Ladd\n" 
            "Service Trainer\n" 
            "Bobcat of the Rockies\n" 
            "nladd@bobcatoftherockies.com"
            ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_layout(self):
        root = ttk.Frame(self)
        root.pack(fill=tk.BOTH, expand=True)

        # Border frames for main UI
        header_border = ttk.Frame(root, relief="groove", borderwidth=2)
        header_border.pack(fill="x", padx=4, pady=4)
        
        left_border = ttk.Frame(root, relief="groove", borderwidth=2)
        left_border.pack(side="left", fill="y", padx=4, pady=4)

        chart_border = ttk.Frame(root, relief="groove", borderwidth=2)
        chart_border.pack(side="right", fill="both", expand=True, padx=4, pady=4)

        # Snapshot Header Information
        self.header_panel = HeaderPanel(header_border, on_action=self.handle_header_action)
        self.header_panel.pack(anchor="nw", padx=4, pady=4) 

        # Search box label
        ttk.Label(left_border, text="Search PIDs", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        
        # Search box
        self.search_var = tk.StringVar()
        search = ttk.Entry(left_border, textvariable=self.search_var)
        search.pack(fill=tk.X, pady=(4, 8), padx=(8,8))
        search.bind("<KeyRelease>", lambda e: self._filter_pids())

        # All columns listbox (multi-select)
        self.pid_list = tk.Listbox(left_border, selectmode=tk.EXTENDED, exportselection=False, height=22, width=43)
        self.pid_list.pack(fill=tk.Y)

        # Buttons to add to primary/secondary
        btns = ttk.Frame(left_border)
        btns.pack(fill=tk.X, pady=8)
        ttk.Button(btns, text="➕ Add to Primary", command=lambda: self._add_selected(target="primary")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))
        ttk.Button(btns, text="➕ Add to Secondary", command=lambda: self._add_selected(target="secondary")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4,0))

        # Buckets display
        buckets = ttk.Frame(left_border)
        buckets.pack(fill=tk.BOTH, expand=False)

        # Primary frame with min/max
        primary_frame = ttk.Labelframe(buckets, text="Primary axis (left)")
        primary_frame.pack(fill=tk.BOTH, expand=False, pady=(4,6))
        self.primary_list = tk.Listbox(primary_frame, height=6, exportselection=False)
        self.primary_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pf_controls = ttk.Frame(primary_frame)
        pf_controls.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(pf_controls, text="▲", width=3, command=lambda: self._move_in_list(self.primary_list, -1)).pack(pady=2)
        ttk.Button(pf_controls, text="▼", width=3, command=lambda: self._move_in_list(self.primary_list, +1)).pack(pady=2)
        ttk.Button(pf_controls, text="🗑", width=3, command=lambda: self._remove_selected_from("primary")).pack(pady=2)

        # Secondary frame with min/max
        secondary_frame = ttk.Labelframe(buckets, text="Secondary axis (right)")
        secondary_frame.pack(fill=tk.BOTH, expand=False)
        self.secondary_list = tk.Listbox(secondary_frame, height=6, exportselection=False)
        self.secondary_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sf_btns = ttk.Frame(secondary_frame)
        sf_btns.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(sf_btns, text="▲", width=3, command=lambda: self._move_in_list(self.secondary_list, -1)).pack(pady=2)
        ttk.Button(sf_btns, text="▼", width=3, command=lambda: self._move_in_list(self.secondary_list, +1)).pack(pady=2)
        ttk.Button(sf_btns, text="🗑", width=3, command=lambda: self._remove_selected_from("secondary")).pack(pady=2)

        # Axis controls
        axis = ttk.Labelframe(left_border, text="Axis ranges (optional)")
        axis.pack(fill=tk.X, pady=(8,6))

        # Primary axis controls
        p_row = ttk.Frame(axis)
        p_row.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(p_row, text="Primary auto", variable=self.primary_auto, command=self._toggle_primary_inputs).pack(side=tk.LEFT)
        ttk.Label(p_row, text="min").pack(side=tk.LEFT, padx=(8,2))
        self.primary_min_entry = ttk.Entry(p_row, width=8, textvariable=self.primary_ymin)
        self.primary_min_entry.pack(side=tk.LEFT)
        ttk.Label(p_row, text="max").pack(side=tk.LEFT, padx=(8,2))
        self.primary_max_entry = ttk.Entry(p_row, width=8, textvariable=self.primary_ymax)
        self.primary_max_entry.pack(side=tk.LEFT)

        # Secondary axis controls
        s_row = ttk.Frame(axis)
        s_row.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(s_row, text="Secondary auto", variable=self.secondary_auto, command=self._toggle_secondary_inputs).pack(side=tk.LEFT)
        ttk.Label(s_row, text="min").pack(side=tk.LEFT, padx=(8,2))
        self.secondary_min_entry = ttk.Entry(s_row, width=8, textvariable=self.secondary_ymin)
        self.secondary_min_entry.pack(side=tk.LEFT)
        ttk.Label(s_row, text="max").pack(side=tk.LEFT, padx=(8,2))
        self.secondary_max_entry = ttk.Entry(s_row, width=8, textvariable=self.secondary_ymax)
        self.secondary_max_entry.pack(side=tk.LEFT)

        # Plot button
        tk.Button(left_border, text="Plot Selected PIDs", font=("Segoe UI", 11, "bold"), command=self.plot_combo_chart).pack(fill=tk.X, padx=(6,6), pady=(4,4))

        # Right: figure area
        self.right = ttk.Frame(chart_border, padding=10)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",              # left-align text
            relief="sunken",         # classic status bar look
            padding=(8, 2)
        )
        self.status_bar.pack(side="bottom", fill="x")
    
    def set_status(self, text: str):
        """Update the status bar text and keep the UI snappy."""
        self.status_var.set(text)
        # Force a quick redraw so the message appears immediately
        self.status_bar.update_idletasks()

    def _build_plot_area(self):
        # Create an empty figure placeholder
        self.figure = Figure(figsize=(7,5), dpi=100)
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()
        self.ax_left.set_title("Combo Line Chart")
        self.ax_left.set_xlabel("Index / Time")
        self.ax_left.set_ylabel("Primary")
        self.ax_right.set_ylabel("Secondary")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.right)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

         # Initialize input toggle states after widgets exist
        try:
            self._toggle_primary_inputs()
            self._toggle_secondary_inputs()
        except Exception:
            pass

#---------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------- Data Loading ----------------------------------------------------
#--------------------------------------------Open and Process the Snapshot--------------------------------------------
    
    #Open the SnapShot
    def open_file(self):

        # Use an Open File diaglog box to get the file path
        path = filedialog.askopenfilename(
            title="Open Bobcat Snapshot File",
            filetypes=[("Fake .xls", ".xls"), ("Converted Excel", "*.xlsx"), ("All files", "*.*")]
        )
        if not path:
            return
        
        self._clear_ui()
        self.snapshot_path = path

        # Get the new file extension and decide how to process it
        ext = os.path.splitext(self.snapshot_path)[1].lower()
        if ext == ".xlsx":       
            try:
                self.raw_snapshot = load_xlsx(self.snapshot_path)
            except Exception as e:
                messagebox.showerror("Load failed", f"Couldn't load file.\n\n{e}")
                return
        elif ext == ".xls":       
            try:
                self.raw_snapshot = load_xls(self.snapshot_path)
            except Exception as e:
                messagebox.showerror("Load failed", f"Couldn't load file.\n\n{e}")
                return     
        else:
            messagebox.showerror("Unsupported file type", f"Unknown file extension: {ext}")
            return
        
        if self.raw_snapshot is None or self.raw_snapshot.empty:
            messagebox.showerror("No data", "The workbook loaded but no data table was found.")
            return

        # Pull any header information from the Snapshot if it exists
        header_info = parse_header(self.raw_snapshot, max_rows=4)
        if header_info:
            self.header_panel.set_rows(header_info)
        else:
            self.header_panel.set_rows([("Header", "No header info present")])

        # ID the snapshot snapshot type
        header_row_idx = find_pid_names(self.raw_snapshot)
        self.snapshot_type = id_snapshot(self.raw_snapshot, header_row_idx)
        self.pid_info = extract_pid_descriptions(self.raw_snapshot, header_row_idx)  

        # Clean the snapshot
        self.snapshot = scrub_snapshot(self.raw_snapshot, header_row_idx)

        # Update the UI
        self._update_controls_state(enabled=True)
        self._set_window_title()
        self.header_panel.set_pid_info(total_pids=len(self.snapshot.columns), frames_found=len(self.snapshot))
        self.header_panel.set_header_snaptype(self.snapshot_type)
        self.set_status(f"Loaded {len(self.snapshot)} Frames of {len(self.snapshot.columns)} PIDs from file: {os.path.basename(self.snapshot_path)}")
        self._populate_pid_list()

#------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------ Button Handling ------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------

    # Button handler for quick chart actions - Uses dispatch dictionary to map action IDs to handler functions
    def handle_header_action(self, action_id: str, snaptype: SnapType):
        print(f"[Quick Chart Button Action] {snaptype}: {action_id}")

        # Dispatch table: map action IDs to handler functions
        dispatch = {
            "V1_BATTERY_TEST": self.V1_show_battery_chart,
            "V1_RAIL_PRESSURE": self.V1_show_rail_pressure_chart,
            "V1_RAIL_GAP": self.V1_show_rail_gap_chart,
            # add more as needed
        }

        # Lookup and call the handler if it exists
        handler = dispatch.get(action_id)
        if handler:
            handler(snaptype)  # or pass whatever args your handlers need
        else:
            print(f"No handler found for action: {action_id}")

    # Helper function to apply quick chart setup
    def _apply_quick_chart_setup(self, snaptype: SnapType, action_id: str, primary_pids: List[str], primary_min: str, primary_max: str, secondary_pids: List[str]=[], secondary_min: str="", secondary_max: str=""):
        # Retrieve tooltip for the chart title
        tooltip = None
        if snaptype in BUTTONS_BY_TYPE:
            for button_name, cmd, tip in BUTTONS_BY_TYPE[snaptype]:
                if cmd == action_id:
                    tooltip = tip
                    break
        
        # Set scripted PID names for primary and secondary axes
        self.primary_series = primary_pids
        self.secondary_series = secondary_pids
        
        # Update list boxes
        self.primary_list.delete(0, tk.END)
        for pid in self.primary_series:
            self.primary_list.insert(tk.END, pid)
        
        self.secondary_list.delete(0, tk.END)
        for pid in self.secondary_series:
            self.secondary_list.insert(tk.END, pid)
        
        # Set scripted min/max values for axes
        self.primary_auto.set(False)
        self.primary_ymin.set(primary_min)
        self.primary_ymax.set(primary_max)
        
        self.secondary_auto.set(False)
        self.secondary_ymin.set(secondary_min)
        self.secondary_ymax.set(secondary_max)
        
        # Trigger toggle to update entry states
        self._toggle_primary_inputs()
        self._toggle_secondary_inputs()
        
        # Generate the chart
        self.plot_combo_chart()
        
        # Set custom title if tooltip found
        if tooltip:
            self.ax_left.set_title(tooltip)
            self.canvas.draw_idle()

    def V1_show_battery_chart(self, snaptype: SnapType):
        self._apply_quick_chart_setup(
            snaptype,
            "V1_BATTERY_TEST",
            ["P_L_Battery_raw"],
            "0",
            "18",
            ["IN_Engine_cycle_speed"],
            "-50",
            "3000"
        )
        
    def V1_show_rail_pressure_chart(self, snaptype: SnapType):
        self._apply_quick_chart_setup(
            snaptype,
            "V1_RAIL_PRESSURE",
            ["RPC_Rail_pressure_dmnd", "P_L_RAIL_PRES_RAW"],
            "-15",
            "30000",
            ["FQD_Chkd_inj_fuel_dmnd"],
            "-5",
            "300"
        )

    def V1_show_rail_gap_chart(self, snaptype: SnapType):
        self._apply_quick_chart_setup(
            snaptype,
            "V1_RAIL_GAP",
            ["RPC_Rail_pressure_error"],
            "-5000",
            "5000",
        )


#------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------- PID List Logic ---------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------

    def _populate_pid_list(self):
        self.pid_list.delete(0, tk.END)
        if self.snapshot is None:
            return
        for col in self.snapshot.columns:
            self.pid_list.insert(tk.END, col)

    def _filter_pids(self):
        term = self.search_var.get().strip().lower()
        self.pid_list.delete(0, tk.END)
        if self.snapshot is None:
            return
        cols = [c for c in self.snapshot.columns if term in c.lower()]
        for c in cols:
            self.pid_list.insert(tk.END, c)

    def _add_selected(self, target: str):
        if self.snapshot is None:
            return
        sel = [self.pid_list.get(i) for i in self.pid_list.curselection()]
        if not sel:
            return
        
        # Prevent duplicates and avoid placing Time or Frame on y-axes (they can still be used on x later)
        filtered = [s for s in sel if s not in ("Frame", "Time")]
        if not filtered:
            messagebox.showinfo("Heads up", "Select one or more PID columns (not Frame/Time).")
            return

        if target == "primary":
            for s in filtered:
                if s not in self.primary_series:
                    self.primary_series.append(s)
                    self.primary_list.insert(tk.END, s)
        else:
            for s in filtered:
                if s not in self.secondary_series:
                    self.secondary_series.append(s)
                    self.secondary_list.insert(tk.END, s)

        # Redraw chart if snapshot is loaded
        if self.snapshot is not None:
            self.plot_combo_chart()

    def _move_in_list(self, listbox: tk.Listbox, delta: int):
        idxs = list(listbox.curselection())
        if not idxs:
            return
        for idx in idxs:
            new_idx = max(0, min(listbox.size()-1, idx + delta))
            if new_idx == idx:
                continue
            text = listbox.get(idx)
            listbox.delete(idx)
            listbox.insert(new_idx, text)
            listbox.selection_set(new_idx)

        # Mirror to backing lists
        if listbox is self.primary_list:
            self.primary_series = list(listbox.get(0, tk.END))
        else:
            self.secondary_series = list(listbox.get(0, tk.END))

        # Redraw chart if snapshot is loaded
        if self.snapshot is not None:
            self.plot_combo_chart()

    def _remove_selected_from(self, which: str):
        lb = self.primary_list if which == "primary" else self.secondary_list
        sel = list(lb.curselection())
        if not sel:
            return
        for idx in reversed(sel):
            lb.delete(idx)
        if which == "primary":
            self.primary_series = list(lb.get(0, tk.END))
        else:
            self.secondary_series = list(lb.get(0, tk.END))

        # Redraw chart if snapshot is loaded
        if self.snapshot is not None:
            self.plot_combo_chart()

    def _update_controls_state(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        for w in (self.pid_list, self.primary_list, self.secondary_list):
            w.configure(state=state)

    def _toggle_primary_inputs(self):
        st = tk.DISABLED if self.primary_auto.get() else tk.NORMAL
        self.primary_min_entry.configure(state=st)
        self.primary_max_entry.configure(state=st)

    def _toggle_secondary_inputs(self):
        st = tk.DISABLED if self.secondary_auto.get() else tk.NORMAL
        self.secondary_min_entry.configure(state=st)
        self.secondary_max_entry.configure(state=st)

    def _parse_limit(self, s: str):
        s = (s or "").strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

#------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------- Plotting ---------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------

    def plot_combo_chart(self):
        if self.snapshot is None:
            messagebox.showinfo("No data", "Open a data file first.")
            return
        if not self.primary_series and not self.secondary_series:
            messagebox.showinfo("Select columns", "Add at least one series to Primary or Secondary axis.")
            return

        df = self.snapshot.copy()

        # Choose X: prefer Time if numeric, else Frame, else index
        x_key = None
        if "Time" in df.columns and pd.api.types.is_numeric_dtype(df["Time"]):
            x_key = "Time"
        elif "Frame" in df.columns and pd.api.types.is_numeric_dtype(df["Frame"]):
            x_key = "Frame"

        # Clear the entire figure and recreate axes for a clean slate
        self.figure.clear()
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()

        # Plot primary series
        if self.primary_series:
            for s in self.primary_series:
                if s in df.columns:
                    y = pd.to_numeric(df[s], errors="coerce")
                    if x_key:
                        self.ax_left.plot(df[x_key], y, label=s)
                    else:
                        self.ax_left.plot(y.index, y, label=s)
            self.ax_left.set_ylabel("Primary")
            self.ax_left.legend(loc="upper left")

        # Plot secondary series
        if self.secondary_series:
            for s in self.secondary_series:
                if s in df.columns:
                    y = pd.to_numeric(df[s], errors="coerce")
                    if x_key:
                        self.ax_right.plot(df[x_key], y, label=s, linestyle='--')
                    else:
                        self.ax_right.plot(y.index, y, label=s, linestyle='--')
            self.ax_right.set_ylabel("Secondary")
            self.ax_right.legend(loc="upper right")

        # Apply axis limits if user entered them
        try:
            if self.primary_min.get():
                self.ax_left.set_ylim(bottom=float(self.primary_min.get()))
            if self.primary_max.get():
                self.ax_left.set_ylim(top=float(self.primary_max.get()))
        except ValueError:
            pass
        try:
            if self.secondary_min.get():
                self.ax_right.set_ylim(bottom=float(self.secondary_min.get()))
            if self.secondary_max.get():
                self.ax_right.set_ylim(top=float(self.secondary_max.get()))
        except ValueError:
            pass

        # Labels and grid
        self.ax_left.set_title("Combo Line Chart")
        self.ax_left.set_xlabel(x_key if x_key else "Index")
        self.ax_left.grid(True, linestyle=":", linewidth=0.6)

        # Apply axis limits if provided
        if not self.primary_auto.get():
            ymin = self._parse_limit(self.primary_ymin.get())
            ymax = self._parse_limit(self.primary_ymax.get())
            if ymin is not None or ymax is not None:
                self.ax_left.set_ylim(bottom=ymin if ymin is not None else None,
                              top=ymax if ymax is not None else None)

        if not self.secondary_auto.get():
            ymin = self._parse_limit(self.secondary_ymin.get())
            ymax = self._parse_limit(self.secondary_ymax.get())
            if ymin is not None or ymax is not None:
                self.ax_right.set_ylim(bottom=ymin if ymin is not None else None,
                               top=ymax if ymax is not None else None)

        self.figure.tight_layout()
        self.canvas.draw_idle()

#------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------ Build a new window with a clean data table ---------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------

    def open_data_table(self, snapshot: pd.DataFrame):
        if snapshot is None or snapshot.empty:
            messagebox.showinfo("No data", "Open a file first so I can show the cleaned table.")
            return

        # # Reuse an existing table window if it's open
        # if hasattr(self, "_table_win") and self._table_win and tk.Toplevel.winfo_exists(self._table_win):
        #     try:
        #         self._table_win.lift()
        #         self._table_win.focus_force()
        #     except Exception:
        #         pass
        #     return

        win = tk.Toplevel(self)
        self._table_win = win
        win.title(f"Validation — Cleaned Data Table: {self.snapshot_path}")
        win.geometry("1000x600")

        # Style to make headings bold
        style = ttk.Style(win)
        style.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))

        container = ttk.Frame(win)
        container.pack(fill=tk.BOTH, expand=True)

        # ---- Sanitize column names for Treeview ----
        raw_cols = list(snapshot.columns)
        safe_cols = []
        used = set()
        for i, c in enumerate(raw_cols):
            name = str(c).strip()
            if not name or name.lower() == "nan":
                name = f"col_{i+1}"
            base = name
            k = 1
            while name in used:
                k += 1
                name = f"{base}_{k}"
            used.add(name)
            safe_cols.append(name)

        # Use a display copy with safe column names
        df_display = snapshot.copy()
        df_display.columns = safe_cols

        # Scrollbars
        xscroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL)
        yscroll = ttk.Scrollbar(container, orient=tk.VERTICAL)

        tree = ttk.Treeview(
            container,
            columns=safe_cols,     # must be a list of strings
            show="headings",       # hide the #0 column
            xscrollcommand=xscroll.set,
            yscrollcommand=yscroll.set,
            height=24
        )
        xscroll.config(command=tree.xview)
        yscroll.config(command=tree.yview)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Headings + widths
        for col in safe_cols:
            tree.heading(col, text=col, anchor='center')
            # width heuristic: 150px min, 300px max, based on ~80th percentile of text length
            try:
                w = max(150, min(300, int(df_display[col].astype(str).map(len).quantile(0.8)) * 8))
            except Exception:
                w = 120
                # I disabled stretch to prevent columns from getting slammed
            tree.column(col, width=w, stretch=False, minwidth=w, anchor='center')

        # Insert rows (convert cells to strings; empty for NaN)
        for _, row in df_display.iterrows():
            values = [(("" if pd.isna(v) else v)) for v in row.tolist()]
            values = [str(v) for v in values]
            tree.insert("", tk.END, values=values)

        def _on_close():
            try:
                self._table_win = None
            finally:
                win.destroy()
        win.protocol("WM_DELETE_WINDOW", _on_close)

#------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------- Open PID Info Window -------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------

    def show_pid_info(self):
        """Display PID info in a new Treeview window with 3 columns."""
        if not self.pid_info:
            tk.messagebox.showinfo("PID Descriptions", "No PID information available.")
            return

        window = tk.Toplevel(self)
        window.attributes("-topmost", True)
        window.title(f"PID Descriptions: {self.snapshot_path}" )
        window.geometry("800x400")

        # Style to make headings bold
        style = ttk.Style(window)
        style.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))

        # Container for tree and scrollbar
        container = ttk.Frame(window)
        container.pack(fill=tk.BOTH, expand=True)

        # Vertical scrollbar
        yscroll = ttk.Scrollbar(container, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Define the columns
        columns = ("PID", "Description", "Unit")

        tree = ttk.Treeview(container, columns=columns, show="headings", yscrollcommand=yscroll.set)
        yscroll.config(command=tree.yview)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Define headings
        tree.heading("PID", text="PID Name")
        tree.heading("Description", text="Description")
        tree.heading("Unit", text="Unit")

        # Optional: set column widths and alignment
        tree.column("PID", width=180, anchor="w")
        tree.column("Description", width=480, anchor="w")
        tree.column("Unit", width=90, anchor="w")

        # Insert rows from your dictionary
        for pid, data in self.pid_info.items():
            tree.insert(
                "",
                "end",
                values=(
                    pid,
                    data.get("Description", ""),
                    data.get("Unit", "")
                )
            )





