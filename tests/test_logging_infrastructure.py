"""
Unit tests for the logging infrastructure.

Tests log file creation, rotation, and verbose toggle functionality.
"""

import unittest
import tempfile
import shutil
import logging
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.logging_config import SnapshotLogger, get_logger, set_verbose


class TestLoggingInfrastructure(unittest.TestCase):
    """Test cases for logging infrastructure."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.test_app_name = "TestSnapshotDecoder"
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Test logger creation and basic functionality."""
        # Create logger with custom temp directory
        logger = SnapshotLogger(self.test_app_name)
        
        # Test logger properties
        self.assertEqual(logger.app_name, self.test_app_name)
        self.assertIsInstance(logger.logs_dir, Path)
        self.assertTrue(logger.logs_dir.exists())
        
        # Test logging functions
        logger.logger.debug("Test debug message")
        logger.logger.info("Test info message")
        logger.logger.warning("Test warning message")
        logger.logger.error("Test error message")
        
        # Check if log file was created
        log_file = logger.logs_dir / f"{self.test_app_name.lower()}.log"
        self.assertTrue(log_file.exists())
        
        # Check if custody log was created
        custody_log = logger.logs_dir / "custody.log"
        self.assertTrue(custody_log.exists())
    
    def test_verbose_mode_toggle(self):
        """Test verbose mode toggle functionality."""
        logger = SnapshotLogger(self.test_app_name)
        
        # Test initial state (should be warning level)
        self.assertEqual(logger.console_handler.level, logging.WARNING)
        
        # Enable verbose mode
        logger.set_verbose(True)
        self.assertEqual(logger.console_handler.level, logging.DEBUG)
        
        # Disable verbose mode
        logger.set_verbose(False)
        self.assertEqual(logger.console_handler.level, logging.WARNING)
    
    def test_custody_logging(self):
        """Test custody logging functionality."""
        logger = SnapshotLogger(self.test_app_name)
        
        # Test custody event logging
        logger.log_custody_event("TEST_EVENT", "Test details")
        logger.log_custody_event("ANOTHER_EVENT", "More details", "WARNING")
        
        # Test convenience functions
        logger.log_file_loaded("test.xlsx", 1024000, "ECU_V1", 2.5, 1500)
        logger.log_file_error("bad.xlsx", "File format error")
        logger.log_chart_generated("line", ["pid1", "pid2"], "test.xlsx")
        logger.log_export("PDF", "output.pdf", "test.xlsx")
        
        # Check custody log file
        custody_log = logger.logs_dir / "custody.log"
        self.assertTrue(custody_log.exists())
        
        # Verify log content
        with open(custody_log, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("TEST_EVENT", content)
            self.assertIn("ANOTHER_EVENT", content)
            self.assertIn("FILE_LOADED", content)
            self.assertIn("CHART_GENERATED", content)
    
    def test_global_logger_functions(self):
        """Test global logger convenience functions."""
        # Test get_logger function
        logger1 = get_logger()
        logger2 = get_logger()
        self.assertIs(logger1, logger2)  # Should return same instance
        
        # Test convenience functions
        from infrastructure import debug, info, warning, error
        from infrastructure import log_custody, log_file_loaded
        
        # These should not raise exceptions
        debug("Test debug")
        info("Test info")
        warning("Test warning")
        error("Test error")
        
        log_custody("TEST", "Test details")
        log_file_loaded("test.xlsx", 1024, "ECU_V1", 1.0, 100)
    
    def test_log_file_rotation(self):
        """Test log file rotation setup."""
        logger = SnapshotLogger(self.test_app_name)
        
        # Check if rotating file handler is used
        main_log_handlers = [h for h in logger.logger.handlers 
                            if isinstance(h, logging.handlers.RotatingFileHandler)]
        self.assertGreater(len(main_log_handlers), 0)
        
        # Check rotation parameters
        handler = main_log_handlers[0]
        self.assertEqual(handler.maxBytes, 10*1024*1024)  # 10MB
        self.assertEqual(handler.backupCount, 5)
        
        # Check custody log handler
        custody_handlers = [h for h in logger.custody_log.handlers 
                           if isinstance(h, logging.handlers.RotatingFileHandler)]
        self.assertGreater(len(custody_handlers), 0)
        
        custody_handler = custody_handlers[0]
        self.assertEqual(custody_handler.maxBytes, 5*1024*1024)  # 5MB
        self.assertEqual(custody_handler.backupCount, 3)


if __name__ == "__main__":
    unittest.main()
