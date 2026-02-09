"""
Settings Dialog for Snapshot Decoder (PySide6)

Unified tabbed dialog for configuring chart appearance and
logging preferences.  All values are persisted to settings.json
via the AppSettings singleton.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QDialogButtonBox, QTabWidget, QWidget, QMessageBox
)
from PySide6.QtCore import Qt

from domain.app_settings import app_settings


class SettingsDialog(QDialog):
    """
    Unified settings dialog with tabs for Chart Appearance and Logging.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 480)

        # Snapshot of current values so we can cancel cleanly
        self._original = app_settings.get_all()

        self._setup_ui()
        self._load_settings()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tab 1 – Chart Appearance
        self.tab_widget.addTab(self._create_chart_tab(), "Chart Appearance")

        # Tab 2 – Logging
        self.tab_widget.addTab(self._create_logging_tab(), "Logging")

        # Buttons
        btn_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        btn_layout.addWidget(button_box)

        layout.addLayout(btn_layout)

    # ---- Chart Appearance tab ----
    def _create_chart_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Chart Appearance")
        form = QFormLayout(group)

        # Legend Font Size
        self.legend_font_spin = QSpinBox()
        self.legend_font_spin.setRange(6, 20)
        self.legend_font_spin.setSuffix(" pt")
        self.legend_font_spin.setToolTip("Font size for chart legends (6-20 points)")
        form.addRow("Legend Font Size:", self.legend_font_spin)

        # Line Width
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.5, 5.0)
        self.line_width_spin.setSingleStep(0.5)
        self.line_width_spin.setToolTip("Thickness of chart data lines (0.5-5.0)")
        form.addRow("Line Width:", self.line_width_spin)

        # Grid Line Width
        self.grid_linewidth_spin = QDoubleSpinBox()
        self.grid_linewidth_spin.setRange(0.1, 2.0)
        self.grid_linewidth_spin.setSingleStep(0.1)
        self.grid_linewidth_spin.setToolTip("Thickness of grid lines (0.1-2.0)")
        form.addRow("Grid Line Width:", self.grid_linewidth_spin)

        # Marker Size
        self.marker_size_spin = QDoubleSpinBox()
        self.marker_size_spin.setRange(2.0, 15.0)
        self.marker_size_spin.setSingleStep(0.5)
        self.marker_size_spin.setToolTip("Size of data point markers (2.0-15.0)")
        form.addRow("Marker Size:", self.marker_size_spin)

        layout.addWidget(group)
        layout.addStretch()
        return widget

    # ---- Logging tab ----
    def _create_logging_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # PID Debug Logging group
        main_group = QGroupBox("PID Debug Logging")
        main_form = QFormLayout(main_group)

        self.enable_pid_debug_cb = QCheckBox("Enable PID debug logging")
        self.enable_pid_debug_cb.setToolTip(
            "Enable detailed logging for PID interpolation and live values updates.\n"
            "This helps diagnose issues with PID values not updating correctly."
        )
        main_form.addRow("", self.enable_pid_debug_cb)
        layout.addWidget(main_group)

        # Rate Limiting group
        rate_group = QGroupBox("Rate Limiting")
        rate_form = QFormLayout(rate_group)

        self.log_interval_spin = QDoubleSpinBox()
        self.log_interval_spin.setRange(0.1, 10.0)
        self.log_interval_spin.setSingleStep(0.1)
        self.log_interval_spin.setSuffix(" seconds")
        self.log_interval_spin.setToolTip(
            "Minimum time between log entries when the slider is moving."
        )
        rate_form.addRow("Log Interval:", self.log_interval_spin)

        self.log_on_stop_cb = QCheckBox("Log when slider stops")
        self.log_on_stop_cb.setToolTip(
            "Log the final position when the slider stops moving,\n"
            "even if the time interval hasn't passed."
        )
        rate_form.addRow("", self.log_on_stop_cb)

        self.position_threshold_spin = QDoubleSpinBox()
        self.position_threshold_spin.setRange(0.001, 1.0)
        self.position_threshold_spin.setSingleStep(0.001)
        self.position_threshold_spin.setDecimals(3)
        self.position_threshold_spin.setSuffix(" units")
        self.position_threshold_spin.setToolTip(
            "Minimum position change to consider the slider as 'moving'."
        )
        rate_form.addRow("Position Threshold:", self.position_threshold_spin)

        layout.addWidget(rate_group)

        # Info
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(
            "PID debug logging provides detailed information about:\n"
            "  - Data quality issues (NaN values, data types)\n"
            "  - Interpolation success/failure for each PID\n"
            "  - Live values card update status\n"
            "  - Performance and caching information\n\n"
            "Rate limiting prevents log spam when moving the slider continuously."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)

        # Toggle rate-limit controls when debug checkbox changes
        self.enable_pid_debug_cb.toggled.connect(self._on_debug_toggled)

        layout.addStretch()
        return widget

    # ------------------------------------------------------------------
    # Load / Apply / Reset
    # ------------------------------------------------------------------
    def _load_settings(self):
        """Populate UI controls from AppSettings."""
        # Chart
        self.legend_font_spin.setValue(app_settings.legend_font_size)
        self.line_width_spin.setValue(app_settings.line_width)
        self.grid_linewidth_spin.setValue(app_settings.grid_linewidth)
        self.marker_size_spin.setValue(app_settings.marker_size)
        # Logging
        self.enable_pid_debug_cb.setChecked(app_settings.enable_pid_debug)
        self.log_interval_spin.setValue(app_settings.log_interval)
        self.log_on_stop_cb.setChecked(app_settings.log_on_stop)
        self.position_threshold_spin.setValue(app_settings.position_threshold)
        # Sync enabled state
        self._on_debug_toggled(app_settings.enable_pid_debug)

    def _apply_settings(self):
        """Write UI values into AppSettings and save to JSON."""
        # Chart
        app_settings.legend_font_size = self.legend_font_spin.value()
        app_settings.line_width = self.line_width_spin.value()
        app_settings.grid_linewidth = self.grid_linewidth_spin.value()
        app_settings.marker_size = self.marker_size_spin.value()
        # Logging
        app_settings.enable_pid_debug = self.enable_pid_debug_cb.isChecked()
        app_settings.log_interval = self.log_interval_spin.value()
        app_settings.log_on_stop = self.log_on_stop_cb.isChecked()
        app_settings.position_threshold = self.position_threshold_spin.value()
        # Persist
        app_settings.save()

    def _on_debug_toggled(self, enabled: bool):
        self.log_interval_spin.setEnabled(enabled)
        self.log_on_stop_cb.setEnabled(enabled)
        self.position_threshold_spin.setEnabled(enabled)

    def _on_reset(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            app_settings.reset_to_defaults()
            self._load_settings()

    # ------------------------------------------------------------------
    # Accept / Reject overrides
    # ------------------------------------------------------------------
    def accept(self):
        self._apply_settings()
        super().accept()

    def reject(self):
        # Restore the snapshot we took when the dialog opened
        app_settings.set_many(self._original)
        app_settings.save()
        super().reject()
