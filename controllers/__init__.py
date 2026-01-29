"""
Controllers package - Application layer orchestration.

Contains UI-agnostic controllers that coordinate domain operations
and communicate via Qt signals.
"""

from controllers.snapshot_loader import SnapshotLoader

__all__ = ["SnapshotLoader"]
