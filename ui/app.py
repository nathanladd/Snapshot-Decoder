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
from ui.pid_info_window import PidInfoWindow
from ui.data_table_window import DataTableWindow
from domain.quick_charts import V1_show_battery_chart, V1_show_rail_pressure_chart, V1_show_rail_gap_chart

# Chart rendering
from domain.chart_config import ChartConfig, AxisConfig
from ui.chart_renderer import ChartRenderer





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
        view_menu.add_command(label="Raw Data...", command=lambda: self.open_data_table(self.raw_snapshot, "Raw Data"))
        view_menu.add_command(label="Clean Table...", command=lambda: self.open_data_table(self.snapshot, "Snapshot Table"))
        view_menu.add_command(label="PID Descriptions...", command=self.show_pid_info)
        menubar.add_cascade(label="Data", menu=view_menu)

        plot_menu = tk.Menu(menubar, tearoff=0)
        plot_menu.add_command(label="Plot Selected PIDs", command=self.plot_combo_chart)
        plot_menu.add_command(label="Chart Table", command=self.open_chart_table)
        plot_menu.add_command(label="Clear Chart", command=self.clear_chart)
        menubar.add_cascade(label="Chart", menu=plot_menu)

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

        # Chart border - use classic theme for visible sash
        style = ttk.Style()
        style.theme_use("classic")
        
        chart_border = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        chart_border.pack(side="right", fill="both", expand=True, padx=4, pady=4)

        # Left pane: Chart canvas area
        chart_pane = ttk.Frame(chart_border)
        chart_border.add(chart_pane, weight=1)

        # Right pane: Chart Cart
        cart_pane = ttk.Frame(chart_border)
        chart_border.add(cart_pane, weight=1)

        # Snapshot Header Information
        self.header_panel = HeaderPanel(header_border, on_action=self.handle_header_action)
        self.header_panel.pack(fill="x", expand=True, padx=4, pady=4) 

        # Configure the style for larger font
        style = ttk.Style()
        style.configure("Book.TButton", font=("Helvetica", 22), padding=0, relief="flat", anchor="s")
        
        # Configure left_border to use grid layout for better control over shrinking
        left_border.columnconfigure(0, weight=1)
        left_border.rowconfigure(2, weight=1)  # PID listbox row gets all the shrinking weight

        # Search box label and button - row 0
        search_label_frame = ttk.Frame(left_border)
        search_label_frame.grid(row=0, column=0, sticky="ew", pady=(0,0), padx=(8,8))
        ttk.Label(search_label_frame, text="Search PIDs", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        book_btn = ttk.Button(search_label_frame, text="📖", width=0, style="Book.TButton", command=self.show_pid_info)
        book_btn.pack(side=tk.RIGHT)

        # Chart Cart in right pane
        ttk.Label(cart_pane, text="Chart Cart", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # Search box - row 1
        search_frame = ttk.Frame(left_border)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8), padx=(8,8))
        self.search_var = tk.StringVar()
        search = ttk.Entry(search_frame, textvariable=self.search_var)
        search.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search.bind("<KeyRelease>", lambda e: self._filter_pids())

        # All PID Names listbox (multi-select) - row 2 (gets all shrinking priority)
        pid_list_frame = ttk.Frame(left_border)
        pid_list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        self.pid_list = tk.Listbox(pid_list_frame, selectmode=tk.EXTENDED, exportselection=False, height=22, width=43)
        self.pid_list.pack(fill=tk.BOTH, expand=True)

        # Buttons to add to primary/secondary - row 3
        btns = ttk.Frame(left_border)
        btns.grid(row=3, column=0, sticky="ew", pady=8)
        ttk.Button(btns, text="➕ Add to Primary", command=lambda: self._add_selected(target="primary")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))
        ttk.Button(btns, text="➕ Add to Secondary", command=lambda: self._add_selected(target="secondary")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4,0))

        # Buckets display - row 4
        buckets = ttk.Frame(left_border)
        buckets.grid(row=4, column=0, sticky="ew")

        # Primary frame with min/max
        primary_frame = ttk.Labelframe(buckets, text="Primary axis (left)")
        primary_frame.pack(fill=tk.BOTH, expand=True, pady=(4,6))
        self.primary_list = tk.Listbox(primary_frame, height=1, exportselection=False)  # Reduced to 1 for minimal space
        self.primary_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pf_controls = ttk.Frame(primary_frame)
        pf_controls.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(pf_controls, text="▲", width=3, command=lambda: self._move_in_list(self.primary_list, -1)).pack(pady=2)
        ttk.Button(pf_controls, text="▼", width=3, command=lambda: self._move_in_list(self.primary_list, +1)).pack(pady=2)
        ttk.Button(pf_controls, text="🗑", width=3, command=lambda: self._remove_selected_from("primary")).pack(pady=2)

        # Secondary frame with min/max
        secondary_frame = ttk.Labelframe(buckets, text="Secondary axis (right)")
        secondary_frame.pack(fill=tk.BOTH, expand=True)
        self.secondary_list = tk.Listbox(secondary_frame, height=1, exportselection=False)  # Reduced to 1 for minimal space
        self.secondary_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sf_btns = ttk.Frame(secondary_frame)
        sf_btns.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(sf_btns, text="▲", width=3, command=lambda: self._move_in_list(self.secondary_list, -1)).pack(pady=2)
        ttk.Button(sf_btns, text="▼", width=3, command=lambda: self._move_in_list(self.secondary_list, +1)).pack(pady=2)
        ttk.Button(sf_btns, text="🗑", width=3, command=lambda: self._remove_selected_from("secondary")).pack(pady=2)

        # Axis controls - row 5
        axis = ttk.Labelframe(left_border, text="Axis ranges (optional)")
        axis.grid(row=5, column=0, sticky="ew", pady=(8,6))

        # Plot and clear buttons - row 6
        plot_btns = ttk.Frame(left_border)
        plot_btns.grid(row=6, column=0, sticky="ew", pady=(0,8))
        ttk.Button(plot_btns, text="Plot Chart", command=self.plot_combo_chart).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        ttk.Button(plot_btns, text="Chart Table", command=self.open_chart_table).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,2))
        ttk.Button(plot_btns, text="Clear Chart", command=self.clear_chart).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))

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

        # Chart canvas in left pane
        self.right = ttk.Frame(chart_pane, padding=10)
        self.right.pack(fill=tk.BOTH, expand=True)

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
        self.ax_left.set_xlabel("Frame / Time")
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

