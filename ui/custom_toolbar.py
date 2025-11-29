# Custom matplotlib toolbar for tkinter
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.backends.backend_pdf import PdfPages
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
import os

from version import APP_VERSION


class CustomNavigationToolbar(NavigationToolbar2Tk):
    """Custom navigation toolbar that saves charts as PDF with metadata."""

    def __init__(self, canvas, window, *, pack_toolbar=True, chart_config=None,
                 cursor_var=None, values_var=None):
        self.chart_config = chart_config
        self._cursor_var = cursor_var
        self._values_var = values_var
        super().__init__(canvas, window, pack_toolbar=pack_toolbar)
        
        # Add toggle buttons for cursor and values after toolbar is built
        if self._cursor_var is not None or self._values_var is not None:
            # Create style for larger font checkbuttons
            style = ttk.Style()
            style.configure("Toolbar.TCheckbutton", font=("TkDefaultFont", 14))
            
            # Add a separator
            sep = ttk.Separator(self, orient=tk.VERTICAL)
            sep.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=2)
        if self._cursor_var is not None:
            cb_cursor = ttk.Checkbutton(self, text="│", variable=self._cursor_var, style="Toolbar.TCheckbutton")
            cb_cursor.pack(side=tk.LEFT, padx=2)
        if self._values_var is not None:
            cb_values = ttk.Checkbutton(self, text="#", variable=self._values_var, style="Toolbar.TCheckbutton")
            cb_values.pack(side=tk.LEFT, padx=2)

    # Override toolitems to exclude the Subplots button
    toolitems = [
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        (None, None, None, None),  # separator
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        (None, None, None, None),  # separator
        ('Save', 'Save chart as PDF', 'filesave', 'save_figure'),
    ]
    
    def save_figure(self, *args):
        """Override save_figure to save as PDF with metadata."""
        # Get default filename from chart config if available
        default_name = "chart.pdf"
        if self.chart_config and self.chart_config.file_name:
            base_name = os.path.splitext(self.chart_config.file_name)[0]
            chart_title = self.chart_config.title.replace(" ", "_").replace("/", "-")
            default_name = f"{base_name}_{chart_title}.pdf"
        
        # Ask user for save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Save Chart as PDF"
        )
        
        if not filepath:
            return  # User cancelled
        
        # Save as PDF with metadata
        with PdfPages(filepath) as pdf:
            # Get the current figure
            fig = self.canvas.figure
                        
            # Add chain of custody metadata at the top if available
            if self.chart_config:
                metadata_parts = []
                if self.chart_config.file_name:
                    metadata_parts.append(f"File: {self.chart_config.file_name}")
                if self.chart_config.date_time:
                    metadata_parts.append(f"Date/Time: {self.chart_config.date_time}")
                if self.chart_config.engine_hours is not None and self.chart_config.engine_hours > 0:
                    metadata_parts.append(f"Engine Hours: {self.chart_config.engine_hours}")
                
                if metadata_parts:
                    metadata_text = "  |  ".join(metadata_parts)
                    fig.text(0.5, 0.98, metadata_text, 
                            ha='center', va='top', fontsize=8, color='gray', style='italic',
                            transform=fig.transFigure)
            
            # Add watermark
            watermark = fig.text(0.99, 0.01, f'Snapshot Decoder {APP_VERSION}', 
                    ha='right', va='bottom', fontsize=10, color='lightgray', alpha=0.7,
                    transform=fig.transFigure)
            
            # Adjust layout to prevent overlapping
            fig.tight_layout(rect=[0, 0.01, 1, 0.96])
            
            # Save to PDF
            pdf.savefig(fig, dpi=150)
            
            # Remove the temporary text elements after saving
            if self.chart_config and metadata_parts:
                fig.texts[-1].remove()  # Remove watermark
                fig.texts[-1].remove()  # Remove metadata
            else:
                watermark.remove()
            
            fig.tight_layout()
            self.canvas.draw()
