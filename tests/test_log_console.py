#!/usr/bin/env python3
"""
Test script for the log console widget.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt

from ui_pyside6.widgets.log_console import LogConsole
from infrastructure import log_debug, log_info, log_warning, log_error


class TestWindow(QMainWindow):
    """Test window for the log console."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Log Console Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create log console
        self.log_console = LogConsole()
        layout.addWidget(self.log_console)
        
        # Test buttons
        test_layout = QVBoxLayout()
        
        debug_btn = QPushButton("Test Debug Messages")
        debug_btn.clicked.connect(self.test_debug)
        test_layout.addWidget(debug_btn)
        
        info_btn = QPushButton("Test Info Messages")
        info_btn.clicked.connect(self.test_info)
        test_layout.addWidget(info_btn)
        
        warning_btn = QPushButton("Test Warning Messages")
        warning_btn.clicked.connect(self.test_warning)
        test_layout.addWidget(warning_btn)
        
        error_btn = QPushButton("Test Error Messages")
        error_btn.clicked.connect(self.test_error)
        test_layout.addWidget(error_btn)
        
        progress_btn = QPushButton("Test Progress Messages")
        progress_btn.clicked.connect(self.test_progress)
        test_layout.addWidget(progress_btn)
        
        layout.addLayout(test_layout)
    
    def test_debug(self):
        """Test debug messages."""
        debug("This is a debug message")
        debug("Another debug message with details")
        debug("Debug message with context")
    
    def test_info(self):
        """Test info messages."""
        info("This is an info message")
        info("Application started successfully")
        info("Processing completed")
    
    def test_warning(self):
        """Test warning messages."""
        warning("This is a warning message")
        warning("Deprecated API used")
        warning("Performance issue detected")
    
    def test_error(self):
        """Test error messages."""
        error("This is an error message")
        error("Failed to load configuration")
        error("Connection timeout occurred")
    
    def test_progress(self):
        """Test progress messages."""
        self.log_console.log_progress("file_load", "Loading file: 0%")
        QApplication.processEvents()
        
        import time
        for i in range(1, 6):
            time.sleep(0.5)
            self.log_console.log_progress("file_load", f"Loading file: {i*20}%")
            QApplication.processEvents()
        
        self.log_console.log_progress("file_load", "File loaded successfully!")


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # Test some initial log messages
    info("Log Console Test Application Started")
    debug("Testing log console functionality")
    warning("This is a test warning")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