#-----------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------- Data Loading -------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------
    
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
        header_info = parse_header(self.raw_snapshot, max_rows=5)
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
            "V1_BATTERY_TEST": V1_show_battery_chart,
            "V1_RAIL_PRESSURE": V1_show_rail_pressure_chart,
            "V1_RAIL_GAP": V1_show_rail_gap_chart,
            # add more as needed
        }

        # Lookup and call the handler if it exists
        handler = dispatch.get(action_id)
        if handler:
            handler(self, snaptype)  # pass self as main_app
        else:
            print(f"No handler found for action: {action_id}")

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
        """Plot chart using the ChartRenderer class."""
        if self.snapshot is None:
            messagebox.showinfo("No data", "Open a data file first.")
            return
        if not self.primary_series and not self.secondary_series:
            messagebox.showinfo("Select columns", "Add at least one series to Primary or Secondary axis.")
            return

        # Configure primary axis
        primary_axis = AxisConfig(
            series=list(self.primary_series),
            auto_scale=self.primary_auto.get(),
            min_value=self._parse_limit(self.primary_ymin.get()),
            max_value=self._parse_limit(self.primary_ymax.get())
        )

        # Configure secondary axis
        secondary_axis = AxisConfig(
            series=list(self.secondary_series),
            auto_scale=self.secondary_auto.get(),
            min_value=self._parse_limit(self.secondary_ymin.get()),
            max_value=self._parse_limit(self.secondary_ymax.get())
        )

        # Create chart configuration
        config = ChartConfig(
            data=self.snapshot.copy(),
            chart_type="line",
            primary_axis=primary_axis,
            secondary_axis=secondary_axis,
            title="Custom Line Chart",
            pid_info=self.pid_info
        )

        # Render the chart
        try:
            renderer = ChartRenderer(config)
            self.ax_left, self.ax_right = renderer.render(self.figure, self.canvas)
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to render chart: {str(e)}")

    def open_chart_table(self):
        if self.snapshot is None or self.snapshot.empty:
            messagebox.showinfo("No data", "Open a file first so I can show the chart table.")
            return
        # Check if Chart Table is already open
        if hasattr(self, 'chart_table_window') and self.chart_table_window and self.chart_table_window.winfo_exists():
            self.chart_table_window.lift()
            return
        # Union of primary and secondary (no duplicates, preserve order)
        selected = list(dict.fromkeys(list(self.primary_series) + list(self.secondary_series)))
        if not selected:
            messagebox.showinfo("No selection", "Add PIDs to Primary or Secondary axis first.")
            return
        existing = [c for c in selected if c in self.snapshot.columns]
        if not existing:
            messagebox.showinfo("No selection", "Selected PIDs not found in data.")
            return
        if "Time" in self.snapshot.columns:
            columns = ["Time"] + [c for c in existing if c != "Time"]
        else:
            columns = existing
        df = self.snapshot[columns].copy()
        win = DataTableWindow(self, df, self.snapshot_path, "Chart Table")
        self.chart_table_window = win.win

    def clear_chart(self):
        # Clear selected series and listboxes
        self.primary_series = []
        self.secondary_series = []
        try:
            self.primary_list.delete(0, tk.END)
            self.secondary_list.delete(0, tk.END)
        except Exception:
            pass

        # Reset axis auto toggles and range entries
        self.primary_auto.set(True)
        self.secondary_auto.set(True)
        try:
            self._toggle_primary_inputs()
            self._toggle_secondary_inputs()
        except Exception:
            pass

        # Clear any manual limits
        try:
            self.primary_ymin.set("")
            self.primary_ymax.set("")
            self.secondary_ymin.set("")
            self.secondary_ymax.set("")
        except Exception:
            pass
        try:
            self.primary_min.set("")
            self.primary_max.set("")
            self.secondary_min.set("")
            self.secondary_max.set("")
        except Exception:
            pass

        # Clear and rebuild the axes
        self.figure.clear()
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()
        self.ax_left.set_title("Custom Line Chart")
        self.ax_left.set_xlabel("Index / Time")
        self.ax_left.set_ylabel("Primary")
        self.ax_right.set_ylabel("Secondary")
        self.figure.tight_layout()
        self.canvas.draw_idle()

#------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------ Build a new window with a data table ---------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------

    def open_data_table(self, snapshot: pd.DataFrame, window_name: str):
        if snapshot is None or snapshot.empty:
            messagebox.showinfo("No data", "Open a file first so I can show the cleaned table.")
            return

        DataTableWindow(self, snapshot, self.snapshot_path, window_name)

#------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------- Open PID Info Window -------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------

    def show_pid_info(self):
        """Display PID info in a new PidInfoWindow."""
        if not self.pid_info:
            tk.messagebox.showinfo("PID Descriptions", "No PID information available.")
            return

        PidInfoWindow(self, self.pid_info, self.snapshot_path, self)

