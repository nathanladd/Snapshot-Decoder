"""
Chart Cart widget for managing chart configurations with thumbnail display.

PySide6 port of the tkinter ChartCart from v1.
"""

import copy
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QLabel,
    QPushButton, QFrame, QFileDialog, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QImage

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from domain.chart_config import ChartConfig
from ui.chart_renderer import ChartRenderer
from version import APP_VERSION
from infrastructure import info, error


class ChartCartItem(QFrame):
    """A single item in the chart cart with thumbnail, title, and control buttons."""
    
    # Standard card dimensions
    CARD_WIDTH = 200
    CARD_HEIGHT = 180
    THUMBNAIL_HEIGHT = 100
    
    move_up_requested = Signal(int)
    move_down_requested = Signal(int)
    remove_requested = Signal(int)
    
    def __init__(self, config: ChartConfig, index: int, parent=None):
        super().__init__(parent)
        self.config = config
        self.index = index
        
        # Use fixed size policy to prevent expansion
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Also set fixed size to prevent flow layout from expanding
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("""
            ChartCartItem {
                background-color: white;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                margin: 4px;
            }
            ChartCartItem:hover {
                border: 2px solid #0078d4;
                background-color: #F8F8FF;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Thumbnail (fixed height)
        thumbnail_label = QLabel()
        thumbnail_label.setFixedSize(self.CARD_WIDTH - 16, self.THUMBNAIL_HEIGHT)
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #F8F8F8;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        pixmap = self._render_thumbnail(config)
        if pixmap:
            # Scale thumbnail to fit the fixed area
            scaled_pixmap = pixmap.scaled(
                thumbnail_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            thumbnail_label.setPixmap(scaled_pixmap)
        else:
            thumbnail_label.setText("(No preview)")
            thumbnail_label.setStyleSheet("""
                QLabel {
                    background-color: #F8F8F8;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    margin: 2px;
                    color: #999;
                    font-style: italic;
                    font-size: 10px;
                }
            """)
        layout.addWidget(thumbnail_label)
        
        # Title (with word wrap and max height)
        title_label = QLabel(config.title or "Chart")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #333;
                padding: 4px 6px;
            }
        """)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(40)  # Allow up to 2 lines
        layout.addWidget(title_label)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)
        
        btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 2px;
                padding: 1px 4px;
                background-color: #F0F0F0;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
        """
        
        up_btn = QPushButton("▲")
        up_btn.setFixedWidth(24)
        up_btn.setStyleSheet(btn_style)
        up_btn.setToolTip("Move up")
        up_btn.clicked.connect(lambda: self.move_up_requested.emit(self.index))
        
        down_btn = QPushButton("▼")
        down_btn.setFixedWidth(24)
        down_btn.setStyleSheet(btn_style)
        down_btn.setToolTip("Move down")
        down_btn.clicked.connect(lambda: self.move_down_requested.emit(self.index))
        
        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(24)
        remove_btn.setStyleSheet(btn_style.replace("#F0F0F0", "#FFF0F0").replace("#E0E0E0", "#FFD0D0"))
        remove_btn.setToolTip("Remove from cart")
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.index))
        
        btn_layout.addStretch()
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def _render_thumbnail(self, config: ChartConfig) -> Optional[QPixmap]:
        """Render a thumbnail of the chart config as a QPixmap."""
        try:
            renderer = ChartRenderer(config)
            fig = renderer.render_thumbnail(figsize=(3, 1.5), dpi=80)
            
            # Remove axis numbers/labels but keep the plot clean
            axes = fig.get_axes()
            for ax in axes:
                ax.set_xlabel("")
                ax.set_ylabel("")
                ax.set_xticklabels([])
                ax.set_yticklabels([])
            
            fig.tight_layout()
        except (ValueError, Exception):
            # Fallback for charts that can't render normally
            fig = Figure(figsize=(3, 1.5), dpi=80)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, config.title or "Chart", ha='center', va='center', fontsize=8)
            ax.set_xticks([])
            ax.set_yticks([])
        
        # Convert matplotlib figure to QPixmap
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        
        buf = canvas.buffer_rgba()
        width, height = fig.get_size_inches() * fig.get_dpi()
        width, height = int(width), int(height)
        
        image = QImage(buf, width, height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(image)
        
        fig.clf()
        del fig
        
        return pixmap
    
    def sizeHint(self) -> QSize:
        """Return the preferred size for the card."""
        return QSize(self.CARD_WIDTH, self.CARD_HEIGHT)
    
    def minimumSize(self) -> QSize:
        """Return the minimum size for the card."""
        return QSize(self.CARD_WIDTH, self.CARD_HEIGHT)


class ChartCartWidget(QWidget):
    """Manages a list of chart configurations with thumbnail display."""
    
    cart_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.configs: List[ChartConfig] = []
        self._items: List[ChartCartItem] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        # Header with title and export button
        header = QHBoxLayout()
        header.setContentsMargins(4, 4, 4, 0)
        
        title_label = QLabel("Chart Cart")
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        header.addWidget(title_label)
        
        header.addStretch()
        
        self._count_label = QLabel("0 charts")
        self._count_label.setStyleSheet("font-size: 10px; color: #666;")
        header.addWidget(self._count_label)
        
        export_btn = QPushButton("Export PDF")
        export_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 3px 8px;
                background-color: #F0F0F0;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
        """)
        export_btn.setToolTip("Export all charts to PDF")
        export_btn.clicked.connect(self._export_to_pdf)
        header.addWidget(export_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 3px 8px;
                background-color: #FFF0F0;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #FFD0D0;
                border: 1px solid #d40000;
            }
        """)
        clear_btn.setToolTip("Clear all charts from cart")
        clear_btn.clicked.connect(self._clear_cart)
        header.addWidget(clear_btn)
        
        main_layout.addLayout(header)
        
        # Scrollable area for chart items
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self._scroll_content = QWidget()
        self._grid_layout = QGridLayout(self._scroll_content)
        self._grid_layout.setContentsMargins(4, 4, 4, 4)
        self._grid_layout.setSpacing(8)
        
        self._scroll_area.setWidget(self._scroll_content)
        main_layout.addWidget(self._scroll_area, stretch=1)
        
        # Empty state label (managed outside grid)
        self._empty_label = QLabel("Add charts using the cart button\non the chart toolbar")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #999; font-style: italic; font-size: 10px;")
        self._grid_layout.addWidget(self._empty_label, 0, 0)
    
    def add_config(self, config: ChartConfig):
        """Add a new chart config to the cart."""
        config_copy = copy.deepcopy(config)
        self.configs.append(config_copy)
        self._rebuild_ui()
        info(f"Chart added to cart: {config.title} ({len(self.configs)} total)")
        self.cart_changed.emit()
    
    def remove_config(self, index: int):
        """Remove config at index."""
        if 0 <= index < len(self.configs):
            removed = self.configs.pop(index)
            info(f"Chart removed from cart: {removed.title} ({len(self.configs)} remaining)")
            self._rebuild_ui()
            self.cart_changed.emit()
    
    def move_up(self, index: int):
        """Move config up in the list."""
        if index > 0:
            self.configs[index], self.configs[index - 1] = self.configs[index - 1], self.configs[index]
            self._rebuild_ui()
            self.cart_changed.emit()
    
    def move_down(self, index: int):
        """Move config down in the list."""
        if index < len(self.configs) - 1:
            self.configs[index], self.configs[index + 1] = self.configs[index + 1], self.configs[index]
            self._rebuild_ui()
            self.cart_changed.emit()
    
    def _rebuild_ui(self):
        """Rebuild the grid with the correct number of columns."""
        # Remove all items from grid
        for item in self._items:
            self._grid_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()
        
        # Update count label
        count = len(self.configs)
        self._count_label.setText(f"{count} chart{'s' if count != 1 else ''}")
        
        # Show/hide empty label
        if count == 0:
            self._empty_label.show()
            return
        self._empty_label.hide()
        
        # Calculate columns based on available width
        cols = self._calc_columns()
        
        # Add items to grid
        for i, config in enumerate(self.configs):
            item = ChartCartItem(config, i)
            item.move_up_requested.connect(self.move_up)
            item.move_down_requested.connect(self.move_down)
            item.remove_requested.connect(self.remove_config)
            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(item, row, col, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self._items.append(item)
    
    def _calc_columns(self) -> int:
        """Calculate how many card columns fit in the current width."""
        available = self._scroll_area.viewport().width()
        card_w = ChartCartItem.CARD_WIDTH + 8  # card + spacing
        cols = max(1, available // card_w)
        return cols
    
    def resizeEvent(self, event):
        """Recalculate grid columns when the widget is resized."""
        super().resizeEvent(event)
        if self._items:
            self._relayout_grid()
    
    def _relayout_grid(self):
        """Re-place existing items into the grid with updated column count."""
        cols = self._calc_columns()
        for i, item in enumerate(self._items):
            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(item, row, col, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    
    def _clear_cart(self):
        """Clear all charts from the cart."""
        if not self.configs:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear Chart Cart",
            f"Remove all {len(self.configs)} charts from the cart?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.configs.clear()
            self._rebuild_ui()
            info("Chart cart cleared")
            self.cart_changed.emit()
    
    def _export_to_pdf(self):
        """Export all charts in the cart to a PDF file."""
        if not self.configs:
            QMessageBox.information(self, "Cart Empty", "Add charts to the cart before exporting.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart Cart to PDF",
            "chart_report.pdf",
            "PDF files (*.pdf);;All Files (*)"
        )
        
        if not filepath:
            return
        
        if not filepath.lower().endswith('.pdf'):
            filepath += '.pdf'
        
        try:
            from file_io.pdf_export import ChartCartPdfExporter
            
            metadata = {
                'Title': 'Snapshot Chart Report',
                'Author': 'Snapshot Decoder',
                'Creator': f'Snapshot Decoder v{APP_VERSION}'
            }
            
            exporter = ChartCartPdfExporter(self.configs)
            exporter.export_with_metadata(
                filepath,
                page_size=(11, 8.5),
                dpi=150,
                metadata=metadata
            )
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(self.configs)} charts to:\n{filepath}"
            )
            info(f"Chart cart exported to PDF: {filepath}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export PDF:\n{str(e)}"
            )
            error(f"Chart cart PDF export failed: {str(e)}")
    
    def get_config_count(self) -> int:
        """Get the number of configs in the cart."""
        return len(self.configs)
