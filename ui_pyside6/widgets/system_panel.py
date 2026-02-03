"""
System panel widget displaying system availability status.
"""

from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from domain.snapshot import Snapshot


class SystemPanel(QWidget):
    """Panel displaying system availability with styled labels."""
    
    # System definitions: (attribute_name, display_name)
    SYSTEMS = [
        ("has_egr", "EGR"),
        ("has_doc", "DOC"),
        ("has_dpf", "DPF"),
        ("has_scr", "SCR"),
        ("has_air_throttle", "Air Throttle"),
        ("mdp_system", "MDP"),  # Special case for MDP system
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._system_labels: Dict[str, QLabel] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Create indicator-style labels for each system in vertical column
        for attr_name, display_name in self.SYSTEMS:
            label = QLabel(display_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedHeight(20)
            label.setFixedWidth(70)
            self._system_labels[attr_name] = label
            
            # Special initialization for MDP label
            if attr_name == "mdp_system":
                label.setText("MDP")  # Initial text
            
            self._set_label_off(label)
            layout.addWidget(label)
        
        # Add stretch to push labels to center when there's extra space
        top_stretch = 1
        bottom_stretch = 1
        layout.insertStretch(0, top_stretch)  # Add stretch at top
        layout.addStretch(bottom_stretch)    # Add stretch at bottom
    
    def _set_label_on(self, label: QLabel):
        """Style label as ON - glowing green indicator light."""
        label.setStyleSheet("""
            QLabel {
                background-color: #00AA00;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10px;
                border: 2px solid #00DD00;
                border-radius: 4px;
                padding: 2px 6px;
            }
        """)
        font = label.font()
        font.setStrikeOut(False)
        label.setFont(font)
    
    def _set_label_off(self, label: QLabel):
        """Style label as OFF - dim indicator light."""
        label.setStyleSheet("""
            QLabel {
                background-color: #D0D0D0;
                color: #888888;
                font-weight: normal;
                font-size: 10px;
                border: 2px solid #B0B0B0;
                border-radius: 4px;
                padding: 2px 6px;
            }
        """)
        font = label.font()
        font.setStrikeOut(False)
        label.setFont(font)
    
    def _set_mdp_label(self, label: QLabel, success_rate: float):
        """Style MDP label with success percentage."""
        # Green background with success percentage
        label.setStyleSheet(f"""
            QLabel {{
                background-color: #00AA00;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 9px;
                border: 2px solid #00DD00;
                border-radius: 4px;
                padding: 2px 4px;
            }}
        """)
        label.setText(f"MDP {success_rate:.1f}%")
        font = label.font()
        font.setStrikeOut(False)
        label.setFont(font)
    
    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with snapshot data."""
        if snapshot is None:
            for attr_name, label in self._system_labels.items():
                if attr_name == "mdp_system":
                    # Reset MDP label text to just "MDP"
                    label.setText("MDP")
                self._set_label_off(label)
            return
        
        # Update each system label based on snapshot attributes
        for attr_name, display_name in self.SYSTEMS:
            label = self._system_labels[attr_name]
            
            if attr_name == "mdp_system":
                # Special handling for MDP system
                if snapshot.mdp_success_rate is not None and snapshot.mdp_success_rate > 0:
                    self._set_mdp_label(label, snapshot.mdp_success_rate)
                else:
                    self._set_label_off(label)
            else:
                # Regular system handling
                has_system = getattr(snapshot, attr_name, False)
                
                if has_system:
                    self._set_label_on(label)
                else:
                    self._set_label_off(label)
    
    def clear(self):
        """Clear all displayed data."""
        self.set_snapshot(None)
