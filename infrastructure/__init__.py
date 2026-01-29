"""
Infrastructure package - Cross-cutting concerns.

Contains logging, configuration, and other infrastructure services.
"""

from infrastructure.logging_config import setup_logging, get_logger

__all__ = ["setup_logging", "get_logger"]
