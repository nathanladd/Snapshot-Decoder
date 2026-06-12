"""
Main application window for Snapshot Decoder.

PySide6 implementation with clean controller-based architecture.
"""

import os
import copy
import re
import webbrowser
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot, QEvent, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QProgressDialog, QSplashScreen,
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QLabel, QFrame
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont, QColor

from domain.snapshot import Snapshot
from domain.constants import APP_TITLE
from controllers.app_controller import AppController
from controllers.chart_controller import ChartController
from version import APP_VERSION
from infrastructure import get_logger, log_info, log_error, log_warning, log_debug
from infrastructure.logging_config import set_error_signal

from ui_pyside6.widgets.header_panel import HeaderPanel
from ui_pyside6.widgets.system_panel import SystemPanel
from ui_pyside6.widgets.integrated_pid_widget import IntegratedPidWidget
from ui_pyside6.widgets.chart_widget import ChartWidget
from ui_pyside6.widgets.quick_chart_panel import QuickChartPanel
from ui_pyside6.widgets.data_table_window import DataTableWindow
from ui_pyside6.widgets.expandable_panel import ExpandablePanel
from ui_pyside6.widgets.log_console_dock import LogConsoleDock
from ui_pyside6.widgets.chart_cart_dock import ChartCartDock
from ui_pyside6.widgets.settings import SettingsDialog
from domain.app_settings import app_settings
    

