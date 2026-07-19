"""
Dockable My Charts panel for the main window.

Provides a dockable widget that contains the user-saved chart templates,
with proper integration into the main window's dock system.
"""

from PySide6.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize

from .my_charts_widget import MyChartsWidget


class MyChartsDock(QDockWidget):
    """Dockable My Charts widget for the main window."""

    def __init__(self, parent=None):
        super().__init__("My Charts", parent)

        # Set dock widget properties
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Create custom title bar with popout/close buttons
        self._setup_title_bar()
        self.topLevelChanged.connect(self._on_top_level_changed)

        # Create the My Charts content widget
        self.my_charts = MyChartsWidget(self)
        self.setWidget(self.my_charts)

        # Default to not floating
        self.setFloating(False)

        # Add padding around the dock widget
        self.setStyleSheet("""
            QDockWidget {
                border: 1px solid #C0C0C0;
                margin: 2px;
                background-color: #F8F8F8;
            }
            QDockWidget::title {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #EAF4FF, stop:1 #D8E9FF);
                border-bottom: 1px solid #AFC8E8;
                padding: 2px;
            }
        """)

        # Set initial size
        self.resize(QSize(220, 400))
        self._on_top_level_changed(self.isFloating())

    def _setup_title_bar(self):
        """Setup custom title bar with left-justified title."""
        title_bar = QWidget()
        title_bar.setFixedHeight(25)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #EAF4FF, stop:1 #D8E9FF);
                border-bottom: 1px solid #AFC8E8;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 2, 5, 2)
        title_layout.setSpacing(5)

        self.title_label = QLabel("My Charts")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)

        btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 2px;
                background-color: #F0F0F0;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
        """

        close_btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 2px;
                background-color: #FFF0F0;
                font-size: 11px;
                font-weight: bold;
                color: #A40000;
            }
            QPushButton:hover {
                background-color: #FFD0D0;
                border: 1px solid #d40000;
            }
            QPushButton:pressed {
                background-color: #FFB8B8;
            }
        """

        self.popout_btn = QPushButton("↗")
        self.popout_btn.setFixedSize(22, 22)
        self.popout_btn.setStyleSheet(btn_style)
        self.popout_btn.clicked.connect(self._on_toggle_floating)
        title_layout.addWidget(self.popout_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setStyleSheet(close_btn_style)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self._on_close_requested)
        title_layout.addWidget(self.close_btn)

        # Set custom title bar
        self.setTitleBarWidget(title_bar)

    def _on_toggle_floating(self):
        self.setFloating(not self.isFloating())

    def _on_close_requested(self):
        self.close()

    def _on_top_level_changed(self, is_floating: bool):
        if is_floating:
            self.popout_btn.setText("⇲")
            self.popout_btn.setToolTip("Dock panel")
        else:
            self.popout_btn.setText("↗")
            self.popout_btn.setToolTip("Pop out panel")
