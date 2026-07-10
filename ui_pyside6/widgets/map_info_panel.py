"""
MAP info panel widget displaying values decoded from the ECU Map Version.

Renders compact horizontal chips (displacement, machine subtype, and
horsepower code) suitable for the window status bar.
"""

from typing import Optional

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from domain.snapshot import Snapshot


class MapInfoPanel(QWidget):
    """Panel showing ECU Map Version values as blue info chips."""

    # Blue info chips - distinct from the system status chips so they read as
    # information, not system status.
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

    def _chip_texts(self, snapshot: Snapshot) -> list:
        """Build the list of chip strings for a snapshot's decoded map values."""
        horsepower = getattr(snapshot, "horsepower", None)
        return [text for text in (
            getattr(snapshot, "displacement", None),
            getattr(snapshot, "subtype", None),
            f"HP Code: {horsepower}" if horsepower is not None else None,
        ) if text]

    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with a snapshot's decoded ECU Map Version values."""
        self._clear_chips()
        if snapshot is None:
            return

        for text in self._chip_texts(snapshot):
            chip = QLabel(text)
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip.setFixedHeight(20)
            chip.setStyleSheet(self._CHIP_STYLE)
            self._layout.addWidget(chip)

    def _clear_chips(self):
        """Remove all chip labels from the layout."""
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def clear(self):
        """Clear all displayed chips."""
        self._clear_chips()
