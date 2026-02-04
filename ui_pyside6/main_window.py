"""
Main application window for Snapshot Decoder.

PySide6 implementation with modern UI layout.
"""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QProgressDialog, QMessageBox,
    QFileDialog, QLabel, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QIcon, QPixmap

from domain.snapshot import Snapshot
from domain.constants import APP_TITLE
from controllers.snapshot_loader import SnapshotLoader
from version import APP_VERSION
from infrastructure import get_logger

from ui_pyside6.widgets.header_panel import HeaderPanel
from ui_pyside6.widgets.system_panel import SystemPanel
from ui_pyside6.widgets.pid_panel import PidPanel
from ui_pyside6.widgets.quick_chart_panel import QuickChartPanel
from ui_pyside6.widgets.chart_widget import ChartWidget
from ui_pyside6.widgets.axis_controls_panel import AxisControlsPanel
from ui_pyside6.widgets.log_console_dock import LogConsoleDock


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize logging system
        self.logger = get_logger()
        self.logger.logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")
        
        self.snapshot: Optional[Snapshot] = None
        self._loader: Optional[SnapshotLoader] = None
        self._progress_dialog: Optional[QProgressDialog] = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_log_console()
        
        self.setWindowTitle(f"{APP_TITLE} {APP_VERSION}")
        self.resize(1400, 900)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Main splitter for left panel and chart area
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel (header, PIDs, quick charts)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        
        # Header panel with system indicators to the right
        header_row = QHBoxLayout()
        header_row.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align entire row to top
        
        self.header_panel = HeaderPanel()
        header_row.addWidget(self.header_panel)
        
        self.system_panel = SystemPanel()
        # Vertically center the system panel relative to header panel
        header_row.addWidget(self.system_panel, 0, Qt.AlignmentFlag.AlignVCenter)
        
        left_layout.addLayout(header_row)
        
        # PID selection panel
        self.pid_panel = PidPanel()
        self.pid_panel.pids_changed.connect(self._on_pids_changed)
        left_layout.addWidget(self.pid_panel, stretch=1)
        
        # Axis controls panel
        self.axis_controls_panel = AxisControlsPanel()
        self.axis_controls_panel.settings_changed.connect(self._on_axis_settings_changed)
        left_layout.addWidget(self.axis_controls_panel)
        
        self.main_splitter.addWidget(left_panel)
        
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
        logo_path = os.path.join(os.path.dirname(__file__), "..", "data", "images", "Snapshot Decoder.png")
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
        right_layout.addWidget(self.chart_widget, stretch=1)
        
        self.main_splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (left panel ~350px, rest for chart)
        self.main_splitter.setSizes([350, 1050])
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        data_table_action = QAction("&Data Table...", self)
        data_table_action.triggered.connect(self._on_show_data_table)
        view_menu.addAction(data_table_action)
        
        pid_info_action = QAction("&PID Info...", self)
        pid_info_action.triggered.connect(self._on_show_pid_info)
        view_menu.addAction(pid_info_action)
        
        view_menu.addSeparator()
        
        log_console_action = QAction("&Log Console", self)
        log_console_action.setCheckable(True)
        log_console_action.triggered.connect(self._on_toggle_log_console)
        view_menu.addAction(log_console_action)
        
        view_menu.addSeparator()
        
        open_logs_action = QAction("&Open Log Files...", self)
        open_logs_action.triggered.connect(self._on_open_log_files)
        view_menu.addAction(open_logs_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_show_about)
        help_menu.addAction(about_action)
    
    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready - Open a snapshot file to begin")
    
    @Slot()
    def _on_open_file(self):
        """Handle file open action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Snapshot File",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self._load_snapshot(file_path)
    
    def _load_snapshot(self, file_path: str):
        """Load a snapshot file in the background."""
        # Create progress dialog
        self._progress_dialog = QProgressDialog(
            "Loading snapshot...", "Cancel", 0, 100, self
        )
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setAutoClose(True)
        self._progress_dialog.setMinimumDuration(0)
        
        # Create and start loader
        self._loader = SnapshotLoader(file_path, self)
        self._loader.progress.connect(self._on_load_progress)
        self._loader.finished_loading.connect(self._on_load_finished)
        self._loader.error.connect(self._on_load_error)
        self._progress_dialog.canceled.connect(self._loader.cancel)
        
        self._loader.start()
    
    @Slot(int, str)
    def _on_load_progress(self, percent: int, message: str):
        """Handle loading progress updates."""
        if self._progress_dialog:
            self._progress_dialog.setValue(percent)
            self._progress_dialog.setLabelText(message)
    
    @Slot(object)
    def _on_load_finished(self, snapshot: Snapshot):
        """Handle successful snapshot load."""
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
    
    @Slot(str)
    def _on_load_error(self, error_msg: str):
        """Handle loading error."""
        if self._progress_dialog:
            self._progress_dialog.close()
        
        QMessageBox.critical(self, "Load Error", error_msg)
        self.statusbar.showMessage("Error loading file")
    
    @Slot()
    def _on_pids_changed(self):
        """Handle PID selection changes."""
        if not self.snapshot:
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
            self._update_axis_controls_from_chart()
        else:
            # No PIDs selected, clear the chart
            self.chart_widget.clear()
            # Reset PID panel colors
            self.pid_panel.update_chart_colors(None)
            self.axis_controls_panel.clear()
    
    @Slot()
    def _on_axis_settings_changed(self):
        """Handle axis settings changes from the controls panel."""
        if not self.snapshot:
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
        
        self.chart_widget.plot_quick_chart(self.snapshot, action_id)
        
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
    def _on_show_data_table(self):
        """Show the data table window."""
        if not self.snapshot:
            QMessageBox.information(self, "No Data", "Please load a snapshot first.")
            return
        # TODO: Implement DataTableWindow
        QMessageBox.information(self, "Coming Soon", "Data table view coming soon.")
    
    @Slot()
    def _on_show_pid_info(self):
        """Show the PID info window."""
        if not self.snapshot:
            QMessageBox.information(self, "No Data", "Please load a snapshot first.")
            return
        # TODO: Implement PidInfoWindow
        QMessageBox.information(self, "Coming Soon", "PID info view coming soon.")
    
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
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_console_dock)
        
        # Hide by default (user can show via menu)
        self.log_console_dock.hide()
    
    @Slot()
    def _on_toggle_log_console(self):
        """Toggle log console visibility."""
        if self.log_console_dock.isVisible():
            self.log_console_dock.hide()
        else:
            self.log_console_dock.show()
            self.log_console_dock.raise_()  # Bring to front
    
    @Slot()
    def _on_open_log_files(self):
        """Open the log files directory in file explorer."""
        import subprocess
        import platform
        
        logger = get_logger()
        log_dir = logger.logs_dir
        
        # Ensure the log directory exists
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Could not create log directory:\n{str(e)}"
            )
            return
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(log_dir)], check=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(log_dir)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(log_dir)], check=True)
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Could not open log files directory:\n{str(e)}\n\nPath: {log_dir}"
            )
