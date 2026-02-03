#!/usr/bin/env python3
"""
Test script for the logging infrastructure.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure import (
    get_logger, set_verbose, log_custody, log_file_loaded, 
    log_file_error, log_chart_generated, debug, info, warning, error
)


def test_logging_infrastructure():
    """Test the logging infrastructure components."""
    
    print("Testing logging infrastructure...")
    
    # Test basic logger setup
    logger = get_logger()
    print(f"✅ Logger created: {logger.app_name}")
    print(f"✅ Logs directory: {logger.logs_dir}")
    
    # Test logging functions
    debug("Debug message test")
    info("Info message test")
    warning("Warning message test")
    error("Error message test")
    
    # Test custody logging
    log_custody("TEST_EVENT", "Test details for logging")
    log_custody("ANOTHER_EVENT", "More details", "WARNING")
    
    # Test file loading logging
    log_file_loaded("test_file.xlsx", 1024000, "ECU_V1", 2.5, 1500)
    log_file_error("bad_file.xlsx", "File format not supported")
    
    # Test chart generation logging
    log_chart_generated("line", ["pid1", "pid2", "pid3"], "test_file.xlsx")
    
    # Test verbose mode toggle
    print("\nTesting verbose mode...")
    set_verbose(True)
    debug("This should appear in console (verbose mode)")
    
    set_verbose(False)
    debug("This should NOT appear in console (non-verbose mode)")
    warning("This warning should still appear")
    
    print("\n✅ All logging tests completed!")
    
    # Show log file locations
    main_log = logger.logs_dir / "snapshotdecoder.log"
    custody_log = logger.logs_dir / "custody.log"
    
    print(f"\n📁 Log files created:")
    print(f"   Main log: {main_log}")
    print(f"   Custody log: {custody_log}")
    
    # Show some log content
    if main_log.exists():
        print(f"\n📄 Main log preview (last 5 lines):")
        with open(main_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(f"   {line.strip()}")
    
    if custody_log.exists():
        print(f"\n📄 Custody log preview (last 5 lines):")
        with open(custody_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(f"   {line.strip()}")


if __name__ == "__main__":
    test_logging_infrastructure()
