"""
Main entry point for Snapshot Decoder (PySide6 version).
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui_pyside6 import MainWindow


def main():
    """Run the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Snapshot Decoder")
    app.setOrganizationName("Snapshot Decoder")
    
    # Set application style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
