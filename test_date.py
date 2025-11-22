import pandas as pd

date_str = "Nov 21 2025/13.20.57"
try:
    dt = pd.to_datetime(date_str)
    print(f"Success: {dt}")
except Exception as e:
    print(f"Failed: {e}")

# Try with format string if auto fails
try:
    # Format: %b %d %Y/%H.%M.%S
    dt = pd.to_datetime(date_str, format="%b %d %Y/%H.%M.%S")
    print(f"Success with format: {dt}")
except Exception as e:
    print(f"Failed with format: {e}")
