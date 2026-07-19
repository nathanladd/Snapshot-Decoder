"""
Per-user writable data directory.

Installed builds run from Program Files, which is not writable by a
standard user. Settings, My Charts, and any future per-user JSON stores
must live under %APPDATA%\\SnapshotDecoder\\ instead.
"""

import os
import sys

APP_DIR_NAME = "SnapshotDecoder"


def user_data_dir() -> str:
    """Per-user writable dir for settings, My Charts, etc. Created on demand."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    path = os.path.join(base, APP_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def user_data_file(filename: str) -> str:
    """Full path to `filename` inside the per-user data directory."""
    return os.path.join(user_data_dir(), filename)
