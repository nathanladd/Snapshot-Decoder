"""
Header panel widget displaying snapshot metadata with toolbar.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QGroupBox, QToolBar, QToolButton
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QAction, QIcon, QPixmap, QDragEnterEvent, QDragLeaveEvent, QDropEvent

from domain.snapshot import Snapshot
from utils import resource_path


class HeaderPanel(QWidget):
    """Panel displaying snapshot header information with toolbar."""
    
    # Signals for toolbar actions
    open_requested = Signal()
    close_requested = Signal()
    raw_data_requested = Signal()
    clean_table_requested = Signal()
    chart_table_requested = Signal()
    help_requested = Signal()
    file_dropped = Signal(str)
    
    _VALID_EXTENSIONS = ('.xlsx', '.xls')
    
    _GROUP_STYLE_DEFAULT = "QGroupBox { font-weight: bold; }"

    # Blue info chips - matches the system panel indicator styling but in a
    # distinct color so they read as information, not system status
    _CHIP_STYLE = """
        QLabel {
            background-color: #0078d4;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 10px;
            border: 2px solid #4aa3e0;
            border-radius: 4px;
            padding: 2px 6px;
        }
    """
    _GROUP_STYLE_EMPTY = (
        "QGroupBox { font-weight: bold; border: 2px dashed #0078d4; "
        "border-radius: 4px; margin-top: 0.5em; padding-top: 0.6em; }"
    )
    _GROUP_STYLE_HOVER = (
        "QGroupBox { font-weight: bold; border: 2px solid #0078d4; "
        "border-radius: 4px; margin-top: 0.5em; padding-top: 0.6em; "
        "background-color: rgba(0, 120, 212, 13); }"
    )
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._snapshot_loaded = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add toolbar
        self._setup_toolbar()
        layout.addWidget(self._toolbar)
        
        # Group box for header info
        self._group = QGroupBox("Header Info")
        self._group.setToolTip("Drag and drop a snapshot file here to open it")
        self._group_layout = QVBoxLayout(self._group)
        self._group_layout.setSpacing(4)
        
        # Grid for dynamic header rows
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(4)
        self._group_layout.addWidget(self._grid_widget)
        
        # Container for dynamic header labels
        self._header_labels = []
        
        # Empty-state placeholder (icon + prompt text)
        self._placeholder = QLabel()
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = resource_path("data/app_images/folder-open.png")
        self._placeholder.setText(
            f'<div style="text-align:center; padding:12px;">'
            f'<img src="{icon_path}" width="32" height="32" '
            f'style="opacity:0.4;"><br>'
            f'<span style="color:#888; font-size:9pt;">'
            f'Drop snapshot file here &mdash; or click Open</span></div>'
        )
        self._group_layout.addWidget(self._placeholder)
        
        # Persistent hint label (visible when snapshot is loaded)
        self._drop_hint = QLabel("Drop a file here to open")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setStyleSheet(
            "color: #888; font-size: 8pt; font-style: italic; padding: 2px 0;"
        )
        self._drop_hint.hide()
        self._group_layout.addWidget(self._drop_hint)
        
        # Start in empty state
        self._set_empty_state()
        
        layout.addWidget(self._group)
    
    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with snapshot data."""
        # Clear existing header labels
        self._clear_header_labels()
        
        if snapshot is None:
            return
        
        # Switch to loaded state
        self._set_loaded_state()
        
        # Add file name as first entry
        self._add_header_row("File:", snapshot.file_name)
        
        # Add snapshot type as second entry
        self._add_header_row("Type:", snapshot.snapshot_type.description)
        
        # Add all parsed header information
        if snapshot.header_list:
            for label, value in snapshot.header_list:
                self._add_header_row(f"{label}:", value)
        
        # Add derived values if available
        if snapshot.hours is not None:
            self._add_header_row("Engine Hours:", f"{snapshot.hours:.1f}")
        if snapshot.idle_time is not None and snapshot.idle_time > 0:
            self._add_header_row("Idle Time:", f"{snapshot.idle_time:.1f}")

        # Compact chips for values decoded from the ECU Map Version
        horsepower = getattr(snapshot, "horsepower", None)
        chip_texts = [text for text in (
            getattr(snapshot, "displacement", None),
            getattr(snapshot, "subtype", None),
            f"HP Code: {horsepower}" if horsepower is not None else None,
        ) if text]
        if chip_texts:
            self._add_chip_row(chip_texts)
    
    def clear(self):
        """Clear all displayed data."""
        self._clear_header_labels()
        self._set_empty_state()
    
    def _clear_header_labels(self):
        """Clear all dynamic header labels."""
        # Remove all widgets from the grid layout
        while self._grid_layout.count():
            child = self._grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear the header labels list
        self._header_labels.clear()
    
    def _add_header_row(self, label_text: str, value_text: str):
        """Add a new header row to the layout."""
        row = self._grid_layout.rowCount()
        
        label = QLabel(label_text)
        # Use QFont for bold instead of stylesheet to preserve palette colors
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        
        value_label = QLabel(value_text or "-")
        value_label.setWordWrap(True)
        
        self._grid_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._grid_layout.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignTop)
        
        # Store references to the labels
        self._header_labels.append((label, value_label))
        
        # Ensure the value column stretches
        self._grid_layout.setColumnStretch(1, 1)
    
    def _add_chip_row(self, texts: list):
        """Add a row of compact info chips spanning both grid columns."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 0)
        row_layout.setSpacing(4)

        for text in texts:
            chip = QLabel(text)
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip.setFixedHeight(20)
            chip.setStyleSheet(self._CHIP_STYLE)
            row_layout.addWidget(chip)

        # Keep chips left-aligned instead of stretching across the row
        row_layout.addStretch(1)

        row = self._grid_layout.rowCount()
        self._grid_layout.addWidget(row_widget, row, 0, 1, 2)

    def _setup_toolbar(self):
        """Set up the toolbar with common actions."""
        self._toolbar = QToolBar()
        self._toolbar.setOrientation(Qt.Horizontal)
        self._toolbar.setMovable(False)
        
        # Apply consistent styling matching existing chart toolbar
        self._toolbar.setStyleSheet("""
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
        
        # Open action
        open_btn = QToolButton()
        open_btn.setIcon(QIcon(resource_path("data/app_images/folder-open.png")))
        open_btn.setToolTip("Open snapshot file (Ctrl+O)")
        open_btn.clicked.connect(self.open_requested.emit)
        self._toolbar.addWidget(open_btn)
        
        # Close action
        close_btn = QToolButton()
        close_btn.setIcon(QIcon(resource_path("data/app_images/folder-close.png")))
        close_btn.setToolTip("Close snapshot")
        close_btn.clicked.connect(self.close_requested.emit)
        self._toolbar.addWidget(close_btn)
        
        # Raw Data action
        raw_data_btn = QToolButton()
        raw_data_btn.setIcon(QIcon(resource_path("data/app_images/raw-table.png")))
        raw_data_btn.setToolTip("Show raw data table")
        raw_data_btn.clicked.connect(self.raw_data_requested.emit)
        self._toolbar.addWidget(raw_data_btn)
        
        # Clean Table action
        clean_table_btn = QToolButton()
        clean_table_btn.setIcon(QIcon(resource_path("data/app_images/data-cleaning.png")))
        clean_table_btn.setToolTip("Show clean data table")
        clean_table_btn.clicked.connect(self.clean_table_requested.emit)
        self._toolbar.addWidget(clean_table_btn)
        
        # Chart Table action
        chart_table_btn = QToolButton()
        chart_table_btn.setIcon(QIcon(resource_path("data/app_images/chart-table.png")))
        chart_table_btn.setToolTip("Show chart data table")
        chart_table_btn.clicked.connect(self.chart_table_requested.emit)
        self._toolbar.addWidget(chart_table_btn)
        
        # Help action
        help_btn = QToolButton()
        help_btn.setIcon(QIcon(resource_path("data/app_images/information.png")))
        help_btn.setToolTip("Show help documentation (F1)")
        help_btn.clicked.connect(self.help_requested.emit)
        self._toolbar.addWidget(help_btn)
    
    # ------------------------------------------------------------------
    # Drag-and-drop support
    # ------------------------------------------------------------------
    
    def _set_empty_state(self):
        """Switch to empty-state visuals (dashed border, placeholder)."""
        self._snapshot_loaded = False
        self._group.setStyleSheet(self._GROUP_STYLE_EMPTY)
        self._placeholder.show()
        self._drop_hint.hide()
    
    def _set_loaded_state(self):
        """Switch to loaded-state visuals (default border, hint label)."""
        self._snapshot_loaded = True
        self._group.setStyleSheet(self._GROUP_STYLE_DEFAULT)
        self._placeholder.hide()
        self._drop_hint.show()
    
    def _apply_hover_style(self):
        """Apply drag-hover highlight."""
        self._group.setStyleSheet(self._GROUP_STYLE_HOVER)
    
    def _remove_hover_style(self):
        """Revert to the appropriate non-hover style."""
        if self._snapshot_loaded:
            self._group.setStyleSheet(self._GROUP_STYLE_DEFAULT)
        else:
            self._group.setStyleSheet(self._GROUP_STYLE_EMPTY)
    
    @staticmethod
    def _valid_file_urls(mime_data: QMimeData) -> list:
        """Return list of local file paths with valid snapshot extensions."""
        if not mime_data.hasUrls():
            return []
        return [
            url.toLocalFile() for url in mime_data.urls()
            if url.isLocalFile()
            and url.toLocalFile().lower().endswith(HeaderPanel._VALID_EXTENSIONS)
        ]
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept drag if it contains valid snapshot file URLs."""
        if self._valid_file_urls(event.mimeData()):
            event.acceptProposedAction()
            self._apply_hover_style()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """Remove hover highlight when drag leaves."""
        self._remove_hover_style()
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop — emit file_dropped with the first valid path."""
        self._remove_hover_style()
        paths = self._valid_file_urls(event.mimeData())
        if paths:
            event.acceptProposedAction()
            self.file_dropped.emit(paths[0])
        else:
            event.ignore()
