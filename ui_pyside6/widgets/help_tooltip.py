"""
Custom help tooltip with clickable 'more...' link.

Shows a tooltip-style popup with the widget's regular tooltip text
plus a clickable 'more...' link that navigates to a help page
in the embedded help browser.
"""

from PySide6.QtWidgets import QLabel, QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QEvent, QObject
from PySide6.QtGui import QCursor


class HelpToolTip(QLabel):
    """
    A custom tooltip widget that displays help text with a clickable 'more...' link.
    
    Appears on hover like a standard tooltip but stays visible long enough
    for the user to click the link.
    """
    
    link_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setOpenExternalLinks(False)
        self.setWordWrap(True)
        self.setMaximumWidth(350)
        self.setMouseTracking(True)
        
        self.setStyleSheet("""
            QLabel {
                background-color: #FFFEF0;
                border: 1px solid #B0B0B0;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
                color: #333;
            }
        """)
        
        self.linkActivated.connect(self._on_link_clicked)
        
        # Auto-hide timer
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
    
    def show_tip(self, global_pos: QPoint, tooltip_text: str, help_url: str):
        """
        Show the custom tooltip at the given global position.
        
        Args:
            global_pos: Screen position to show the tooltip near
            tooltip_text: The descriptive text to show
            help_url: URL for the 'more...' link
        """
        html = (
            f'<span style="color: #333;">{tooltip_text}</span>'
            f'<br/>'
            f'<a href="{help_url}" style="color: #0078d4; font-size: 10px;">more...</a>'
        )
        self.setText(html)
        self.adjustSize()
        
        # Position near cursor, offset slightly
        pos = global_pos + QPoint(16, 16)
        
        # Keep on screen
        screen = QApplication.screenAt(global_pos)
        if screen:
            screen_rect = screen.availableGeometry()
            if pos.x() + self.width() > screen_rect.right():
                pos.setX(screen_rect.right() - self.width())
            if pos.y() + self.height() > screen_rect.bottom():
                pos.setY(global_pos.y() - self.height() - 8)
        
        self.move(pos)
        self.show()
        self.raise_()
        
        # Auto-hide after 6 seconds if user doesn't interact
        self._hide_timer.start(6000)
    
    def enterEvent(self, event):
        """Keep tooltip visible while mouse is over it."""
        self._hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Start hide timer when mouse leaves."""
        self._hide_timer.start(500)
        super().leaveEvent(event)
    
    def _on_link_clicked(self, url: str):
        """Handle 'more...' link click."""
        self.hide()
        self.link_clicked.emit(url)


class HelpEventFilter(QObject):
    """
    Event filter that intercepts ToolTip events on registered widgets
    and shows a custom HelpToolTip with a clickable 'more...' link instead.
    
    Usage:
        help_filter = HelpEventFilter(parent)
        help_filter.link_clicked.connect(my_help_browser.navigate)
        help_filter.register(my_widget, "This is a widget", "quick_charts.html")
    """
    
    link_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tooltip = HelpToolTip()
        self._tooltip.link_clicked.connect(self.link_clicked.emit)
        self._registry = {}  # widget id -> (tooltip_text, help_url)
    
    def register(self, widget: QWidget, tooltip_text: str, help_url: str):
        """
        Register a widget to show a custom help tooltip on hover.
        
        Args:
            widget: The widget to attach help to
            tooltip_text: Descriptive tooltip text
            help_url: Help page filename (e.g. 'quick_charts.html') or full URL
        """
        widget.installEventFilter(self)
        # Clear the standard tooltip so Qt doesn't show its own
        widget.setToolTip("")
        self._registry[id(widget)] = (tooltip_text, help_url)
    
    def unregister(self, widget: QWidget):
        """Remove help tooltip from a widget."""
        widget.removeEventFilter(self)
        self._registry.pop(id(widget), None)
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Intercept ToolTip events and show custom tooltip."""
        if event.type() == QEvent.Type.ToolTip:
            widget_id = id(obj)
            if widget_id in self._registry:
                tooltip_text, help_url = self._registry[widget_id]
                self._tooltip.show_tip(
                    QCursor.pos(),
                    tooltip_text,
                    help_url
                )
                return True  # Consume the event (suppress default tooltip)
        
        elif event.type() == QEvent.Type.Leave:
            # Only start hide timer if mouse isn't over the tooltip itself
            if not self._tooltip.underMouse():
                self._tooltip._hide_timer.start(500)
        
        return super().eventFilter(obj, event)
