"""
Dockable help browser panel for the main window.

Provides an embedded web browser for displaying local and remote
help pages, navigated via clickable tooltip links.
"""

import os
import sys

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QStyle
)
from PySide6.QtCore import Qt, QSize, QUrl, Slot
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
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
        self.topLevelChanged.connect(self._on_top_level_changed)

        # Main content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Navigation bar
        nav = QHBoxLayout()
        nav.setContentsMargins(4, 0, 4, 2)
        nav.setSpacing(4)

        nav_btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 4px;
                background-color: #F0F0F0;
            }
            QPushButton:hover { background-color: #E0E0E0; border: 1px solid #0078d4; }
            QPushButton:pressed { background-color: #D0D0D0; }
            QPushButton:disabled { background-color: #F8F8F8; }
        """
        nav_icon_size = QSize(18, 18)

        self._back_btn = QPushButton()
        self._back_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self._back_btn.setIconSize(nav_icon_size)
        self._back_btn.setFixedSize(34, 34)
        self._back_btn.setStyleSheet(nav_btn_style)
        self._back_btn.setToolTip("Back")
        self._back_btn.clicked.connect(self._on_back)
        nav.addWidget(self._back_btn)

        self._fwd_btn = QPushButton()
        self._fwd_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self._fwd_btn.setIconSize(nav_icon_size)
        self._fwd_btn.setFixedSize(34, 34)
        self._fwd_btn.setStyleSheet(nav_btn_style)
        self._fwd_btn.setToolTip("Forward")
        self._fwd_btn.clicked.connect(self._on_forward)
        nav.addWidget(self._fwd_btn)

        self._home_btn = QPushButton("\u2302")
        self._home_btn.setFixedSize(34, 34)
        self._home_btn.setStyleSheet(nav_btn_style + "QPushButton { font-size: 18px; }")
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

        # Persistent browser profile (retains cookies/sessions across restarts)
        if getattr(sys, "frozen", False):
            profile_path = os.path.join(os.path.dirname(sys.executable), "browser_data")
        else:
            profile_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "browser_data",
            )
        self._profile = QWebEngineProfile("SnapshotDecoder", self)
        self._profile.setCachePath(os.path.join(profile_path, "cache"))
        self._profile.setPersistentStoragePath(os.path.join(profile_path, "storage"))
        self._profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # Web view with persistent profile
        from PySide6.QtWebEngineCore import QWebEnginePage
        page = QWebEnginePage(self._profile, self)
        self.browser = QWebEngineView()
        self.browser.setPage(page)

        # Enable useful browser settings
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

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
                    stop:0 #EAF4FF, stop:1 #D8E9FF);
                border-bottom: 1px solid #AFC8E8;
                padding: 2px;
            }
        """)

        self.resize(self._expanded_size)
        self._on_top_level_changed(self.isFloating())

        # Load home page
        self._on_home()

    # ── Title bar ──────────────────────────────────────────────

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

        self.title_label = QLabel("Help")
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

    def collapse(self):
        self._is_expanded = False
        self.widget().setVisible(False)
        self.resize(self._collapsed_size)

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
        if not self._is_expanded:
            self.expand()
        self.raise_()

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
