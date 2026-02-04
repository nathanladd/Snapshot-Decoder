"""
Custom matplotlib toolbar for PySide6.

Provides PDF export with chain of custody metadata.
"""

import os
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Signal

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.backends.backend_pdf import PdfPages

from domain.chart_config import ChartConfig
from version import APP_VERSION


class CustomNavigationToolbar(NavigationToolbar2QT):
    """Custom navigation toolbar that saves charts as PDF with metadata."""
    
    # Signal emitted when chart is added to cart
    add_to_cart_requested = Signal()
    
    # Signal emitted when pop-out is requested
    pop_out_requested = Signal()
    
    def __init__(self, canvas, parent, *, coordinates=True, chart_config: Optional[ChartConfig] = None):
        """
        Initialize the custom toolbar.
        
        Args:
            canvas: The matplotlib FigureCanvas
            parent: Parent widget
            coordinates: Whether to show coordinates
            chart_config: Optional ChartConfig for metadata in PDF export
        """
        self.chart_config = chart_config
        super().__init__(canvas, parent, coordinates=coordinates)
    
    def set_chart_config(self, config: Optional[ChartConfig]):
        """Update the chart configuration for PDF export."""
        self.chart_config = config
    
    def save_figure(self, *args):
        """Override save_figure to save as PDF with metadata."""
        # Get default filename from chart config if available
        default_name = "chart.pdf"
        if self.chart_config and self.chart_config.file_name:
            base_name = os.path.splitext(self.chart_config.file_name)[0]
            chart_title = self.chart_config.title.replace(" ", "_").replace("/", "-") if self.chart_config.title else "chart"
            default_name = f"{base_name}_{chart_title}.pdf"
        
        # Ask user for save location
        filepath, _ = QFileDialog.getSaveFileName(
            self.parent(),
            "Save Chart as PDF",
            default_name,
            "PDF files (*.pdf);;All Files (*)"
        )
        
        if not filepath:
            return  # User cancelled
        
        # Ensure .pdf extension
        if not filepath.lower().endswith('.pdf'):
            filepath += '.pdf'
        
        try:
            self._save_as_pdf(filepath)
            QMessageBox.information(
                self.parent(),
                "Export Complete",
                f"Chart saved to:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.critical(
                self.parent(),
                "Export Error",
                f"Failed to save PDF:\n{str(e)}"
            )
    
    def _save_as_pdf(self, filepath: str):
        """Save the current figure as a PDF with metadata."""
        # Save as PDF with metadata
        with PdfPages(filepath) as pdf:
            # Get the current figure
            fig = self.canvas.figure
            
            # Track added text elements for cleanup
            added_texts = []
            
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
                    text_obj = fig.text(
                        0.5, 0.98, metadata_text,
                        ha='center', va='top', fontsize=8, 
                        color='gray', style='italic',
                        transform=fig.transFigure
                    )
                    added_texts.append(text_obj)
            
            # Add watermark
            watermark = fig.text(
                0.99, 0.01, f'Snapshot Decoder {APP_VERSION}',
                ha='right', va='bottom', fontsize=10, 
                color='lightgray', alpha=0.7,
                transform=fig.transFigure
            )
            added_texts.append(watermark)
            
            # Adjust layout to prevent overlapping
            fig.tight_layout(rect=[0, 0.01, 1, 0.96])
            
            # Save to PDF
            pdf.savefig(fig, dpi=150)
            
            # Remove the temporary text elements after saving
            for text_obj in added_texts:
                text_obj.remove()
            
            # Restore layout
            fig.tight_layout()
            self.canvas.draw()
