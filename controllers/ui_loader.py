"""
Background UI loader with progress updates.

Loads PySide6 UI components in a dedicated QThread to keep the splash screen responsive,
emitting Qt signals at each processing phase.
"""

import sys
from typing import Optional

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QPalette, QColor

from ui_pyside6 import MainWindow


class UILoader(QThread):
    """
    Background thread for loading PySide6 UI with progress updates.
    
    Signals:
        progress: Emitted with (percent, message) during loading
        finished_loading: Emitted with MainWindow instance on successful load
        error: Emitted with error message string on failure
    """
    
    # Signals
    progress = Signal(int, str)           # (percent, message)
    finished_loading = Signal(object)     # MainWindow on success
    error = Signal(str)                   # Error message on failure
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False
        self._app = None
        self._window = None
    
    def cancel(self):
        """Request cancellation (checked between phases)."""
        self._cancelled = True
    
    def run(self):
        """Execute the UI loading pipeline."""
        try:
            # Phase 1: Import heavy modules (this is where the real work happens)
            self.progress.emit(10, "Loading PySide6 modules...")
            # These imports happen here to show progress during loading
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPalette, QColor
            if self._cancelled:
                return
            
            # Phase 2: Import UI components (but don't create widgets yet)
            self.progress.emit(30, "Loading UI components...")
            from ui_pyside6 import MainWindow
            if self._cancelled:
                return
            
            # Phase 3: Import domain modules
            self.progress.emit(50, "Loading domain modules...")
            from domain.snapshot import Snapshot
            from domain.constants import APP_TITLE, APP_VERSION, UPDATE_URL
            if self._cancelled:
                return
            
            # Phase 4: Import controller modules
            self.progress.emit(70, "Loading controllers...")
            from controllers.snapshot_loader import SnapshotLoader
            if self._cancelled:
                return
            
            # Phase 5: Import file I/O modules
            self.progress.emit(90, "Loading file I/O modules...")
            from file_io.reader_excel import load_xls, load_xlsx
            if self._cancelled:
                return
            
            # Store the MainWindow class for creation in main thread
            self._main_window_class = MainWindow
            
            self.progress.emit(100, "Complete")
            # Emit the class instead of instance - main thread will create the actual window
            self.finished_loading.emit(self._main_window_class)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def create_window(self, window_class):
        """Create the main window instance (called from main thread)."""
        try:
            window = window_class()
            self._window = window
            return window
        except Exception as e:
            self.error.emit(str(e))
            return None
    
    def get_app(self) -> Optional[QApplication]:
        """Get the QApplication instance (after loading completes)."""
        return self._app
    
    def get_window(self) -> Optional[MainWindow]:
        """Get the MainWindow instance (after loading completes)."""
        return self._window
