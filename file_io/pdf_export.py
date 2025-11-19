"""
PDF Export for Chart Cart

Exports all charts from the cart to a multi-page PDF document.
"""

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from ui.chart_renderer import ChartRenderer
from typing import List
from domain.chart_config import ChartConfig
from domain.constants import PDF_LOGO_POSITION, PDF_LOGO_ALPHA
import matplotlib.image as mpimg
import os
import sys


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    # Check if running as PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ChartCartPdfExporter:
    """Exports chart cart contents to a multi-page PDF document."""
    
    def __init__(self, configs: List[ChartConfig]):
        """
        Initialize the PDF exporter.
        
        Args:
            configs: List of ChartConfig objects from the chart cart
        """
        self.configs = configs
    
    def export(self, filepath: str, page_size: tuple = (11, 8.5), dpi: int = 150):
        """
        Export all charts to a PDF file, one chart per page.
        
        Args:
            filepath: Path to save the PDF file
            page_size: Page size in inches (width, height). Default is landscape letter size.
            dpi: Resolution for the PDF. Default is 150.
        """
        if not self.configs:
            raise ValueError("No charts to export. Chart cart is empty.")
        
        with PdfPages(filepath) as pdf:
            for i, config in enumerate(self.configs, start=1):
                # Create a new figure for each chart
                fig = Figure(figsize=page_size, dpi=dpi)
                
                # Create axes based on whether we have secondary axis
                ax_left = fig.add_subplot(111)
                ax_right = None
                if config.secondary_axis.series:
                    ax_right = ax_left.twinx()
                
                # Render the chart
                renderer = ChartRenderer(config)
                
                # Render based on chart type
                if config.chart_type == "line":
                    renderer._render_line_chart(ax_left, ax_right, config.data)
                elif config.chart_type == "bar":
                    renderer._render_bar_chart(ax_left, ax_right, config.data)
                elif config.chart_type == "bubble":
                    renderer._render_bubble_chart(ax_left, ax_right, config.data)
                
                # Apply formatting (axis labels, limits, grid, legends)
                renderer._apply_formatting(ax_left, ax_right)
                
                # Set the chart title
                ax_left.set_title(config.title, fontsize=14, fontweight='bold', pad=15)
                
                # Add logo to top right on first page only
                if i == 1:
                    logo_path = resource_path("logo.png")
                    if os.path.exists(logo_path):
                        try:
                            logo = mpimg.imread(logo_path)
                            # Create a small axes for the logo in the top right
                            logo_ax = fig.add_axes(PDF_LOGO_POSITION)  # [left, bottom, width, height]
                            logo_ax.imshow(logo, alpha=PDF_LOGO_ALPHA) # alpha controls transparency
                            logo_ax.axis('off')
                        except Exception:
                            pass  # If logo fails to load, continue without it
                
                # Add chain of custody metadata at the top
                metadata_parts = []
                if config.file_name:
                    metadata_parts.append(f"File: {config.file_name}")
                if config.date_time:
                    metadata_parts.append(f"Date/Time: {config.date_time}")
                if config.engine_hours is not None and config.engine_hours > 0:
                    metadata_parts.append(f"Engine Hours: {config.engine_hours}")
                
                if metadata_parts:
                    metadata_text = "  |  ".join(metadata_parts)
                    fig.text(0.5, 0.98, metadata_text, 
                            ha='center', va='top', fontsize=8, color='gray', style='italic')
                
                # Add page number at the bottom
                fig.text(0.5, 0.02, f'Page {i} of {len(self.configs)}', 
                        ha='center', va='bottom', fontsize=8, color='gray')
                
                # Adjust layout to prevent overlapping
                fig.tight_layout(rect=[0, 0.03, 1, 0.96])  # Leave space for page number, title, and metadata
                
                # Save the figure to the PDF
                pdf.savefig(fig, dpi=dpi)
                
                # Close the figure to free memory
                fig.clf()
                del fig
    
    def export_with_metadata(self, filepath: str, metadata: dict = None, **kwargs):
        """
        Export charts to PDF with custom metadata.
        
        Args:
            filepath: Path to save the PDF file
            metadata: Dictionary with PDF metadata (Title, Author, Subject, Keywords, Creator)
            **kwargs: Additional arguments passed to export()
        """
        if not self.configs:
            raise ValueError("No charts to export. Chart cart is empty.")
        
        with PdfPages(filepath, metadata=metadata) as pdf:
            # Use the same export logic
            for i, config in enumerate(self.configs, start=1):
                fig = Figure(figsize=kwargs.get('page_size', (11, 8.5)), 
                           dpi=kwargs.get('dpi', 150))
                
                ax_left = fig.add_subplot(111)
                ax_right = None
                if config.secondary_axis.series:
                    ax_right = ax_left.twinx()
                
                renderer = ChartRenderer(config)
                
                if config.chart_type == "line":
                    renderer._render_line_chart(ax_left, ax_right, config.data)
                elif config.chart_type == "bar":
                    renderer._render_bar_chart(ax_left, ax_right, config.data)
                elif config.chart_type == "bubble":
                    renderer._render_bubble_chart(ax_left, ax_right, config.data)
                
                renderer._apply_formatting(ax_left, ax_right)
                ax_left.set_title(config.title, fontsize=14, fontweight='bold', pad=15)
                
                # Add logo to top right on first page only
                if i == 1:
                    logo_path = resource_path("logo.png")
                    if os.path.exists(logo_path):
                        try:
                            logo = mpimg.imread(logo_path)
                            # Create a small axes for the logo in the top right
                            logo_ax = fig.add_axes(PDF_LOGO_POSITION)  # [left, bottom, width, height]
                            logo_ax.imshow(logo, alpha=PDF_LOGO_ALPHA) # alpha controls transparency
                            logo_ax.axis('off')
                        except Exception:
                            pass  # If logo fails to load, continue without it
                
                # Add chain of custody metadata at the top
                metadata_parts = []
                if config.file_name:
                    metadata_parts.append(f"File: {config.file_name}")
                if config.date_time:
                    metadata_parts.append(f"Date/Time: {config.date_time}")
                if config.engine_hours is not None and config.engine_hours > 0:
                    metadata_parts.append(f"Engine Hours: {config.engine_hours}")
                
                if metadata_parts:
                    metadata_text = "  |  ".join(metadata_parts)
                    fig.text(0.5, 0.98, metadata_text, 
                            ha='center', va='top', fontsize=8, color='gray', style='italic')
                
                fig.text(0.5, 0.02, f'Page {i} of {len(self.configs)}', 
                        ha='center', va='bottom', fontsize=8, color='gray')
                fig.tight_layout(rect=[0, 0.03, 1, 0.96])
                
                pdf.savefig(fig, dpi=kwargs.get('dpi', 150))
                fig.clf()
                del fig
