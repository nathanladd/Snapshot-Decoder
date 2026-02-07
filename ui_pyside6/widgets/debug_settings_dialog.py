"""
Debug Settings Dialog

Provides a user interface for configuring debug logging settings,
including PID interpolation debugging options.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QDialogButtonBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from pid_debug_config import (
    get_pid_debug_setting, set_pid_debug_logging,
    get_log_interval, set_log_interval,
    get_log_on_stop, set_log_on_stop,
    get_position_threshold, set_position_threshold
)


class DebugSettingsDialog(QDialog):
    """Dialog for configuring debug settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Debug Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        # Store original values to detect changes
        self._original_values = {}
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # PID Debug tab
        pid_tab = self._create_pid_debug_tab()
        self.tab_widget.addTab(pid_tab, "PID Debug Logging")
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)
    
    def _create_pid_debug_tab(self) -> QWidget:
        """Create the PID debug logging settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Main PID Debug Settings
        main_group = QGroupBox("PID Debug Logging")
        main_layout = QFormLayout(main_group)
        
        # Enable PID Debug Logging
        self.enable_pid_debug_checkbox = QCheckBox("Enable PID debug logging")
        self.enable_pid_debug_checkbox.setToolTip(
            "Enable detailed logging for PID interpolation and live values updates.\n"
            "This helps diagnose issues with PID values not updating correctly."
        )
        main_layout.addRow("", self.enable_pid_debug_checkbox)
        
        layout.addWidget(main_group)
        
        # Rate Limiting Settings
        rate_group = QGroupBox("Rate Limiting")
        rate_layout = QFormLayout(rate_group)
        
        # Log Interval
        self.log_interval_spinbox = QDoubleSpinBox()
        self.log_interval_spinbox.setRange(0.1, 10.0)
        self.log_interval_spinbox.setSingleStep(0.1)
        self.log_interval_spinbox.setSuffix(" seconds")
        self.log_interval_spinbox.setToolTip(
            "Minimum time between log entries when slider is moving.\n"
            "Higher values reduce log frequency."
        )
        rate_layout.addRow("Log Interval:", self.log_interval_spinbox)
        
        # Log on Stop
        self.log_on_stop_checkbox = QCheckBox("Log when slider stops")
        self.log_on_stop_checkbox.setToolTip(
            "Log the final position when the slider stops moving,\n"
            "even if the time interval hasn't passed."
        )
        rate_layout.addRow("", self.log_on_stop_checkbox)
        
        # Position Threshold
        self.position_threshold_spinbox = QDoubleSpinBox()
        self.position_threshold_spinbox.setRange(0.001, 1.0)
        self.position_threshold_spinbox.setSingleStep(0.001)
        self.position_threshold_spinbox.setDecimals(3)
        self.position_threshold_spinbox.setSuffix(" units")
        self.position_threshold_spinbox.setToolTip(
            "Minimum position change to consider the slider as 'moving'.\n"
            "Smaller values make the system more sensitive to movement."
        )
        rate_layout.addRow("Position Threshold:", self.position_threshold_spinbox)
        
        layout.addWidget(rate_group)
        
        # Information section
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        info_label = QLabel(
            "PID debug logging provides detailed information about:\n"
            "• Data quality issues (NaN values, data types)\n"
            "• Interpolation success/failure for each PID\n"
            "• Live values card update status\n"
            "• Performance and caching information\n\n"
            "Rate limiting prevents log spam when moving the slider continuously."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
    
    def _load_settings(self):
        """Load current settings into the UI."""
        # Store original values
        self._original_values = {
            'enable_pid_debug': get_pid_debug_setting(),
            'log_interval': get_log_interval(),
            'log_on_stop': get_log_on_stop(),
            'position_threshold': get_position_threshold()
        }
        
        # Set UI values
        self.enable_pid_debug_checkbox.setChecked(self._original_values['enable_pid_debug'])
        self.log_interval_spinbox.setValue(self._original_values['log_interval'])
        self.log_on_stop_checkbox.setChecked(self._original_values['log_on_stop'])
        self.position_threshold_spinbox.setValue(self._original_values['position_threshold'])
        
        # Enable/disable rate limiting controls based on main setting
        self._on_enable_pid_debug_changed(self._original_values['enable_pid_debug'])
        
        # Connect signal
        self.enable_pid_debug_checkbox.toggled.connect(self._on_enable_pid_debug_changed)
    
    def _on_enable_pid_debug_changed(self, enabled: bool):
        """Handle enable PID debug checkbox change."""
        # Enable/disable rate limiting controls
        self.log_interval_spinbox.setEnabled(enabled)
        self.log_on_stop_checkbox.setEnabled(enabled)
        self.position_threshold_spinbox.setEnabled(enabled)
    
    def _apply_settings(self):
        """Apply current settings."""
        # Get current values
        enable_pid_debug = self.enable_pid_debug_checkbox.isChecked()
        log_interval = self.log_interval_spinbox.value()
        log_on_stop = self.log_on_stop_checkbox.isChecked()
        position_threshold = self.position_threshold_spinbox.value()
        
        # Apply settings
        set_pid_debug_logging(enable_pid_debug)
        set_log_interval(log_interval)
        set_log_on_stop(log_on_stop)
        set_position_threshold(position_threshold)
        
        # Update original values
        self._original_values = {
            'enable_pid_debug': enable_pid_debug,
            'log_interval': log_interval,
            'log_on_stop': log_on_stop,
            'position_threshold': position_threshold
        }
    
    def accept(self):
        """Accept the dialog (apply settings and close)."""
        self._apply_settings()
        super().accept()
    
    def reject(self):
        """Reject the dialog (restore original settings and close)."""
        # Restore original settings
        set_pid_debug_logging(self._original_values['enable_pid_debug'])
        set_log_interval(self._original_values['log_interval'])
        set_log_on_stop(self._original_values['log_on_stop'])
        set_position_threshold(self._original_values['position_threshold'])
        
        super().reject()
    
    def has_changes(self) -> bool:
        """Check if settings have been changed."""
        current_values = {
            'enable_pid_debug': self.enable_pid_debug_checkbox.isChecked(),
            'log_interval': self.log_interval_spinbox.value(),
            'log_on_stop': self.log_on_stop_checkbox.isChecked(),
            'position_threshold': self.position_threshold_spinbox.value()
        }
        
        return current_values != self._original_values
