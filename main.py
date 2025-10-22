"""
Snapshot Reader — Column Selector & Combo Chart (Tkinter)
--------------------------------------------------------
Adds a UI panel that lists all column headers from the loaded dataset and lets
users choose one or more series for a combo *line* chart with dual y-axes.

Key bits:
- File ▶ Open loads an .xlsx and auto-detects the header row using the project rule:
  • Col 1 must be "Frame" and col 2 "Time".
  • Starting around row 3, find the row that contains "P_L_Battery_raw" and
    set that row as the header for the whole table.
  • Start the data where Frame == 0.
- Left panel shows all columns in a searchable, multi-select list.
- Buttons add selections to Primary or Secondary axis buckets (you can add multiple).
- Plot ▶ Combo Line Chart draws all Primary on left axis and Secondary on right axis.
- Embeds Matplotlib figure inside Tkinter.


Note on old .xls files:
  xlrd >= 2.0 dropped support for .xls. This app will politely instruct users to
  open the .xls in Excel and “Save As” .xlsx, then try again.
"""

from ui.app import SnapshotReaderApp

def main():
    app = SnapshotReaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()