"""
Utility functions for the Snapshot Decoder application.

This module contains shared utility functions used across different layers
of the application, including infrastructure concerns like resource path resolution.
"""

import os
import sys


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    When running as a PyInstaller bundle, resources are extracted to a temporary
    directory. This function returns the correct path whether running in development
    or as a bundled executable.
    
    Args:
        relative_path: Path relative to the application root
        
    Returns:
        Absolute path to the resource
    """
    # Check if running as PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
