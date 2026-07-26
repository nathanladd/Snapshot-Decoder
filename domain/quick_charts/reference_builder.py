"""
Reference chart builder for V2 architecture.

Creates multi-page PDF reference charts using ChartConfigBuilder
and PySide6 file dialogs.
"""

from typing import List, Optional
from PySide6.QtWidgets import QFileDialog, QWidget
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from version import APP_VERSION

from .builders import ChartConfigBuilder
from .reference_definitions import ReferenceChartPage, REFERENCE_CHARTS_BY_TYPE
from domain.snaptypes import SnapType
from domain.chart_config import ChartConfig
from rendering.chart_renderer import ChartRenderer


class ReferenceChartBuilder:
    """Builds multi-page PDF reference charts using V2 architecture."""
    
    def __init__(self, snapshot, parent_widget: Optional[QWidget] = None):
        """
        Initialize the reference chart builder.
        
        Args:
            snapshot: The loaded snapshot containing data and metadata
            parent_widget: Parent widget for file dialogs
        """
        self.snapshot = snapshot
        self.parent_widget = parent_widget
    
    def create_reference_pdf(self, snapshot_type: SnapType) -> Optional[str]:
        """
        Create reference PDF and return file path or None if cancelled.
        
        Args:
            snapshot_type: Type of snapshot to generate reference charts for
            
        Returns:
            File path of saved PDF, or None if user cancelled
        """
        # Use PySide6 file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            "Save Reference Charts PDF",
            "V2_Reference_Charts.pdf",
            "PDF files (*.pdf)"
        )
        
        if not file_path:
            return None
            
        pages = REFERENCE_CHARTS_BY_TYPE.get(snapshot_type, [])
        if not pages:
            return None
            
        self._generate_pdf(pages, file_path)
        return file_path
    
    def build_reference_chart(self, action_id: str) -> Optional[ChartConfig]:
        """
        Build a single reference chart configuration.
        
        Args:
            action_id: Action ID of the reference chart to build
            
        Returns:
            ChartConfig for the reference chart, or None if not found
        """
        # Find the chart definition across all pages
        for pages in REFERENCE_CHARTS_BY_TYPE.values():
            for page in pages:
                for chart_def in page.charts:
                    if chart_def.action_id == action_id:
                        return ChartConfigBuilder.build(chart_def, self.snapshot)
        return None
    
    def _generate_pdf(self, pages: List[ReferenceChartPage], file_path: str):
        """Generate PDF using ChartConfigBuilder for each chart."""
        with PdfPages(file_path) as pdf:
            for page_num, page in enumerate(pages, start=1):
                fig = Figure(figsize=(11, 8.5), dpi=150)
                fig.suptitle(page.title, fontsize=16, fontweight='bold', y=0.96)
                
                # Create subplots
                axes_col = fig.subplots(3, 1)
                charts = page.charts
                
                # Handle layout for pages with fewer charts
                if len(charts) == 1:
                    axes_col[0].set_visible(False)
                    axes_col[2].set_visible(False)
                    axes_to_use = [axes_col[1]]
                else:
                    axes_to_use = list(axes_col)
                
                # Build each chart using ChartConfigBuilder
                for chart_idx, chart_def in enumerate(charts):
                    ax_left = axes_to_use[chart_idx]
                    ax_right = None
                    
                    # Use V2 ChartConfigBuilder
                    config = ChartConfigBuilder.build(chart_def, self.snapshot)
                    
                    # Create secondary axis if needed
                    if config.secondary_axis.series:
                        ax_right = ax_left.twinx()
                    
                    # Render using existing renderer logic
                    renderer = ChartRenderer(config)
                    renderer._render_line_chart(ax_left, ax_right, config.data)
                    renderer._apply_formatting(ax_left, ax_right)
                    
                    # Format title with units
                    self._format_chart_title(ax_left, config, chart_def.title)
                
                # Add metadata and page numbers
                self._add_page_metadata(fig, page_num, len(pages))
                
                pdf.savefig(fig, dpi=150)
                fig.clf()
    
    def _format_chart_title(self, ax_left, config: ChartConfig, chart_title: str):
        """Format chart title with units from PID info."""
        # Get units from pid_info for the first primary PID
        if config.primary_axis.series and config.pid_info:
            first_pid = config.primary_axis.series[0]
            pid_info = config.pid_info.get(first_pid, {})
            unit = pid_info.get("Unit", "")
            if unit:
                chart_title = f"{chart_title} ({unit})"
        
        ax_left.set_ylabel(chart_title, fontsize=8, fontweight='bold')
        ax_left.set_title("")  # Remove top title
        ax_left.set_xlabel("")  # Remove x-axis label for more vertical space
    
    def _add_page_metadata(self, fig: Figure, page_num: int, total_pages: int):
        """Add metadata, page numbers, and watermark to the figure."""
        # Add chain of custody metadata at the top
        metadata_parts = []
        if hasattr(self.snapshot, 'file_name') and self.snapshot.file_name:
            metadata_parts.append(f"File: {self.snapshot.file_name}")
        if hasattr(self.snapshot, 'date_time') and self.snapshot.date_time:
            metadata_parts.append(f"Date/Time: {self.snapshot.date_time}")
        if hasattr(self.snapshot, 'hours') and self.snapshot.hours is not None and self.snapshot.hours > 0:
            metadata_parts.append(f"Engine Hours: {self.snapshot.hours}")
        
        if metadata_parts:
            metadata_text = "  |  ".join(metadata_parts)
            fig.text(0.5, 0.99, metadata_text, 
                    ha='center', va='top', fontsize=8, color='gray', style='italic')
        
        # Add page number at the bottom
        fig.text(0.5, 0.02, f'Page {page_num} of {total_pages}', 
                ha='center', va='bottom', fontsize=8, color='gray')
        
        # Add watermark
        fig.text(0.99, 0.01, f'Snapshot Decoder {APP_VERSION}', 
                ha='right', va='bottom', fontsize=8, color='lightgray', alpha=0.7)
        
        # Adjust layout to prevent overlapping
        fig.tight_layout(rect=[0.02, 0.04, 0.98, 0.92])
