"""
Application Controller - UI-agnostic orchestration using Qt signals.

Coordinates between snapshot loading, chart configuration, and UI updates.
No UI dependencies - pure business logic with Qt signal communication.
"""

from PySide6.QtCore import QObject, Signal
from typing import Optional
import os
import time

from domain.snapshot import Snapshot
from controllers.snapshot_loader import SnapshotLoader
from infrastructure import get_logger, log_file_loaded, log_file_error, info, error, warning


class AppController(QObject):
    """
    Main application controller - orchestrates all app actions.
    
    Manages:
    - Snapshot loading with progress feedback
    - Chart state management  
    - Error handling and logging
    - Signal-based communication with UI
    """
    
    # Signals for UI to connect to
    snapshot_loaded = Signal(object)          # emits Snapshot
    snapshot_load_progress = Signal(int, str) # emits (percent, message)
    error_occurred = Signal(str)              # emits error message
    chart_updated = Signal(object)            # emits ChartConfig
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        info("AppController initialized")
        self.snapshot: Optional[Snapshot] = None
        self.loader: Optional[SnapshotLoader] = None
    
    def load_snapshot(self, file_path: str):
        """
        Load a snapshot file in background thread.
        
        Args:
            file_path: Path to the snapshot file to load
        """
        if not os.path.exists(file_path):
            self.error_occurred.emit(f"File not found: {file_path}")
            return
        
        info(f"Starting snapshot load: {file_path}")
        
        # Cancel any existing load
        if self.loader and self.loader.isRunning():
            self.loader.cancel()
            self.loader.wait()
        
        # Create new loader
        self.loader = SnapshotLoader(file_path)
        
        # Connect signals
        self.loader.progress.connect(self._on_load_progress)
        self.loader.finished_loading.connect(self._on_load_finished)
        self.loader.error.connect(self._on_load_error)
        
        # Start loading
        self.loader.start()
    
    def _on_load_progress(self, percent: int, message: str):
        """Forward loader progress to UI."""
        self.snapshot_load_progress.emit(percent, message)
    
    def _on_load_finished(self, snapshot: Snapshot):
        """Handle successful snapshot load."""
        self.snapshot = snapshot
        info(f"Snapshot loaded successfully: {snapshot.snapshot_type}")
        
        # Emit to UI
        self.snapshot_loaded.emit(snapshot)
    
    def _on_load_error(self, error_msg: str):
        """Handle snapshot load error."""
        error(f"Snapshot load failed: {error_msg}")
        
        # Log error for chain of custody
        file_path = self.loader.file_path if self.loader else "unknown"
        log_file_error(file_path, error_msg)
        
        # Emit to UI
        self.error_occurred.emit(error_msg)
    
    def get_snapshot(self) -> Optional[Snapshot]:
        """Get currently loaded snapshot."""
        return self.snapshot
    
    def has_snapshot(self) -> bool:
        """Check if a snapshot is currently loaded."""
        return self.snapshot is not None
    
    def clear_snapshot(self):
        """Clear the current snapshot."""
        self.snapshot = None
        info("Snapshot cleared")
    
    def shutdown(self):
        """Clean shutdown - cancel any operations."""
        if self.loader and self.loader.isRunning():
            self.loader.cancel()
            self.loader.wait()
        
        info("AppController shutdown complete")
