"""
Dockable Quick IQ browser panel.

Provides an embedded browser for chart-specific SharePoint pages.
"""

from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from domain.app_settings import app_settings


class QuickIQDock(QDockWidget):
    """Dockable browser panel for Quick IQ chart guidance pages."""

    def __init__(self, parent=None):
        super().__init__("Quick IQ", parent)

        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self._setup_title_bar()
        self.topLevelChanged.connect(self._on_top_level_changed)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = QHBoxLayout()
        nav.setContentsMargins(4, 0, 4, 2)
        nav.setSpacing(4)

        btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 2px;
                padding: 2px 6px;
                background-color: #F0F0F0;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #E0E0E0; border: 1px solid #0078d4; }
            QPushButton:pressed { background-color: #D0D0D0; }
            QPushButton:disabled { color: #AAA; background-color: #F8F8F8; }
        """

        self._back_btn = QPushButton("◀")
        self._back_btn.setFixedWidth(28)
        self._back_btn.setStyleSheet(btn_style)
        self._back_btn.setToolTip("Back")
        self._back_btn.clicked.connect(self._on_back)
        nav.addWidget(self._back_btn)

        self._fwd_btn = QPushButton("▶")
        self._fwd_btn.setFixedWidth(28)
        self._fwd_btn.setStyleSheet(btn_style)
        self._fwd_btn.setToolTip("Forward")
        self._fwd_btn.clicked.connect(self._on_forward)
        nav.addWidget(self._fwd_btn)

        self._home_btn = QPushButton("⌂")
        self._home_btn.setFixedWidth(28)
        self._home_btn.setStyleSheet(btn_style)
        self._home_btn.setToolTip("Quick IQ home")
        self._home_btn.clicked.connect(self._on_home)
        nav.addWidget(self._home_btn)

        self._url_bar = QLineEdit()
        self._url_bar.setReadOnly(True)
        self._url_bar.setStyleSheet(
            "QLineEdit { font-size: 10px; padding: 2px 4px; "
            "background: #FAFAFA; border: 1px solid #CCC; border-radius: 2px; }"
        )
        nav.addWidget(self._url_bar, stretch=1)

        layout.addLayout(nav)

        self.browser = QWebEngineView()
        self.set_zoom_factor(app_settings.web_zoom_factor)
        self.browser.urlChanged.connect(self._on_url_changed)
        layout.addWidget(self.browser, stretch=1)

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

        self.setWidget(container)
        self.setFloating(False)
        self.resize(360, 500)
        self._on_top_level_changed(self.isFloating())

        self._on_home()

    def _setup_title_bar(self):
        """Setup custom title bar with left-justified title and actions."""
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

        self.title_label = QLabel("Quick IQ")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333; text-align: left;")
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

        self.setTitleBarWidget(title_bar)

    def navigate(self, url: str):
        """Navigate to a Quick IQ URL and show the dock."""
        self.browser.setUrl(QUrl(url))
        if not self.isVisible():
            self.show()
        self.raise_()

    def set_zoom_factor(self, zoom_factor: float):
        """Set browser zoom factor with a safe clamp range."""
        zoom = max(0.50, min(2.50, float(zoom_factor)))
        self.browser.setZoomFactor(zoom)

    @Slot()
    def _on_back(self):
        self.browser.back()

    @Slot()
    def _on_forward(self):
        self.browser.forward()

    @Slot()
    def _on_home(self):
        self.browser.setHtml(
            "<html><body style='font-family:Segoe UI;padding:16px;'>"
            "<h3>Quick IQ</h3><p>Select a chart and click the brain icon to load Quick IQ content.</p>"
            "</body></html>"
        )

    @Slot(QUrl)
    def _on_url_changed(self, url: QUrl):
        self._url_bar.setText(url.toString())
        self._back_btn.setEnabled(self.browser.history().canGoBack())
        self._fwd_btn.setEnabled(self.browser.history().canGoForward())

    @Slot()
    def _on_toggle_floating(self):
        self.setFloating(not self.isFloating())

    @Slot()
    def _on_close_requested(self):
        self.close()

    @Slot(bool)
    def _on_top_level_changed(self, is_floating: bool):
        if is_floating:
            self.popout_btn.setText("⇲")
            self.popout_btn.setToolTip("Dock panel")
        else:
            self.popout_btn.setText("↗")
            self.popout_btn.setToolTip("Pop out panel")
