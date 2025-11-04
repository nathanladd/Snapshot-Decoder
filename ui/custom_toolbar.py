# Custom matplotlib toolbar for tkinter
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk


class CustomNavigationToolbar(NavigationToolbar2Tk):
    """Custom navigation toolbar that excludes the configure subplots button."""

    def __init__(self, canvas, window, *, pack_toolbar=True):
        super().__init__(canvas, window, pack_toolbar=pack_toolbar)

    # Override toolitems to exclude the Subplots button
    toolitems = [
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        (None, None, None, None),  # separator
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        (None, None, None, None),  # separator
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]
