"""
Header panel widget displaying snapshot metadata.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox
)
from PySide6.QtCore import Qt

from domain.snapshot import Snapshot


class HeaderPanel(QWidget):
    """Panel displaying snapshot header information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Group box for header info
        group = QGroupBox("Snapshot Info")
        group_layout = QGridLayout(group)
        group_layout.setSpacing(4)
        
        # Labels for header fields
        self._labels = {}
        fields = [
            ("file_name", "File:"),
            ("snapshot_type", "Type:"),
            ("date_time", "Date/Time:"),
            ("hours", "Engine Hours:"),
            ("idle_time", "Idle Time:"),
            ("mdp_success", "MDP Success:"),
            ("systems", "Systems:"),
        ]
        
        for row, (key, label_text) in enumerate(fields):
            label = QLabel(label_text)
            # Use QFont for bold instead of stylesheet to preserve palette colors
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            value_label = QLabel("-")
            value_label.setWordWrap(True)
            
            group_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignTop)
            group_layout.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignTop)
            self._labels[key] = value_label
        
        group_layout.setColumnStretch(1, 1)
        layout.addWidget(group)
    
    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with snapshot data."""
        if snapshot is None:
            for label in self._labels.values():
                label.setText("-")
            return
        
        self._labels["file_name"].setText(snapshot.file_name)
        self._labels["snapshot_type"].setText(snapshot.snapshot_type.name)
        self._labels["date_time"].setText(snapshot.date_time or "-")
        self._labels["hours"].setText(f"{snapshot.hours:.1f}" if snapshot.hours else "-")
        self._labels["idle_time"].setText(f"{snapshot.idle_time:.1f}" if snapshot.idle_time else "-")
        self._labels["mdp_success"].setText(
            f"{snapshot.mdp_success_rate:.1f}%" if snapshot.mdp_success_rate else "-"
        )
        
        # Build systems string
        systems = []
        if snapshot.has_egr:
            systems.append("EGR")
        if snapshot.has_turbo:
            systems.append("Turbo")
        if snapshot.has_doc:
            systems.append("DOC")
        if snapshot.has_dpf:
            systems.append("DPF")
        if snapshot.has_scr:
            systems.append("SCR")
        if snapshot.has_air_throttle:
            systems.append("Air Throttle")
        
        self._labels["systems"].setText(", ".join(systems) if systems else "-")
    
    def clear(self):
        """Clear all displayed data."""
        self.set_snapshot(None)
