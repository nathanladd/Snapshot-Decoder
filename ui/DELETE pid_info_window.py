import tkinter as tk
from tkinter import ttk


class PidInfoWindow:
    def __init__(self, parent, pid_info, snapshot_path, main_app):
        self.parent = parent
        self.pid_info = pid_info
        self.snapshot_path = snapshot_path
        self.main_app = main_app

        self.window = tk.Toplevel(parent)
        self.window.attributes("-topmost", True)
        self.window.title(f"PID Descriptions: {snapshot_path}")
        self.window.geometry("800x400")

        # Style to make headings bold
        style = ttk.Style(self.window)
        style.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))

        # Search box at the top
        search_frame = ttk.Frame(self.window)
        search_frame.pack(fill=tk.X, padx=10, pady=(10,0))
        ttk.Label(search_frame, text="Search Descriptions:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))
        search_entry.bind("<KeyRelease>", self._filter_descriptions)

        # Container for tree and scrollbar
        container = ttk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Vertical scrollbar
        yscroll = ttk.Scrollbar(container, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Define the columns
        columns = ("PID", "Description", "Unit")

        self.tree = ttk.Treeview(container, columns=columns, show="headings", yscrollcommand=yscroll.set)
        yscroll.config(command=self.tree.yview)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Define headings
        self.tree.heading("PID", text="PID Name")
        self.tree.heading("Description", text="Description")
        self.tree.heading("Unit", text="Unit")

        # Optional: set column widths and alignment
        self.tree.column("PID", width=180, anchor="w")
        self.tree.column("Description", width=480, anchor="w")
        self.tree.column("Unit", width=90, anchor="w")

        # Bind double-click
        self.tree.bind("<Double-1>", self._on_double_click)

        # Populate tree
        self._populate_tree()

    def _populate_tree(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert all
        for pid, data in self.pid_info.items():
            self.tree.insert(
                "",
                "end",
                values=(
                    pid,
                    data.get("Description", ""),
                    data.get("Unit", "")
                )
            )

    def _filter_descriptions(self, event=None):
        term = self.search_var.get().strip().lower()
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Filter and insert
        for pid, data in self.pid_info.items():
            desc = data.get("Description", "").lower()
            if term in desc:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        pid,
                        data.get("Description", ""),
                        data.get("Unit", "")
                    )
                )

    def _on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        pid = self.tree.item(item, "values")[0]
        self.click_x = event.x_root
        self.click_y = event.y_root
        self._show_choice_dialog(pid)

    def _show_choice_dialog(self, pid):
        choice_win = tk.Toplevel(self.window)
        choice_win.title("Choose Axis")
        choice_win.geometry("300x100")
        choice_win.geometry(f"+{self.click_x + 10}+{self.click_y + 10}")
        choice_win.attributes("-topmost", True)
        choice_win.grab_set()  # Make modal
        ttk.Label(choice_win, text=f"Add '{pid}' to which axis?").pack(pady=10)

        def add_to_primary():
            if pid not in self.main_app.primary_series:
                self.main_app.primary_series.append(pid)
                self.main_app.primary_list.insert(tk.END, pid)
                if self.main_app.engine is not None:
                    self.main_app.plot_combo_chart()
            choice_win.destroy()

        def add_to_secondary():
            if pid not in self.main_app.secondary_series:
                self.main_app.secondary_series.append(pid)
                self.main_app.secondary_list.insert(tk.END, pid)
                if self.main_app.engine is not None:
                    self.main_app.plot_combo_chart()
            choice_win.destroy()

        btn_frame = ttk.Frame(choice_win)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Primary", command=add_to_primary).pack(side=tk.LEFT, padx=20)
        ttk.Button(btn_frame, text="Secondary", command=add_to_secondary).pack(side=tk.RIGHT, padx=20)
