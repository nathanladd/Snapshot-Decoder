"""
System panel widget displaying system availability status.
"""

from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout
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
        ("has_mdp", "MDP"),  # MDP now uses has_mdp attribute like other systems
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._system_labels: Dict[str, QLabel] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Create indicator-style labels for each system in a horizontal row
        # (sized to sit in the window status bar)
        for attr_name, display_name in self.SYSTEMS:
            label = QLabel(display_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedHeight(20)
            label.setFixedWidth(80)
            self._system_labels[attr_name] = label

            self._set_label_off(label)
            layout.addWidget(label)
    
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
        if success_rate <= 50.0:
            bg = "#C62828"
            fg = "#FFFFFF"
            border = "#E53935"
        elif success_rate >= 76.0:
            bg = "#00AA00"
            fg = "#FFFFFF"
            border = "#00DD00"
        else:
            bg = "#F9A825"
            fg = "#111111"
            border = "#FBC02D"

        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-weight: bold;
                font-size: 10px;
                border: 2px solid {border};
                border-radius: 4px;
                padding: 2px 6px;
            }}
        """)
        label.setText(f"MDP {success_rate:.1f}%")
        font = label.font()
        font.setStrikeOut(False)
        label.setFont(font)
    
    def _set_scr_label(self, label: QLabel, snapshot: Snapshot):
        """Style the SCR label, flagging temperature-only (unverified) detection."""
        if not getattr(snapshot, "has_scr", False):
            label.setText("SCR")
            label.setToolTip("")
            self._set_label_off(label)
            return

        if getattr(snapshot, "scr_temp_unverified", False):
            # Detected from inlet/outlet temperatures on an engine we could not
            # verify (ECU map version absent/unrecognized).
            label.setText("SCR *")
            label.setToolTip(
                "Engine horsepower could not be verified from the MAP file.\n"
                "The fall-back temperature sensor method was used to detect the "
                "SCR, which is less accurate."
            )
        else:
            label.setText("SCR")
            label.setToolTip("")
        self._set_label_on(label)

    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with snapshot data."""
        if snapshot is None:
            for attr_name, label in self._system_labels.items():
                if attr_name == "has_mdp":
                    # Reset MDP label text to just "MDP"
                    label.setText("MDP")
                elif attr_name == "has_scr":
                    label.setText("SCR")
                    label.setToolTip("")
                self._set_label_off(label)
            return

        # Update each system label based on snapshot attributes
        for attr_name, display_name in self.SYSTEMS:
            label = self._system_labels[attr_name]

            if attr_name == "has_mdp":
                # Special handling for MDP system - check both detection and success rate
                if getattr(snapshot, attr_name, False):
                    mdp_rate = snapshot.mdp_success_rate if snapshot.mdp_success_rate is not None else 0.0
                    self._set_mdp_label(label, mdp_rate)
                else:
                    self._set_label_off(label)
            elif attr_name == "has_scr":
                # SCR may be inferred from temperature sensors on an engine we
                # could not verify; mark it and explain via tooltip.
                self._set_scr_label(label, snapshot)
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
