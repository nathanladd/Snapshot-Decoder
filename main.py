"""
Snapshot Decoder — Open various snapshot files (Excel, CSV, etc.) and plot data (Tkinter)
--------------------------------------------------------
Adds a UI panel that lists all column headers from the loaded dataset and lets
users choose one or more series for a combo *line* chart with dual y-axes.

Key bits:
- File ▶ Open loads an .xlsx or .xlsand auto-detects the header information
- The Snapshot is then parsed:
  • Header row is identified.
  • PID descriptions and units are extracted.
  • PID Frames are parsed.
- Left panel shows all columns in a searchable, multi-select list.
- Buttons add selections to Primary or Secondary axis buckets (you can add multiple).
- Plot ▶ Combo Line Chart draws all Primary on left axis and Secondary on right axis.
- Embeds Matplotlib figure inside Tkinter.
"""

# Main entry point
from ui.app import SnapshotDecoderApp

# The apps 'main' function definition
# Common convenion for the app starting point
def main():
    """Main entry point for the application"""
    # Create the main application window
    app = SnapshotDecoderApp()
    # Run the application -
    # In a GUI app, the window needs to stay open and respond to user actions 
    # (e.g., clicking buttons, typing in fields). mainloop() keeps the app running 
    # indefinitely until the user closes the window.
    app.mainloop()

if __name__ == "__main__":
  # If this file is run as the main program, call the main function
  # __name__ is a special variable in Python that is set to "__main__" 
  # when the script is run as the main program
  # and to the name of the module when it is imported as a module in another program
  # This is a common convention in Python for the app starting point
    main()