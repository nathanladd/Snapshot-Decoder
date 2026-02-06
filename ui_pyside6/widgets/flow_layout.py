"""
Flow layout widget for responsive grid arrangement.

Arranges items horizontally, wrapping to new rows as needed.
Perfect for card-based UIs that need to adapt to container width.
"""

from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QSize, QRect, QPoint


class FlowLayout(QLayout):
    """
    A flow layout that arranges items in rows, wrapping as needed.
    
    Similar to CSS flexbox with flex-wrap: wrap.
    Items maintain their preferred size hints.
    """
    
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super().__init__(parent)
        
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._item_list = []
    
    def addItem(self, item: QLayoutItem):
        """Add an item to the layout."""
        self._item_list.append(item)
    
    def count(self) -> int:
        """Return the number of items in the layout."""
        return len(self._item_list)
    
    def itemAt(self, index: int) -> QLayoutItem:
        """Return the item at the given index."""
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None
    
    def takeAt(self, index: int) -> QLayoutItem:
        """Remove and return the item at the given index."""
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None
    
    def expandingDirections(self) -> Qt.Orientation:
        """Layout expands horizontally but not vertically."""
        return Qt.Orientation.Horizontal
    
    def hasHeightForWidth(self) -> bool:
        """Height depends on width due to wrapping behavior."""
        return True
    
    def heightForWidth(self, width: int) -> int:
        """Calculate the total height needed for a given width."""
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect: QRect):
        """Set the geometry and arrange items accordingly."""
        super().setGeometry(rect)
        self._do_layout(rect, False)
    
    def sizeHint(self) -> QSize:
        """Return the preferred size."""
        return self.minimumSize()
    
    def minimumSize(self) -> QSize:
        """Return the minimum size needed."""
        size = QSize()
        
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        
        # Add spacing
        margin_left, margin_top, margin_right, margin_bottom = self.getContentsMargins()
        size += QSize(margin_left + margin_right, margin_top + margin_bottom)
        
        return size
    
    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        """Arrange items in the given rectangle.
        
        Args:
            rect: The available rectangle
            test_only: If True, only calculate height without actually moving items
            
        Returns:
            The total height needed
        """
        margin_left, margin_top, margin_right, margin_bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(margin_left, margin_top, -margin_right, -margin_bottom)
        
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        
        for item in self._item_list:
            widget = item.widget()
            if widget and not widget.isVisible():
                continue
            
            space_x = self.horizontalSpacing()
            space_y = self.verticalSpacing()
            
            # Always use sizeHint - widget.size() can be (0,0) before first show
            item_size = item.sizeHint()
            
            # Check if we need to wrap to next line
            next_x = x + item_size.width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                # Move to next line
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item_size.width() + space_x
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))
            
            x = next_x
            line_height = max(line_height, item_size.height())
        
        return y + line_height - rect.y() + margin_bottom
    
    def horizontalSpacing(self) -> int:
        """Get horizontal spacing between items."""
        if self._hspacing >= 0:
            return self._hspacing
        else:
            # Use smart spacing based on style
            return self.smartSpacing(Qt.Orientation.Horizontal)
    
    def verticalSpacing(self) -> int:
        """Get vertical spacing between items."""
        if self._vspacing >= 0:
            return self._vspacing
        else:
            # Use smart spacing based on style
            return self.smartSpacing(Qt.Orientation.Vertical)
    
    def smartSpacing(self, orientation: Qt.Orientation) -> int:
        """Calculate smart spacing based on the widget's style."""
        parent = self.parent()
        if not parent:
            return -1
        
        if orientation == Qt.Orientation.Horizontal:
            if parent.isWindowType():
                return 10
            else:
                return parent.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal
                )
        else:
            if parent.isWindowType():
                return 10
            else:
                return parent.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical
                )
