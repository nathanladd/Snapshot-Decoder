"""
Main application window for Snapshot Decoder.

PySide6 implementation with clean controller-based architecture.
"""

import os
import copy
import webbrowser
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QProgressDialog, QMessageBox,
    QFileDialog, QLabel, QFrame
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QIcon, QPixmap

from domain.snapshot import Snapshot
from domain.constants import APP_TITLE
from controllers.app_controller import AppController
from controllers.chart_controller import ChartController
from version import APP_VERSION
from infrastructure import get_logger, info, error, warning, debug

from ui_pyside6.widgets.header_panel import HeaderPanel
from ui_pyside6.widgets.system_panel import SystemPanel
from ui_pyside6.widgets.integrated_pid_widget import IntegratedPidWidget
from ui_pyside6.widgets.axis_controls_panel import AxisControlsPanel
from ui_pyside6.widgets.chart_widget import ChartWidget
from ui_pyside6.widgets.quick_chart_panel import QuickChartPanel
from ui_pyside6.widgets.data_table_window import DataTableWindow
from ui_pyside6.widgets.expandable_panel import ExpandablePanel
from ui_pyside6.widgets.log_console_dock import LogConsoleDock
from ui_pyside6.widgets.chart_cart_dock import ChartCartDock
from ui_pyside6.widgets.help_browser_dock import HelpBrowserDock
from ui_pyside6.widgets.help_tooltip import HelpEventFilter
from ui_pyside6.widgets.debug_settings_dialog import DebugSettingsDialog
    

