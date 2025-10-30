"""
Time conversion utilities for Snapshot Decoder.
"""

def seconds_to_hours(seconds: float) -> float:
    """
    Convert seconds to hours, rounded to the tenth of an hour.
    
    Args:
        seconds (float): Number of seconds.
    
    Returns:
        float: Hours rounded to 1 decimal place.
    """
    return round(seconds / 3600, 1)

def seconds_to_min_sec(seconds: int) -> str:
    """
    Convert total seconds to minutes and seconds format (MM:SS).
    
    Args:
        seconds (int): Total number of seconds.
    
    Returns:
        str: Formatted time as "MM:SS".
    """
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"
