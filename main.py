"""
Main entry point for Snapshot Decoder (PySide6 version).
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QColor, QPalette

from ui_pyside6 import MainWindow
from version import APP_VERSION


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    """Run the application with splash screen."""
    # Enable high DPI scaling (must be done before QApplication creation)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Phase 1: Create QApplication first (required for QSplashScreen)
    app = QApplication(sys.argv)
    app.setApplicationName("Snapshot Decoder")
    app.setOrganizationName("Snapshot Decoder")
    
    # Phase 2: Create and show splash screen
    splash_pixmap = QPixmap(resource_path("data/images/splash.png"))
    if splash_pixmap.isNull():
        # Fallback if image doesn't load
        print("Warning: Could not load splash.png")
        splash = None
    else:
        # Scale down to 70% of original size
        scaled_w = int(splash_pixmap.width() * 0.70)
        scaled_h = int(splash_pixmap.height() * 0.70)
        splash_pixmap = splash_pixmap.scaled(
            scaled_w, scaled_h, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Add padding below the image so text doesn't overlap
        padding_height = 60
        padded_pixmap = QPixmap(scaled_w, scaled_h + padding_height)
        padded_pixmap.fill(QColor(255, 255, 255))  # White background
        
        from PySide6.QtGui import QPainter
        painter = QPainter(padded_pixmap)
        painter.drawPixmap(0, 0, splash_pixmap)
        painter.end()
        
        splash = QSplashScreen(padded_pixmap)
        
        # Set font for splash messages
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        splash.setFont(font)
        
        # Initial message with version
        splash.showMessage(
            f"Snapshot Decoder v{APP_VERSION}\nLoading...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor(0, 0, 0)  # Black color
        )
        splash.show()
        app.processEvents()  # Ensure splash is rendered immediately
    
    # Track splash start time for minimum display duration
    splash_start_time = time.time()
    min_display_time = 3.0  # 3 seconds minimum
    
    # Phase 3: Load application normally (this will show progress naturally)
    if splash:
        splash.showMessage(
            f"Snapshot Decoder v{APP_VERSION}\nLoading modules...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor(0, 0, 0)
        )
        app.processEvents()
    
    # Set application style
    app.setStyle("Fusion")
    
    # Force light mode palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    if splash:
        splash.showMessage(
            f"Snapshot Decoder v{APP_VERSION}\nCreating UI...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor(0, 0, 0)
        )
        app.processEvents()
    
    # Phase 4: Create main window
    window = MainWindow()
    
    if splash:
        splash.showMessage(
            f"Snapshot Decoder v{APP_VERSION}\nReady!",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor(0, 0, 0)
        )
        app.processEvents()
    
    # Ensure minimum display time
    elapsed_time = time.time() - splash_start_time
    remaining_time = max(0, min_display_time - elapsed_time)
    
    def show_main_window():
        """Show main window and finish splash screen."""
        window.show()
        if splash:
            splash.finish(window)
    
    if remaining_time > 0 and splash:
        # Use QTimer to delay window show for remaining time
        QTimer.singleShot(int(remaining_time * 1000), show_main_window)
    else:
        show_main_window()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