class MainWindow(QMainWindow):
    """Main application window with clean controller architecture."""
    
    # Signal for log_error notifications (will be connected to logging system)
    error_notification = Signal()
    
    def __init__(self):
        super().__init__()
        
        # Set up log_error signal for logging system
        set_error_signal(self.error_notification)
        self.error_notification.connect(self._on_error_logged)
        
        # Initialize logging system
        self.logger = get_logger()
        log_info(f"Starting {APP_TITLE} v{APP_VERSION}")
        
        # Initialize controllers (UI-agnostic business logic)
        self.app_controller = AppController()
        self.chart_controller = ChartController()
        
        # UI state
        self.snapshot: Optional[Snapshot] = None
        self._progress_dialog: Optional[QProgressDialog] = None
        self._is_minimizing: bool = False
        self._update_checkers: list = []
        
        # Setup UI and connect signals
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_log_console()
        self._setup_chart_cart()
        self._connect_signals()
        
        log_info("MainWindow initialized with controller architecture")
        QTimer.singleShot(4000, self._auto_check_updates)
    
    def _connect_signals(self):
        """Connect controller signals to UI slots."""
        # AppController signals
        self.app_controller.snapshot_loaded.connect(self._on_snapshot_loaded)
        self.app_controller.snapshot_load_progress.connect(self._on_load_progress)
        self.app_controller.partial_loading.connect(self._on_partial_loading)
        self.app_controller.error_occurred.connect(self._on_error)
        
        # UI widget signals
        # Note: Widgets will be refactored to emit signals in later Phase 3 tasks
        # For now, we'll use the existing widget methods directly
        
        self.setWindowTitle(f"{APP_TITLE} {APP_VERSION}")
        self.resize(1600, 900)
    
    def changeEvent(self, event):
        """Detect minimize/restore to guard dock visibility sync."""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self._is_minimizing = True
            elif self._is_minimizing:
                self._is_minimizing = False
                # Defer sync until Qt has fully restored the window
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self._sync_view_menu_checks)
        super().changeEvent(event)

    def _setup_ui(self):
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Left panel as dockable widget with expandable functionality
        from ui_pyside6.widgets.expandable_dock import ExpandableDock
        
        self.controls_dock = ExpandableDock("Snapshot Data", self)
        self.controls_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Create content widget for the dockable panel
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        
        # Header panel with system indicators to the right
        header_row = QHBoxLayout()
        header_row.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align entire row to top
        
        self.header_panel = HeaderPanel()
        header_row.addWidget(self.header_panel)
        
        # Connect toolbar signals to existing handler methods
        self.header_panel.open_requested.connect(self._on_open_file_dialog)
        self.header_panel.close_requested.connect(self._on_close_snapshot)
        self.header_panel.raw_data_requested.connect(self._on_show_raw_table)
        self.header_panel.clean_table_requested.connect(self._on_show_clean_table)
        self.header_panel.chart_table_requested.connect(self._on_show_chart_table)
        self.header_panel.help_requested.connect(self._on_show_help_home)
        self.header_panel.file_dropped.connect(self._on_open_file)
        
        self.system_panel = SystemPanel()
        # Vertically center the system panel relative to header panel
        header_row.addWidget(self.system_panel, 0, Qt.AlignmentFlag.AlignVCenter)
        
        left_layout.addLayout(header_row)
        
        # PID selection panel (integrated widget)
        self.pid_panel = IntegratedPidWidget()
        self.pid_panel.pids_changed.connect(self._on_pids_changed)
        left_layout.addWidget(self.pid_panel, stretch=1)
        
        # Set the content widget
        self.controls_dock.set_content_widget(left_content)
        
        # Add dock widget and dock to left side
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.controls_dock)
        self.controls_dock.visibilityChanged.connect(self._on_controls_panel_visibility_changed)
        self.controls_dock.toggleViewAction().toggled.connect(self._on_controls_panel_visibility_changed)
        
        # Right panel (quick charts above chart)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        
        # Top bar with quick charts and logo
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(8)
        
        # Quick chart buttons panel
        self.quick_chart_panel = QuickChartPanel()
        self.quick_chart_panel.chart_requested.connect(self._on_quick_chart_requested)
        top_bar_layout.addWidget(self.quick_chart_panel, stretch=1)
        
        # Logo in top right - scale to match quick chart panel height
        logo_path = os.path.join(os.path.dirname(__file__), "..", "data", "images", "logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            # Scale to 100px height
            scaled_pixmap = pixmap.scaledToHeight(100, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            top_bar_layout.addWidget(logo_label)
        
        right_layout.addWidget(top_bar)
        
        # Chart widget
        self.chart_widget = ChartWidget()
        self.chart_widget.add_to_cart_requested.connect(self.add_current_chart_to_cart)
        self.chart_widget.pop_out_requested.connect(self.pop_out_chart)
        self.chart_widget.quick_iq_requested.connect(self._on_quick_iq_requested)
        self.chart_widget.axis_settings_changed.connect(self._on_axis_settings_changed)
        right_layout.addWidget(self.chart_widget, stretch=1)
        
        main_layout.addWidget(right_panel)
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file_dialog)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self._on_show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        data_menu = view_menu.addMenu("Data Tables")
        
        # Chart menu
        chart_menu = menubar.addMenu("&Chart")
        
        pop_out_action = QAction("&Pop Out Chart", self)
        pop_out_action.setShortcut("Ctrl+P")
        pop_out_action.triggered.connect(self.pop_out_chart)
        chart_menu.addAction(pop_out_action)
        
        raw_table_action = QAction("&Raw Data...", self)
        raw_table_action.triggered.connect(self._on_show_raw_table)
        data_menu.addAction(raw_table_action)
        
        clean_table_action = QAction("&Clean Table...", self)
        clean_table_action.triggered.connect(self._on_show_clean_table)
        data_menu.addAction(clean_table_action)
        
        chart_table_action = QAction("&Chart Table...", self)
        chart_table_action.triggered.connect(self._on_show_chart_table)
        data_menu.addAction(chart_table_action)
        
        view_menu.addSeparator()

        self._controls_panel_action = QAction("&Snapshot Data Panel", self)
        self._controls_panel_action.setCheckable(True)
        self._controls_panel_action.triggered.connect(self._on_toggle_controls_panel)
        view_menu.addAction(self._controls_panel_action)
        
        self._chart_cart_action = QAction("&Chart Cart", self)
        self._chart_cart_action.setCheckable(True)
        self._chart_cart_action.triggered.connect(self._on_toggle_chart_cart)
        view_menu.addAction(self._chart_cart_action)
        
        self._log_console_action = QAction("&Log Console", self)
        self._log_console_action.setCheckable(True)
        self._log_console_action.triggered.connect(self._on_toggle_log_console)
        view_menu.addAction(self._log_console_action)

        view_menu.addSeparator()

        default_view_action = QAction("&Default View", self)
        default_view_action.setShortcut("Ctrl+Shift+D")
        default_view_action.triggered.connect(self._restore_default_layout)
        view_menu.addAction(default_view_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        snapshot_home_action = QAction("Snapshot Decoder Home", self)
        snapshot_home_action.triggered.connect(self._on_snapshot_decoder_home)
        help_menu.addAction(snapshot_home_action)
        
        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self._on_check_for_updates)
        help_menu.addAction(check_updates_action)
        
        help_menu.addSeparator()
        
        help_home_action = QAction("&Help Home", self)
        help_home_action.setShortcut("F1")
        help_home_action.triggered.connect(self._on_show_help_home)
        help_menu.addAction(help_home_action)
        
        seven_step_action = QAction("Seven Step Diagnostic Process", self)
        seven_step_action.triggered.connect(self._on_show_seven_step)
        help_menu.addAction(seven_step_action)
        
        ref_charts_action = QAction("What are Reference Charts?", self)
        ref_charts_action.triggered.connect(self._on_what_are_reference_charts)
        help_menu.addAction(ref_charts_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_show_about)
        help_menu.addAction(about_action)
    
    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready - Open a snapshot file to begin")
    
    @Slot()
    def _on_open_file_dialog(self):
        """Open file dialog and request file load via AppController."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Snapshot File",
            "",
            "Snapshot Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self._on_open_file(file_path)
    
    @Slot(str)
    def _on_open_file(self, file_path: str):
        """Handle file open request via AppController."""
        from pathlib import Path
        
        # Warn user if a snapshot is already loaded
        if self.snapshot is not None:
            reply = QMessageBox.warning(
                self,
                "Opening a new file will clear all current data",
                "All current charts and the chart cart cannot be saved.\n\n"
                "Please complete all PDF exports before opening a new file.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Clear all snapshot state before loading the new file
            self._clear_all_snapshot_state()
        
        # Clear the log console for a fresh start
        if hasattr(self, 'log_console_dock') and self.log_console_dock:
            self.log_console_dock.log_console._clear_console()
        
        log_info(f"Opening file: {Path(file_path).name}")

        # Show progress dialog while the background loader runs
        self._progress_dialog = QProgressDialog("Loading snapshot...", None, 0, 100, self)
        self._progress_dialog.setWindowTitle("Loading")
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setValue(0)

        self.app_controller.load_snapshot(file_path)
    
    @Slot()
    def _on_close_snapshot(self):
        """Handle close snapshot request - reset app to freshly-loaded state."""
        if self.snapshot is None:
            return
        
        reply = QMessageBox.warning(
            self,
            "Close Snapshot",
            "All current charts and the chart cart cannot be saved.\n\n"
            "Please complete all PDF exports before closing.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self._clear_all_snapshot_state()
        
        # Clear the log console
        if hasattr(self, 'log_console_dock') and self.log_console_dock:
            self.log_console_dock.log_console._clear_console()
        
        log_info("Snapshot closed by user")
    
    def _clear_all_snapshot_state(self):
        """Clear all snapshot data from the UI and controller."""
        log_info("Clearing all snapshot state for new file load")
        
        self.snapshot = None
        self.app_controller.clear_snapshot()
        
        self.header_panel.clear()
        self.system_panel.clear()
        self.pid_panel.clear()
        self.quick_chart_panel.clear()
        self.chart_widget.clear()
        self.chart_cart_dock.chart_cart.clear_all()
        
        self.statusbar.showMessage("Ready - Open a snapshot file to begin")
    
    @Slot(object)
    def _on_snapshot_loaded(self, snapshot: Snapshot):
        """Handle successful snapshot load from AppController."""
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        self.snapshot = snapshot
        
        # Update UI with snapshot data
        self.header_panel.set_snapshot(snapshot)
        self.system_panel.set_snapshot(snapshot)
        self.pid_panel.set_snapshot(snapshot)
        self.quick_chart_panel.set_snapshot(snapshot)
        self.chart_widget.clear()
        
        self.statusbar.showMessage(
            f"Loaded: {snapshot.file_name} | "
            f"Type: {snapshot.snapshot_type.name} | "
            f"Hours: {snapshot.hours}"
        )
        
        log_info(f"UI updated with loaded snapshot: {snapshot.snapshot_type}")
    
    @Slot(int, str)
    def _on_load_progress(self, percent: int, message: str):
        """Handle load progress from AppController."""
        dialog = self._progress_dialog
        if dialog:
            dialog.setValue(percent)
            dialog.setLabelText(message)
    
    @Slot(str)
    def _on_error(self, log_error_msg: str):
        """Handle log_error from AppController."""
        if self._progress_dialog:
            self._progress_dialog.close()
        
        QMessageBox.critical(self, "Error", log_error_msg)
        self.statusbar.showMessage("Error occurred")
        log_error(f"Error displayed to user: {log_error_msg}")
    
    @Slot()
    def _on_error_logged(self):
        """Handle log_error notification from logging system - show and focus logger."""
        if not self.log_console_dock.isVisible():
            self.log_console_dock.show()
        self.log_console_dock.raise_()
        self.log_console_dock.setFocus()
    
    @Slot(object)
    def _on_partial_loading(self, snapshot: Snapshot):
        """Handle partial snapshot loading when identification fails."""
        if self._progress_dialog:
            self._progress_dialog.close()
        
        # Load the raw snapshot for inspection but don't populate widgets
        self.snapshot = snapshot
        log_info(f"Raw snapshot loaded for inspection (identification failed): {snapshot.file_path}")
        
        # Show user-friendly message
        QMessageBox.warning(
            self, 
            "Low Confidence Snapshot", 
            f"The snapshot file was loaded but could not be identified with sufficient confidence.\n\n"
            f"File: {os.path.basename(snapshot.file_path)}\n"
            f"Reason: Snapshot type detection confidence below 80%\n\n"
            f"The raw data is available for inspection in the Data Tables menu.\n"
            f"Check the log console for detailed debugging log_information."
        )
        
        # Show logger automatically
        if not self.log_console_dock.isVisible():
            self.log_console_dock.show()
        self.log_console_dock.raise_()
        self.log_console_dock.setFocus()
        
        self.statusbar.showMessage("Raw data loaded (identification failed)")
        log_info("Raw snapshot loaded for inspection, widgets not populated due to identification failure")
    
    @Slot(str)
    def _on_quick_chart_requested(self, action_id: str):
        """Handle quick chart request via AppController."""
        if not self.app_controller.has_snapshot():
            log_warning("Quick chart requested but no snapshot loaded")
            return
        
        log_info(f"Quick chart requested: {action_id}")
        
        # Handle special reference PDF generation
        if action_id == "REF_GENERATE_PDF":
            self._generate_reference_pdf()
            return
        
        self.chart_widget.plot_quick_chart(self.app_controller.get_snapshot(), action_id)
        
        # Sync PID panel with quick chart's PIDs
        primary_pids = self.chart_widget.get_current_primary_pids()
        secondary_pids = self.chart_widget.get_current_secondary_pids()
        self.pid_panel.set_pids(primary_pids, secondary_pids, emit_signal=False)
        
        # Update PID panel colors to match quick chart
        config = self.chart_widget.get_current_config()
        if config:
            self.pid_panel.update_chart_colors(config)
        
        # Update axis controls from the chart config
        self._update_axis_controls_from_config()
    
    @Slot()
    def _on_pids_changed(self):
        """Handle PID selection changes."""
        if not self.app_controller.has_snapshot():
            return
        
        # Get current PIDs from panel
        primary_pids = self.pid_panel.get_primary_pids()
        secondary_pids = self.pid_panel.get_secondary_pids()
        
        # Update chart if we have PIDs, otherwise clear chart
        if primary_pids or secondary_pids:
            self.chart_widget.update_chart(
                self.app_controller.get_snapshot(),
                primary_pids,
                secondary_pids,
                self._get_axis_settings()
            )
        else:
            # Clear chart when no PIDs selected
            self.chart_widget.clear()
        
        # Update PID panel colors
        config = self.chart_widget.get_current_config()
        if config:
            self.pid_panel.update_chart_colors(config)
        else:
            # Reset colors when no chart
            self.pid_panel.update_chart_colors(None)
    
    @Slot(list, list)
    def _on_pid_selection_changed(self, primary_pids: list, secondary_pids: list):
        """Handle PID selection changes (alternative handler)."""
        # This handler is not used but kept for compatibility
        self._on_pids_changed()
    
    @Slot(object)
    def _on_chart_config_changed(self, config):
        """Handle chart configuration changes."""
        if config and self.app_controller.has_snapshot():
            # Re-render chart with new config
            try:
                self.chart_controller.render(config, self.chart_widget.figure)
                self.chart_widget.canvas.draw()
                log_debug("Chart re-rendered from config change")
            except Exception as e:
                log_error(f"Failed to re-render chart: {str(e)}")
                self.app_controller.error_occurred.emit(f"Chart rendering failed: {str(e)}")
            self.chart_widget.clear_axis_controls()
    
    @Slot()
    def _on_axis_settings_changed(self):
        """Handle axis settings changes from the controls panel."""
        if not self.app_controller.has_snapshot():
            return
        
        primary_pids = self.pid_panel.get_primary_pids()
        secondary_pids = self.pid_panel.get_secondary_pids()
        
        if primary_pids or secondary_pids:
            self.chart_widget.update_chart(
                self.snapshot, primary_pids, secondary_pids,
                axis_settings=self._get_axis_settings()
            )
            # Update PID panel colors to match chart
            config = self.chart_widget.get_current_config()
            if config:
                self.pid_panel.update_chart_colors(config)
        else:
            # No PIDs selected, clear the chart
            self.chart_widget.clear()
            # Reset PID panel colors
            self.pid_panel.update_chart_colors(None)
    
    def _get_axis_settings(self) -> dict:
        """Get current axis settings from chart toolbar controls."""
        return self.chart_widget.get_axis_settings()
    
    def _update_axis_controls_from_chart(self):
        """Update axis controls with current chart axis limits (auto-computed)."""
        limits = self.chart_widget.get_current_axis_limits()
        if limits:
            current_settings = self._get_axis_settings()
            self.chart_widget.update_axis_controls(
                primary_auto=current_settings.get('primary_auto', True),
                primary_min=limits.get('primary_min'),
                primary_max=limits.get('primary_max'),
                secondary_auto=current_settings.get('secondary_auto', True),
                secondary_min=limits.get('secondary_min'),
                secondary_max=limits.get('secondary_max'),
            )
    
    def _update_axis_controls_from_config(self):
        """Update axis controls from the current chart configuration."""
        config = self.chart_widget.get_current_config()
        if not config:
            return
        
        # Get limits from rendered chart
        limits = self.chart_widget.get_current_axis_limits()
        
        # Use config's auto_scale settings and either config values or rendered limits
        primary_auto = config.primary_axis.auto_scale
        secondary_auto = config.secondary_axis.auto_scale
        
        if primary_auto and limits:
            primary_min = limits.get('primary_min')
            primary_max = limits.get('primary_max')
        else:
            primary_min = config.primary_axis.min_value
            primary_max = config.primary_axis.max_value
        
        if secondary_auto and limits:
            secondary_min = limits.get('secondary_min')
            secondary_max = limits.get('secondary_max')
        else:
            secondary_min = config.secondary_axis.min_value
            secondary_max = config.secondary_axis.max_value
        
        self.chart_widget.update_axis_controls(
            primary_auto=primary_auto,
            primary_min=primary_min,
            primary_max=primary_max,
            secondary_auto=secondary_auto,
            secondary_min=secondary_min,
            secondary_max=secondary_max,
        )
    
    @Slot(str)
    def _on_quick_chart_requested(self, action_id: str):
        """Handle quick chart button click."""
        if not self.snapshot:
            return
        
        # Handle special reference PDF generation
        if action_id == "REF_GENERATE_PDF":
            self._generate_reference_pdf()
            return
        
        self.chart_widget.plot_quick_chart(self.app_controller.get_snapshot(), action_id)
        
        # Sync PID panel with quick chart's PIDs
        primary_pids = self.chart_widget.get_current_primary_pids()
        secondary_pids = self.chart_widget.get_current_secondary_pids()
        self.pid_panel.set_pids(primary_pids, secondary_pids, emit_signal=False)
        
        # Update PID panel colors to match quick chart
        config = self.chart_widget.get_current_config()
        if config:
            self.pid_panel.update_chart_colors(config)
        
        # Update axis controls from the chart config
        self._update_axis_controls_from_config()
    
    @Slot()
    def _on_show_raw_table(self):
        """Show the raw data table window."""
        if not self.snapshot:
            QMessageBox.information(self, "No Data", "Please load a snapshot first.")
            return
        
        # Create and show raw data table window
        data_table = DataTableWindow(
            self,
            self.snapshot.raw_table,
            self.snapshot.file_path,
            "Raw Data"
        )
        data_table.show()
    
    @Slot()
    def _on_show_clean_table(self):
        """Show the clean data table window."""
        if not self.snapshot:
            QMessageBox.information(self, "No Data", "Please load a snapshot first.")
            return
        
        # Create and show clean data table window
        data_table = DataTableWindow(
            self,
            self.snapshot.snapshot,
            self.snapshot.file_path,
            "Clean Table"
        )
        data_table.show()
    
    @Slot()
    def _on_show_chart_table(self):
        """Show the chart table window."""
        if not self.snapshot:
            QMessageBox.information(self, "No Data", "Please load a snapshot first.")
            return
        
        # Get current chart PIDs
        primary_pids = self.chart_widget.get_current_primary_pids()
        secondary_pids = self.chart_widget.get_current_secondary_pids()
        
        # Union of primary and secondary (no duplicates, preserve order)
        selected_pids = list(dict.fromkeys(primary_pids + secondary_pids))
        
        if not selected_pids:
            QMessageBox.information(self, "No Chart Data", "Please create a chart first to show the chart table.")
            return
        
        # Create dataframe with only chart PIDs
        chart_df = self.snapshot.snapshot[selected_pids].copy()
        
        # Create and show chart table window
        data_table = DataTableWindow(
            self,
            chart_df,
            self.snapshot.file_path,
            "Chart Table"
        )
        data_table.show()
    
    @Slot()
    def _on_show_data_table(self):
        """Show the data table window (legacy - redirects to clean table)."""
        self._on_show_clean_table()
    
    @Slot()
    def _on_show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_TITLE}",
            f"{APP_TITLE} {APP_VERSION}\n\n"
            "A tool for analyzing engine snapshot data.\n\n"
            "Nathan Ladd\n"
            "Service Trainer\n"
            "nladd@bobcatoftherockies.com"
        )
    
    def _setup_log_console(self):
        """Setup the log console dock widget."""
        self.log_console_dock = LogConsoleDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_console_dock)
        self.log_console_dock.visibilityChanged.connect(self._on_log_console_visibility_changed)
        self.log_console_dock.toggleViewAction().toggled.connect(self._on_log_console_visibility_changed)
        
        # Hide by default (user can show via menu)
        self.log_console_dock.hide()
    
    def _setup_chart_cart(self):
        """Setup the chart cart dock widget."""
        self.chart_cart_dock = ChartCartDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.chart_cart_dock)
        
        # Visible by default
        self.chart_cart_dock.show()
        
        # Sync menu check state when dock visibility changes
        self.chart_cart_dock.visibilityChanged.connect(self._on_chart_cart_visibility_changed)
        self.chart_cart_dock.toggleViewAction().toggled.connect(self._on_chart_cart_visibility_changed)
        
        # Tab the chart cart and log console together in the right dock area
        self.tabifyDockWidget(self.chart_cart_dock, self.log_console_dock)
        
        # Listen for cart changes to sync PID panel
        self.chart_cart_dock.chart_cart.cart_changed.connect(self._on_chart_cart_changed)
    
    @Slot(bool)
    def _on_toggle_log_console(self, enabled: bool):
        """Enable/disable the log console dock from the View menu."""
        if self._is_minimizing:
            return
        self.log_console_dock.setVisible(enabled)
        if enabled:
            self.log_console_dock.raise_()

    @Slot(bool)
    def _on_toggle_controls_panel(self, enabled: bool):
        """Enable/disable the controls panel dock from the View menu."""
        if self._is_minimizing:
            return
        self.controls_dock.setVisible(enabled)
        if enabled:
            self.controls_dock.raise_()
    
    @Slot(bool)
    def _on_toggle_chart_cart(self, enabled: bool):
        """Enable/disable the chart cart dock from the View menu."""
        if self._is_minimizing:
            return
        self.chart_cart_dock.setVisible(enabled)
        if enabled:
            self.chart_cart_dock.raise_()

    def _sync_view_menu_checks(self):
        """Sync View menu checks with dock enabled states (independent of tab focus)."""
        if self._is_minimizing:
            return
        if hasattr(self, 'controls_dock') and hasattr(self, '_controls_panel_action'):
            self._controls_panel_action.setChecked(self.controls_dock.isVisible())
        if hasattr(self, 'chart_cart_dock') and hasattr(self, '_chart_cart_action'):
            self._chart_cart_action.setChecked(self.chart_cart_dock.isVisible())
        if hasattr(self, 'log_console_dock') and hasattr(self, '_log_console_action'):
            self._log_console_action.setChecked(self.log_console_dock.isVisible())

    @Slot(bool)
    def _on_controls_panel_visibility_changed(self, _visible: bool):
        """Sync menu check state when controls panel dock state changes."""
        self._sync_view_menu_checks()

    @Slot(bool)
    def _on_log_console_visibility_changed(self, _visible: bool):
        """Sync menu check state when log console dock state changes."""
        self._sync_view_menu_checks()

    @Slot(bool)
    def _on_chart_cart_visibility_changed(self, _visible: bool):
        """Sync menu check state with chart cart dock visibility."""
        self._sync_view_menu_checks()
    
    def add_current_chart_to_cart(self):
        """Add the current chart configuration to the chart cart."""
        config = self.chart_widget.get_current_config()
        if not config:
            QMessageBox.information(self, "No Chart", "Create a chart first to add it to the cart.")
            return
        
        config_copy = copy.deepcopy(config)
        self.chart_cart_dock.add_config(config_copy)
        if not self.chart_cart_dock.isVisible():
            self.chart_cart_dock.show()
        self.chart_cart_dock.raise_()
        log_info(f"Added chart to cart: {config.title}")
    
    
    @Slot()
    def _restore_default_layout(self):
        """Reset all dock widgets to their default positions and visibility."""
        docks = [
            self.controls_dock,
            self.chart_cart_dock,
            self.log_console_dock,
        ]

        # Unfloat and remove all docks
        for dock in docks:
            dock.setFloating(False)
            self.removeDockWidget(dock)

        # Re-add to default areas
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.controls_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.chart_cart_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_console_dock)

        # Re-tab the right-side docks
        self.tabifyDockWidget(self.chart_cart_dock, self.log_console_dock)

        # Set default visibility
        self.controls_dock.show()
        self.chart_cart_dock.show()
        self.log_console_dock.hide()

        # Expand controls dock if collapsed
        if hasattr(self.controls_dock, 'is_expanded') and not self.controls_dock.is_expanded():
            self.controls_dock.expand()

        # Raise chart cart as the active right-side tab
        self.chart_cart_dock.raise_()

        self._sync_view_menu_checks()

    @Slot()
    def _on_snapshot_decoder_home(self):
        """Open Snapshot Decoder Home in web browser."""
        webbrowser.open("https://berrycompanies.sharepoint.com/sites/BOTRServiceSupport/Snapshot_Decoder")
    
    @Slot()
    def _on_check_for_updates(self):
        self._run_update_check(silent_if_current=False)

    def _auto_check_updates(self) -> None:
        if not app_settings._data.get("auto_check_updates", True):
            return
        self._run_update_check(silent_if_current=True)

    def _run_update_check(self, *, silent_if_current: bool) -> None:
        from ui_pyside6.widgets.update_checker import UpdateChecker
        checker = UpdateChecker()
        self._update_checkers.append(checker)

        def _cleanup() -> None:
            try:
                self._update_checkers.remove(checker)
            except ValueError:
                pass
            checker.deleteLater()

        checker.update_available.connect(self._on_update_available)
        if not silent_if_current:
            checker.up_to_date.connect(
                lambda: QMessageBox.information(
                    self, "No Updates", f"Snapshot Decoder v{APP_VERSION} is up to date."
                )
            )
        checker.check_failed.connect(
            lambda msg: QMessageBox.warning(self, "Update Check Failed", msg)
        )
        checker.finished.connect(_cleanup)
        checker.start()

    def _on_update_available(self, ver: str, notes: str, url: str, sha: str) -> None:
        from ui_pyside6.widgets.update_dialog import UpdateDialog
        dlg = UpdateDialog(ver, notes, url, sha, parent=self)
        dlg.exec()
    
    @Slot()
    def _on_what_are_reference_charts(self):
        """Open the Reference Charts help page in the default browser."""
        webbrowser.open(
            "https://berrycompanies.sharepoint.com/:u:/r/sites/BOTRServiceSupport/Snapshot_Decoder/SitePages/Reference-Snapshot.aspx?csf=1&web=1&e=HyLXbK"
        )
    
    @Slot()
    def _on_show_help_home(self):
        webbrowser.open("https://decoder.rudi-hq.com/")

    @Slot()
    def _on_show_seven_step(self):
        webbrowser.open("https://decoder.rudi-hq.com/seven_step.html")

    def _build_quick_iq_url(self, chart_title: str) -> str:
        """Build a Quick IQ URL from chart title."""
        slug = chart_title.strip()
        slug = slug.replace("&", " and ")
        slug = slug.replace("/", "-")
        slug = re.sub(r"\s+", "-", slug)
        slug = re.sub(r"[^A-Za-z0-9\-]", "", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")

        return f"https://decoder.rudi-hq.com/quick_iq/{slug}.html"

    @Slot(str)
    def _on_quick_iq_requested(self, chart_title: str):
        """Open Quick IQ page in the default browser."""
        if not chart_title:
            QMessageBox.information(self, "Quick IQ", "Create or select a chart first.")
            return

        url = self._build_quick_iq_url(chart_title)
        webbrowser.open(url)
    
    @Slot()
    def _on_chart_cart_changed(self):
        """Handle chart cart changes - sync PID panel when cart is cleared."""
        count = self.chart_cart_dock.chart_cart.get_config_count()
        if count == 0:
            # Cart is empty - clear PID panel checkboxes
            self.pid_panel.set_pids([], [], emit_signal=False)
    
    @Slot()
    def pop_out_chart(self):
        """Open the current chart in a separate window."""
        config = self.chart_widget.get_current_config()
        if not config:
            QMessageBox.information(self, "No Chart", "Configure a chart first to pop it out.")
            return
        
        # Capture current axis limits from the chart (after pan/zoom)
        # Note: This would need access to the chart's axes - for now use config as-is
        # In a full implementation, we'd need to get the current axis limits
        
        # Open pop-out window with current config and cart
        from ui_pyside6.widgets.chart_popout_window import ChartPopoutWindow
        popup = ChartPopoutWindow(self, config, chart_cart=self.chart_cart_dock.chart_cart)
        popup.quick_iq_requested.connect(self._on_quick_iq_requested)
        popup.show()
    
    @Slot()
    def _on_show_settings(self):
        """Show the unified settings dialog."""
        original = app_settings.get_all()
        dialog = SettingsDialog(self)
        
        if dialog.exec():
            # Settings were accepted – propagate debug/logging changes to live widgets
            new = app_settings.get_all()
            if any(original.get(k) != new.get(k)
                   for k in ('enable_pid_debug', 'log_interval', 'log_on_stop', 'position_threshold')):
                debug_settings = {
                    'enable': new['enable_pid_debug'],
                    'interval': new['log_interval'],
                    'log_on_stop': new['log_on_stop'],
                    'threshold': new['position_threshold'],
                }
                if hasattr(self.chart_widget, '_live_values_widget'):
                    self.chart_widget._live_values_widget.update_settings(debug_settings)

    
    def _generate_reference_pdf(self):
        """Generate reference PDF using V2 architecture."""
        from domain.quick_charts.reference_builder import ReferenceChartBuilder
        from domain.snaptypes import SnapType
        
        snapshot = self.app_controller.get_snapshot()
        if not snapshot:
            log_warning("No snapshot available for reference PDF generation")
            return
        
        # Create reference builder
        builder = ReferenceChartBuilder(snapshot, self)
        
        # Generate PDF
        file_path = builder.create_reference_pdf(snapshot.snapshot_type)
        if file_path:
            # Show success message
            QMessageBox.information(
                self,
                "Reference PDF Generated",
                f"Reference charts PDF saved to:\n{file_path}"
            )
            log_info(f"Reference PDF generated: {file_path}")
        else:
            log_info("Reference PDF generation cancelled or failed")
