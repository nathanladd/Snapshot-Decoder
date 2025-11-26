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

# Only lightweight imports here - heavy imports happen AFTER splash is shown
import os
import sys
import tkinter as tk

from version import APP_VERSION

# This code checks if the script is running from a PyInstaller-packaged executable. 
# sys._MEIPASS is an attribute PyInstaller sets to the temporary directory containing 
# bundled files. If it exists, the function uses that as the base path for resources; 
# otherwise, it falls back to the current working directory. This ensures resource paths
# work in both development and bundled environments.
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# This function creates and displays a splash screen styled like the About window.
def show_splash():
    """
    Create and display a splash screen styled like the About window.
    Returns the splash window so it can be destroyed after loading.
    """
    splash = tk.Tk()
    splash.overrideredirect(True)  # Remove title bar
    
    bg_color = "#dcd5bf"  # Matches splash.png background
    splash.configure(bg=bg_color)
    
    # Window size matching About window
    window_width = 650
    window_height = 750
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    splash.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Make sure it appears on top
    splash.lift()
    splash.attributes('-topmost', True)
    
    # Load splash image
    try:
        img_path = resource_path("splash.png")
        if os.path.exists(img_path):
            splash_img = tk.PhotoImage(file=img_path)
            
            # Auto-scale down if too wide for the window
            target_width = window_width - 50
            if splash_img.width() > target_width:
                scale_factor = (splash_img.width() // target_width) + 1
                splash_img = splash_img.subsample(scale_factor)
            
            img_label = tk.Label(splash, image=splash_img, bg=bg_color)
            img_label.image = splash_img  # Keep reference
            img_label.pack(pady=(20, 10))
    except Exception as e:
        print(f"Error loading splash image: {e}")
    
    # Loading message
    loading_label = tk.Label(
        splash, 
        text=f"Snapshot Decoder {APP_VERSION}\n\nLoading...", 
        font=("Segoe UI", 14), 
        bg=bg_color, 
        anchor="center"
    )
    loading_label.pack(expand=True, pady=10)
    
    # Store reference to update text later
    splash.loading_label = loading_label
    
    # Force the window to render
    splash.update()
    
    return splash


def main():
    """Main entry point for the application"""
    # Phase 1: Show splash screen BEFORE heavy imports
    splash = show_splash()
    
    # Phase 2: Import heavy modules (splash is visible during this)
    splash.loading_label.config(text=f"Snapshot Decoder {APP_VERSION}\n\nLoading libraries...")
    splash.update()
    
    from ui.app import SnapshotDecoderApp
    
    # Phase 3: Destroy splash, create and run main app
    splash.destroy()
    
    app = SnapshotDecoderApp()
    app.mainloop()

# This dunder method checks if the script is being run as the 
# main program (not imported as a module)
if __name__ == "__main__":
    main()