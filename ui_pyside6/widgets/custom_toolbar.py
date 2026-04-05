"""
Custom matplotlib toolbar for PySide6.

Provides PDF export with chain of custody metadata.
"""

import os
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QMessageBox, QToolButton
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.backends.backend_pdf import PdfPages

from domain.chart_config import ChartConfig
from version import APP_VERSION
from ui_pyside6.widgets.axis_controls_panel import AxisControlsPanel

from utils import resource_path


class CustomNavigationToolbar(NavigationToolbar2QT):
    """Custom navigation toolbar that saves charts as PDF with metadata."""
    
    # Remove "Configure Subplots" and "Edit Axis" from the default toolbar
    toolitems = [
        t for t in NavigationToolbar2QT.toolitems
        if t[0] not in ("Subplots", "Customize")
    ]
    
    # Signal emitted when chart is added to cart
    add_to_cart_requested = Signal()
    
    # Signal emitted when pop-out is requested
    pop_out_requested = Signal()

    # Signal emitted when Quick IQ is requested
    quick_iq_requested = Signal()
    
    # Signal emitted when value display toggle changes
    value_display_changed = Signal(bool)
    
    # Signal emitted when time slider toggle changes
    time_slider_changed = Signal(bool)

    # Signal emitted when axis controls are changed
    axis_settings_changed = Signal()
    
    def __init__(self, canvas, parent, *, coordinates=True, chart_config: Optional[ChartConfig] = None, show_popout=True):
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
        
        # Add separator and cart button
        self.addSeparator()
        self._cart_btn = QToolButton(self)
        self._cart_btn.setToolTip("Add current chart to the Chart Cart")
        
        # Load cart icon
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        self._cart_btn.setIcon(QIcon(resource_path('data/images/online-shopping.png')))
        self._cart_btn.setIconSize(QSize(20, 20))  # Fixed 20x20 size for toolbar
        
        self._cart_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 4px;
                background-color: #F0F0F0;
            }
            QToolButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QToolButton:pressed {
                background-color: #D0D0D0;
            }
        """)
        self._cart_btn.clicked.connect(self.add_to_cart_requested.emit)
        self.addWidget(self._cart_btn)
        
        # Add value display toggle
        self.addSeparator()
        self._value_display_btn = QToolButton(self)
        self._value_display_btn.setToolTip("Show/hide data values on hover")
        self._value_display_btn.setCheckable(True)  # Makes it a latching button
        
        # Load value popup icon
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        self._value_display_btn.setIcon(QIcon(resource_path('data/images/value-popup.png')))
        self._value_display_btn.setIconSize(QSize(20, 20))  # Fixed 20x20 size for toolbar
        
        self._value_display_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 4px;
                background-color: #F0F0F0;
            }
            QToolButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QToolButton:pressed {
                background-color: #D0D0D0;
            }
            QToolButton:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QToolButton:checked:hover {
                background-color: #106ebe;
            }
        """)
        self._value_display_btn.toggled.connect(self.value_display_changed.emit)
        self.addWidget(self._value_display_btn)
        
        # Add time slider toggle
        self._time_slider_btn = QToolButton(self)
        self._time_slider_btn.setToolTip("Show/hide time slider and cursor")
        self._time_slider_btn.setCheckable(True)  # Makes it a latching button
        
        # Load vertical cursor icon
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        self._time_slider_btn.setIcon(QIcon(resource_path('data/images/time.png')))
        self._time_slider_btn.setIconSize(QSize(20, 20))  # Fixed 20x20 size for toolbar
        
        self._time_slider_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 4px;
                background-color: #F0F0F0;
            }
            QToolButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QToolButton:pressed {
                background-color: #D0D0D0;
            }
            QToolButton:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QToolButton:checked:hover {
                background-color: #106ebe;
            }
        """)
        self._time_slider_btn.toggled.connect(self.time_slider_changed.emit)
        self.addWidget(self._time_slider_btn)

        # Add Quick IQ button
        self._quick_iq_btn = QToolButton(self)
        self._quick_iq_btn.setToolTip("Open Quick IQ in your default browser")

        # Load brain icon
        from PySide6.QtCore import QSize
        self._quick_iq_btn.setIcon(QIcon(resource_path('data/images/brain.png')))
        self._quick_iq_btn.setIconSize(QSize(20, 20))

        self._quick_iq_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 4px;
                background-color: #F0F0F0;
            }
            QToolButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QToolButton:pressed {
                background-color: #D0D0D0;
            }
        """)
        self._quick_iq_btn.clicked.connect(self.quick_iq_requested.emit)
        self.addWidget(self._quick_iq_btn)

        # Add compact axis controls directly on the chart toolbar
        self.addSeparator()
        self._axis_controls = AxisControlsPanel(self, compact=True)
        self._axis_controls.settings_changed.connect(self.axis_settings_changed.emit)
        self.addWidget(self._axis_controls)
        
        # Add pop-out button (only if not in a pop-out window)
        if show_popout:
            self._popout_btn = QToolButton(self)
            self._popout_btn.setToolTip("Pop out chart to separate window")
            
            # Load icon
            from PySide6.QtGui import QIcon
            from PySide6.QtCore import QSize
            self._popout_btn.setIcon(QIcon(resource_path('data/images/expand-in-new-window.png')))
            self._popout_btn.setIconSize(QSize(20, 20))  # Fixed 20x20 size for toolbar
            
            self._popout_btn.setStyleSheet("""
                QToolButton {
                    border: 1px solid #C0C0C0;
                    border-radius: 3px;
                    padding: 4px;
                    background-color: #F0F0F0;
                }
                QToolButton:hover {
                    background-color: #E0E0E0;
                    border: 1px solid #0078d4;
                }
                QToolButton:pressed {
                    background-color: #D0D0D0;
                }
            """)
            self._popout_btn.clicked.connect(self.pop_out_requested.emit)
            self.addWidget(self._popout_btn)

    def get_axis_settings(self) -> dict:
        """Get current axis settings from toolbar controls."""
        return self._axis_controls.get_axis_settings()

    def update_axis_controls_from_config(
        self,
        primary_auto: bool,
        primary_min: Optional[float],
        primary_max: Optional[float],
        secondary_auto: bool,
        secondary_min: Optional[float],
        secondary_max: Optional[float],
    ):
        """Update toolbar axis controls from chart config values."""
        self._axis_controls.update_from_config(
            primary_auto=primary_auto,
            primary_min=primary_min,
            primary_max=primary_max,
            secondary_auto=secondary_auto,
            secondary_min=secondary_min,
            secondary_max=secondary_max,
        )

    def clear_axis_controls(self):
        """Reset toolbar axis controls to defaults."""
        self._axis_controls.clear()
    
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
