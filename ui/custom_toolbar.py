# Custom matplotlib toolbar for tkinter
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.backends.backend_pdf import PdfPages
from tkinter import filedialog
import os
import matplotlib.image as mpimg


class CustomNavigationToolbar(NavigationToolbar2Tk):
    """Custom navigation toolbar that saves charts as PDF with metadata."""

    def __init__(self, canvas, window, *, pack_toolbar=True, chart_config=None):
        self.chart_config = chart_config
        super().__init__(canvas, window, pack_toolbar=pack_toolbar)

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
            
            # Add logo to top right
            logo_path = "logo.png"
            if os.path.exists(logo_path):
                try:
                    logo = mpimg.imread(logo_path)
                    # Create a small axes for the logo in the top right
                    logo_ax = fig.add_axes([0.85, 0.92, 0.12, 0.06])  # [left, bottom, width, height]
                    logo_ax.imshow(logo)
                    logo_ax.axis('off')
                except Exception:
                    pass  # If logo fails to load, continue without it
            
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
            
            # Adjust layout to prevent overlapping
            fig.tight_layout(rect=[0, 0.01, 1, 0.96])
            
            # Save to PDF
            pdf.savefig(fig, dpi=150)
            
            # Remove the metadata text and logo after saving
            if self.chart_config and metadata_parts:
                # Remove the last added text (metadata)
                fig.texts[-1].remove()
            
            # Remove logo axes if it was added
            if os.path.exists("logo.png"):
                try:
                    # Find and remove the logo axes
                    for ax in fig.axes:
                        if not ax.get_xlabel() and not ax.get_ylabel() and not ax.get_visible():
                            continue
                        # Check if this is the logo axes (has no labels and is small)
                        bbox = ax.get_position()
                        if bbox.width < 0.2 and bbox.height < 0.1:
                            fig.delaxes(ax)
                            break
                except Exception:
                    pass
            
            fig.tight_layout()
            self.canvas.draw()