class MainWindow(QMainWindow):
    """Main application window with clean controller architecture."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize logging system
        self.logger = get_logger()
        info(f"Starting {APP_TITLE} v{APP_VERSION}")
        
        # Initialize controllers (UI-agnostic business logic)
        self.app_controller = AppController()
        self.chart_controller = ChartController()
        
        # UI state
        self.snapshot: Optional[Snapshot] = None
        self._progress_dialog: Optional[QProgressDialog] = None
        
        # Setup UI and connect signals
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_log_console()
        self._setup_chart_cart()
        self._setup_help_browser()
        self._setup_help_tooltips()
        self._connect_signals()
        
        info("MainWindow initialized with controller architecture")
    
    def _connect_signals(self):
        """Connect controller signals to UI slots."""
        # AppController signals
        self.app_controller.snapshot_loaded.connect(self._on_snapshot_loaded)
        self.app_controller.snapshot_load_progress.connect(self._on_load_progress)
        self.app_controller.error_occurred.connect(self._on_error)
        
        # UI widget signals
        # Note: Widgets will be refactored to emit signals in later Phase 3 tasks
        # For now, we'll use the existing widget methods directly
        
        self.setWindowTitle(f"{APP_TITLE} {APP_VERSION}")
        self.resize(1600, 900)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Left panel as dockable widget with expandable functionality
        from ui_pyside6.widgets.expandable_dock import ExpandableDock
        
        left_dock = ExpandableDock("Controls", self)
        left_dock.setAllowedAreas(
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
        self.header_panel.raw_data_requested.connect(self._on_show_raw_table)
        self.header_panel.clean_table_requested.connect(self._on_show_clean_table)
        self.header_panel.chart_table_requested.connect(self._on_show_chart_table)
        self.header_panel.help_requested.connect(self._on_show_help_home)
        
        self.system_panel = SystemPanel()
        # Vertically center the system panel relative to header panel
        header_row.addWidget(self.system_panel, 0, Qt.AlignmentFlag.AlignVCenter)
        
        left_layout.addLayout(header_row)
        
        # PID selection panel (integrated widget)
        self.pid_panel = IntegratedPidWidget()
        self.pid_panel.pids_changed.connect(self._on_pids_changed)
        left_layout.addWidget(self.pid_panel, stretch=1)
        
        # Axis controls panel
        self.axis_controls_panel = AxisControlsPanel()
        self.axis_controls_panel.settings_changed.connect(self._on_axis_settings_changed)
        left_layout.addWidget(self.axis_controls_panel)
        
        # Set the content widget
        left_dock.set_content_widget(left_content)
        
        # Add dock widget and dock to left side
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
        
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
        
        self._chart_cart_action = QAction("&Chart Cart", self)
        self._chart_cart_action.setCheckable(True)
        self._chart_cart_action.setChecked(True)
        self._chart_cart_action.triggered.connect(self._on_toggle_chart_cart)
        view_menu.addAction(self._chart_cart_action)
        
        self._help_browser_action = QAction("&Help Browser", self)
        self._help_browser_action.setCheckable(True)
        self._help_browser_action.triggered.connect(self._on_toggle_help_browser)
        view_menu.addAction(self._help_browser_action)
        
        self._log_console_action = QAction("&Log Console", self)
        self._log_console_action.setCheckable(True)
        self._log_console_action.triggered.connect(self._on_toggle_log_console)
        view_menu.addAction(self._log_console_action)
        
        # Debug menu
        debug_menu = menubar.addMenu("&Debug")
        
        debug_settings_action = QAction("&Debug Settings...", self)
        debug_settings_action.triggered.connect(self._on_show_debug_settings)
        debug_menu.addAction(debug_settings_action)
        
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
        info(f"Opening file: {Path(file_path).name}")
        self.app_controller.load_snapshot(file_path)
    
    @Slot(object)
    def _on_snapshot_loaded(self, snapshot: Snapshot):
        """Handle successful snapshot load from AppController."""
        self.snapshot = snapshot
        
        # Update UI with snapshot data
        self.header_panel.set_snapshot(snapshot)
        self.system_panel.set_snapshot(snapshot)
        self.pid_panel.set_snapshot(snapshot)
        self.quick_chart_panel.set_snapshot_type(snapshot.snapshot_type)
        self.chart_widget.clear()
        
        self.statusbar.showMessage(
            f"Loaded: {snapshot.file_name} | "
            f"Type: {snapshot.snapshot_type.name} | "
            f"Hours: {snapshot.hours}"
        )
        
        info(f"UI updated with loaded snapshot: {snapshot.snapshot_type}")
    
    @Slot(int, str)
    def _on_load_progress(self, percent: int, message: str):
        """Handle load progress from AppController."""
        if self._progress_dialog:
            self._progress_dialog.setValue(percent)
            self._progress_dialog.setLabelText(message)
    
    @Slot(str)
    def _on_error(self, error_msg: str):
        """Handle error from AppController."""
        if self._progress_dialog:
            self._progress_dialog.close()
        
        QMessageBox.critical(self, "Error", error_msg)
        self.statusbar.showMessage("Error occurred")
        error(f"Error displayed to user: {error_msg}")
    
    @Slot(str)
    def _on_quick_chart_requested(self, action_id: str):
        """Handle quick chart request via AppController."""
        if not self.app_controller.has_snapshot():
            warning("Quick chart requested but no snapshot loaded")
            return
        
        info(f"Quick chart requested: {action_id}")
        
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
                self.axis_controls_panel.get_axis_settings()
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
                debug("Chart re-rendered from config change")
            except Exception as e:
                error(f"Failed to re-render chart: {str(e)}")
                self.app_controller.error_occurred.emit(f"Chart rendering failed: {str(e)}")
            self.axis_controls_panel.clear()
    
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
        """Get current axis settings from controls panel."""
        return {
            'primary_auto': self.axis_controls_panel.is_primary_auto(),
            'primary_min': self.axis_controls_panel.get_primary_min(),
            'primary_max': self.axis_controls_panel.get_primary_max(),
            'secondary_auto': self.axis_controls_panel.is_secondary_auto(),
            'secondary_min': self.axis_controls_panel.get_secondary_min(),
            'secondary_max': self.axis_controls_panel.get_secondary_max(),
        }
    
    def _update_axis_controls_from_chart(self):
        """Update axis controls with current chart axis limits (auto-computed)."""
        limits = self.chart_widget.get_current_axis_limits()
        if limits:
            self.axis_controls_panel.update_from_config(
                primary_auto=self.axis_controls_panel.is_primary_auto(),
                primary_min=limits.get('primary_min'),
                primary_max=limits.get('primary_max'),
                secondary_auto=self.axis_controls_panel.is_secondary_auto(),
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
        
        self.axis_controls_panel.update_from_config(
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
            "© 2024-2025"
        )
    
    def _setup_log_console(self):
        """Setup the log console dock widget."""
        self.log_console_dock = LogConsoleDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_console_dock)
        
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
        
        # Listen for cart changes to sync PID panel
        self.chart_cart_dock.chart_cart.cart_changed.connect(self._on_chart_cart_changed)
    
    def _setup_help_browser(self):
        """Setup the help browser dock widget."""
        self.help_browser_dock = HelpBrowserDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.help_browser_dock)
        
        # Hidden by default (auto-shows when a help link is clicked)
        self.help_browser_dock.hide()
        
        # Tab the help browser and log console together in the right dock area
        self.tabifyDockWidget(self.chart_cart_dock, self.help_browser_dock)
        self.tabifyDockWidget(self.help_browser_dock, self.log_console_dock)
        
        # Set up dock widget visibility changes to raise the active tab
        self.help_browser_dock.visibilityChanged.connect(self._on_help_browser_visibility_changed)
        
        # When help browser is shown, raise it to the front
        def raise_help_browser():
            if self.help_browser_dock.isVisible():
                self.help_browser_dock.raise_()
        
        # Connect menu action to raise help browser when shown
        if hasattr(self, '_help_browser_action'):
            self._help_browser_action.triggered.connect(raise_help_browser)
    
    @Slot()
    def _on_toggle_log_console(self):
        """Toggle the log console visibility."""
        if self.log_console_dock.isVisible():
            self.log_console_dock.hide()
        else:
            self.log_console_dock.show()
            self.log_console_dock.raise_()  # Bring to front
    
    @Slot()
    def _on_toggle_chart_cart(self):
        """Toggle the chart cart visibility."""
        if self.chart_cart_dock.isVisible():
            self.chart_cart_dock.hide()
        else:
            self.chart_cart_dock.show()
            self.chart_cart_dock.raise_()
    
    @Slot(bool)
    def _on_chart_cart_visibility_changed(self, visible: bool):
        """Sync menu check state with chart cart dock visibility."""
        self._chart_cart_action.setChecked(visible)
    
    @Slot()
    def _on_toggle_help_browser(self):
        """Toggle the help browser visibility."""
        if self.help_browser_dock.isVisible():
            self.help_browser_dock.hide()
        else:
            self.help_browser_dock.show()
            self.help_browser_dock.raise_()  # Bring to front
    
    def add_current_chart_to_cart(self):
        """Add the current chart configuration to the chart cart."""
        config = self.chart_widget.get_current_config()
        if not config:
            QMessageBox.information(self, "No Chart", "Create a chart first to add it to the cart.")
            return
        
        config_copy = copy.deepcopy(config)
        self.chart_cart_dock.add_config(config_copy)
        info(f"Added chart to cart: {config.title}")
    
    
# ############################################################################################################################
# ########################################### HELP TOOLTIPS ##################################################################
# ############################################################################################################################
    
    def _setup_help_tooltips(self):
        """Register help tooltips on widgets throughout the UI."""
        self._help_filter = HelpEventFilter(self)
        self._help_filter.link_clicked.connect(self.help_browser_dock.navigate)
        
        # Register widgets with their help pages
        self._help_filter.register(
            self.header_panel,
            "Snapshot header info — file name, type, hours",
            "snapshot_header.html"
        )
        self._help_filter.register(
            self.quick_chart_panel,
            "One-click diagnostic charts for common analyses",
            "quick_charts.html"
        )
        self._help_filter.register(
            self.pid_panel,
            "Search and select PIDs for custom charts",
            "custom_charts.html"
        )
        self._help_filter.register(
            self.axis_controls_panel,
            "Set axis ranges and auto-scale options",
            "axis_controls.html"
        )
            
    @Slot(bool)
    def _on_help_browser_visibility_changed(self, visible: bool):
        """Sync menu check state with help browser dock visibility."""
        self._help_browser_action.setChecked(visible)
    
    @Slot()
    def _on_snapshot_decoder_home(self):
        """Open Snapshot Decoder Home in web browser."""
        webbrowser.open("https://berrycompanies.sharepoint.com/sites/BOTRServiceSupport/Snapshot_Decoder")
    
    @Slot()
    def _on_check_for_updates(self):
        """Open the update checking page in the default browser."""
        # Open the updating page on GitHub Pages
        update_url = "https://nathanladd.github.io/Snapshot-Decoder/updating.html"
        webbrowser.open(update_url)
    
    @Slot()
    def _on_show_help_home(self):
        """Show the help browser with the home page."""
        self.help_browser_dock.navigate("index.html")
    
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
        popup.show()
    
    @Slot()
    def _on_show_debug_settings(self):
        """Show the debug settings dialog."""
        dialog = DebugSettingsDialog(self)
        
        # Get current settings before dialog
        from pid_debug_config import get_pid_debug_setting, get_log_interval, get_log_on_stop, get_position_threshold
        original_settings = {
            'enable': get_pid_debug_setting(),
            'interval': get_log_interval(),
            'log_on_stop': get_log_on_stop(),
            'threshold': get_position_threshold()
        }
        
        if dialog.exec():
            # Settings were applied - update running instances
            new_settings = {
                'enable': get_pid_debug_setting(),
                'interval': get_log_interval(),
                'log_on_stop': get_log_on_stop(),
                'threshold': get_position_threshold()
            }
            
            # Update chart widget's live values widget if settings changed
            if original_settings != new_settings:
                self._update_debug_settings(new_settings)
    
    def _update_debug_settings(self, settings: dict):
        """Update debug settings in running widgets."""
        # Update chart widget's live values widget
        if hasattr(self.chart_widget, '_live_values_widget'):
            self.chart_widget._live_values_widget.update_settings(settings)
    
    def _generate_reference_pdf(self):
        """Generate reference PDF using V2 architecture."""
        from domain.quick_charts.reference_builder import ReferenceChartBuilder
        from domain.snaptypes import SnapType
        
        snapshot = self.app_controller.get_snapshot()
        if not snapshot:
            warning("No snapshot available for reference PDF generation")
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
            info(f"Reference PDF generated: {file_path}")
        else:
            info("Reference PDF generation cancelled or failed")
