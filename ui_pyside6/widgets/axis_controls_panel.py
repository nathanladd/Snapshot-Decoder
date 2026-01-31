"""
Axis controls panel widget for chart axis limits.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QLabel, QLineEdit, QFormLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDoubleValidator


class AxisControlsPanel(QWidget):
    """Panel with controls for chart axis limits."""
    
    # Signal emitted when any axis setting changes
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Group box
        self._group = QGroupBox("Axis Ranges (optional)")
        group_layout = QVBoxLayout(self._group)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)
        
        # Validator for numeric input
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        
        # Primary axis controls
        primary_row = QHBoxLayout()
        primary_row.setSpacing(8)
        
        self._primary_auto = QCheckBox("Primary auto")
        self._primary_auto.setChecked(True)
        primary_row.addWidget(self._primary_auto)
        
        primary_row.addWidget(QLabel("min:"))
        self._primary_min = QLineEdit()
        self._primary_min.setMaximumWidth(70)
        self._primary_min.setValidator(validator)
        self._primary_min.setEnabled(False)
        primary_row.addWidget(self._primary_min)
        
        primary_row.addWidget(QLabel("max:"))
        self._primary_max = QLineEdit()
        self._primary_max.setMaximumWidth(70)
        self._primary_max.setValidator(validator)
        self._primary_max.setEnabled(False)
        primary_row.addWidget(self._primary_max)
        
        primary_row.addStretch()
        group_layout.addLayout(primary_row)
        
        # Secondary axis controls
        secondary_row = QHBoxLayout()
        secondary_row.setSpacing(8)
        
        self._secondary_auto = QCheckBox("Secondary auto")
        self._secondary_auto.setChecked(True)
        secondary_row.addWidget(self._secondary_auto)
        
        secondary_row.addWidget(QLabel("min:"))
        self._secondary_min = QLineEdit()
        self._secondary_min.setMaximumWidth(70)
        self._secondary_min.setValidator(validator)
        self._secondary_min.setEnabled(False)
        secondary_row.addWidget(self._secondary_min)
        
        secondary_row.addWidget(QLabel("max:"))
        self._secondary_max = QLineEdit()
        self._secondary_max.setMaximumWidth(70)
        self._secondary_max.setValidator(validator)
        self._secondary_max.setEnabled(False)
        secondary_row.addWidget(self._secondary_max)
        
        secondary_row.addStretch()
        group_layout.addLayout(secondary_row)
        
        layout.addWidget(self._group)
    
    def _connect_signals(self):
        """Connect internal signals."""
        # Auto checkboxes toggle input fields and emit change
        self._primary_auto.toggled.connect(self._on_primary_auto_toggled)
        self._secondary_auto.toggled.connect(self._on_secondary_auto_toggled)
        
        # Line edits emit change on editing finished
        self._primary_min.editingFinished.connect(self.settings_changed.emit)
        self._primary_max.editingFinished.connect(self.settings_changed.emit)
        self._secondary_min.editingFinished.connect(self.settings_changed.emit)
        self._secondary_max.editingFinished.connect(self.settings_changed.emit)
    
    def _on_primary_auto_toggled(self, checked: bool):
        """Handle primary auto checkbox toggle."""
        self._primary_min.setEnabled(not checked)
        self._primary_max.setEnabled(not checked)
        self.settings_changed.emit()
    
    def _on_secondary_auto_toggled(self, checked: bool):
        """Handle secondary auto checkbox toggle."""
        self._secondary_min.setEnabled(not checked)
        self._secondary_max.setEnabled(not checked)
        self.settings_changed.emit()
    
    # Getters
    def is_primary_auto(self) -> bool:
        """Return whether primary axis is in auto-scale mode."""
        return self._primary_auto.isChecked()
    
    def is_secondary_auto(self) -> bool:
        """Return whether secondary axis is in auto-scale mode."""
        return self._secondary_auto.isChecked()
    
    def get_primary_min(self) -> Optional[float]:
        """Get primary axis minimum value."""
        return self._parse_float(self._primary_min.text())
    
    def get_primary_max(self) -> Optional[float]:
        """Get primary axis maximum value."""
        return self._parse_float(self._primary_max.text())
    
    def get_secondary_min(self) -> Optional[float]:
        """Get secondary axis minimum value."""
        return self._parse_float(self._secondary_min.text())
    
    def get_secondary_max(self) -> Optional[float]:
        """Get secondary axis maximum value."""
        return self._parse_float(self._secondary_max.text())
    
    def _parse_float(self, text: str) -> Optional[float]:
        """Parse a string to float, returning None if invalid."""
        try:
            return float(text) if text.strip() else None
        except ValueError:
            return None
    
    # Setters (for updating controls from chart config)
    def set_primary_auto(self, auto: bool):
        """Set primary axis auto-scale mode."""
        self._primary_auto.blockSignals(True)
        self._primary_auto.setChecked(auto)
        self._primary_min.setEnabled(not auto)
        self._primary_max.setEnabled(not auto)
        self._primary_auto.blockSignals(False)
    
    def set_secondary_auto(self, auto: bool):
        """Set secondary axis auto-scale mode."""
        self._secondary_auto.blockSignals(True)
        self._secondary_auto.setChecked(auto)
        self._secondary_min.setEnabled(not auto)
        self._secondary_max.setEnabled(not auto)
        self._secondary_auto.blockSignals(False)
    
    def set_primary_min(self, value: Optional[float]):
        """Set primary axis minimum value."""
        self._primary_min.blockSignals(True)
        self._primary_min.setText(str(value) if value is not None else "")
        self._primary_min.blockSignals(False)
    
    def set_primary_max(self, value: Optional[float]):
        """Set primary axis maximum value."""
        self._primary_max.blockSignals(True)
        self._primary_max.setText(str(value) if value is not None else "")
        self._primary_max.blockSignals(False)
    
    def set_secondary_min(self, value: Optional[float]):
        """Set secondary axis minimum value."""
        self._secondary_min.blockSignals(True)
        self._secondary_min.setText(str(value) if value is not None else "")
        self._secondary_min.blockSignals(False)
    
    def set_secondary_max(self, value: Optional[float]):
        """Set secondary axis maximum value."""
        self._secondary_max.blockSignals(True)
        self._secondary_max.setText(str(value) if value is not None else "")
        self._secondary_max.blockSignals(False)
    
    def update_from_config(self, primary_auto: bool, primary_min: Optional[float],
                           primary_max: Optional[float], secondary_auto: bool,
                           secondary_min: Optional[float], secondary_max: Optional[float]):
        """Update all controls from chart configuration values."""
        self.set_primary_auto(primary_auto)
        self.set_primary_min(primary_min)
        self.set_primary_max(primary_max)
        self.set_secondary_auto(secondary_auto)
        self.set_secondary_min(secondary_min)
        self.set_secondary_max(secondary_max)
    
    def clear(self):
        """Reset all controls to default values."""
        self.update_from_config(True, None, None, True, None, None)
