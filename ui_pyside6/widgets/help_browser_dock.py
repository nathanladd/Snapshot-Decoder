"""
Dockable help browser panel for the main window.

Provides an embedded web browser for displaying local and remote
help pages, navigated via clickable tooltip links.
"""

import os

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStyle, QLabel, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QUrl, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from domain.app_settings import app_settings


# Resolve the help directory path once
_HELP_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "help")
)


class HelpBrowserDock(QDockWidget):
    """
    Dockable help browser with back/forward navigation.

    Displays local HTML help pages and remote URLs.
    Hidden by default; auto-shows when a help link is clicked.
    """

    def __init__(self, parent=None):
        super().__init__("Help", parent)

        # Track expansion state
        self._is_expanded = True
        self._collapsed_size = QSize(0, 30)
        self._expanded_size = QSize(350, 500)

        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        self._setup_title_bar()

        # Main content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Navigation bar
        nav = QHBoxLayout()
        nav.setContentsMargins(4, 2, 4, 2)
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
        self._home_btn.setToolTip("Help home")
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

        # Web view
        self.browser = QWebEngineView()
        self.set_zoom_factor(app_settings.web_zoom_factor)
        self.browser.urlChanged.connect(self._on_url_changed)
        layout.addWidget(self.browser, stretch=1)

        self.setWidget(container)
        self.setFloating(False)

        self.setStyleSheet("""
            QDockWidget {
                border: 1px solid #C0C0C0;
                margin: 2px;
                background-color: #F8F8F8;
            }
            QDockWidget::title {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F0F0F0, stop:1 #E0E0E0);
                border-bottom: 1px solid #C0C0C0;
                padding: 2px;
            }
        """)

        self.resize(self._expanded_size)

        # Load home page
        self._on_home()

    # ── Title bar ──────────────────────────────────────────────

    def _setup_title_bar(self):
        """Setup custom title bar with expand/collapse button and drag handle."""
        title_bar = QWidget()
        title_bar.setFixedHeight(25)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 2, 5, 2)
        title_layout.setSpacing(5)

        self.drag_handle = QLabel()
        self.drag_handle.setFixedHeight(16)
        self.drag_handle.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(120,120,120,0.3),
                    stop:0.5 rgba(120,120,120,0.5),
                    stop:1 rgba(120,120,120,0.3));
                border: 1px solid rgba(120,120,120,0.4);
                border-radius: 3px; margin: 2px;
            }
            QLabel:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100,100,100,0.4),
                    stop:0.5 rgba(100,100,100,0.6),
                    stop:1 rgba(100,100,100,0.4));
                border: 1px solid rgba(100,100,100,0.6);
            }
        """)
        self.drag_handle.setToolTip("Drag to move panel")

        self.expand_btn = QPushButton()
        self.expand_btn.setFixedSize(16, 16)
        self.expand_btn.clicked.connect(self.toggle_expand)
        self._update_expand_button_icon()
        self.expand_btn.setStyleSheet("""
            QPushButton { border: none; padding: 0px; background: transparent; }
            QPushButton:hover { background: rgba(200,200,200,100); border-radius: 2px; }
            QPushButton:pressed { background: rgba(150,150,150,100); }
        """)

        title_layout.addWidget(self.drag_handle, 1)
        title_layout.addWidget(self.expand_btn)
        self.setTitleBarWidget(title_bar)

    # ── Expand / collapse ──────────────────────────────────────

    def toggle_expand(self):
        if self._is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self._is_expanded = True
        self.widget().setVisible(True)
        self.resize(self._expanded_size)
        self._update_expand_button_icon()

    def collapse(self):
        self._is_expanded = False
        self.widget().setVisible(False)
        self.resize(self._collapsed_size)
        self._update_expand_button_icon()

    def _update_expand_button_icon(self):
        if self._is_expanded:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown)
            self.expand_btn.setIcon(icon)
            self.expand_btn.setToolTip("Collapse")
        else:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)
            self.expand_btn.setIcon(icon)
            self.expand_btn.setToolTip("Expand")

    def set_zoom_factor(self, zoom_factor: float):
        """Set browser zoom factor with a safe clamp range."""
        zoom = max(0.50, min(2.50, float(zoom_factor)))
        self.browser.setZoomFactor(zoom)

    # ── Navigation ─────────────────────────────────────────────

    def navigate(self, url_or_filename: str):
        """
        Navigate to a help page.

        Args:
            url_or_filename: Either a full URL (http/https), a local file path,
                             or just a filename like 'quick_charts.html' which
                             is resolved relative to data/help/.
        """
        if url_or_filename.startswith(("http://", "https://")):
            url = QUrl(url_or_filename)
        elif os.path.isabs(url_or_filename):
            url = QUrl.fromLocalFile(url_or_filename)
        else:
            # Treat as a filename relative to data/help/
            full_path = os.path.join(_HELP_DIR, url_or_filename)
            url = QUrl.fromLocalFile(os.path.normpath(full_path))

        self.browser.setUrl(url)

        # Auto-show and expand if hidden/collapsed
        if not self.isVisible():
            self.show()
            self.raise_()
        if not self._is_expanded:
            self.expand()

    @Slot()
    def _on_back(self):
        self.browser.back()

    @Slot()
    def _on_forward(self):
        self.browser.forward()

    @Slot()
    def _on_home(self):
        home = os.path.join(_HELP_DIR, "index.html")
        if os.path.exists(home):
            self.browser.setUrl(QUrl.fromLocalFile(home))
        else:
            self.browser.setHtml(
                "<html><body style='font-family:Segoe UI;'>"
                "<h2>Help</h2><p>No help files found.</p></body></html>"
            )

    @Slot(QUrl)
    def _on_url_changed(self, url: QUrl):
        """Update the URL bar and nav button states."""
        display = url.toLocalFile() if url.isLocalFile() else url.toString()
        # Show just the filename for local files
        if url.isLocalFile():
            display = os.path.basename(display)
        self._url_bar.setText(display)
        self._back_btn.setEnabled(self.browser.history().canGoBack())
        self._fwd_btn.setEnabled(self.browser.history().canGoForward())
