"""
DataFrame cleaning and scrubbing logic.

Handles normalization of column names, removal of unsupported PIDs,
and data type conversions.
"""

from typing import Dict, Set
import pandas as pd


def scrub_snapshot(
    raw_df: pd.DataFrame, 
    header_row_idx: int,
    pid_info: Dict[str, Dict[str, str]]
) -> pd.DataFrame:
    """
    Clean and prepare raw snapshot data for analysis.
    
    Args:
        raw_df: Raw DataFrame from snapshot file
        header_row_idx: Index of the header row in the raw data
        pid_info: PID metadata dictionary (may be modified to update units)
        
    Returns:
        Cleaned DataFrame ready for analysis
    """
    # Set column header row
    pid_header = raw_df.iloc[header_row_idx].astype(str).str.strip().tolist()
    df = raw_df.iloc[header_row_idx + 1:].copy()
    df.columns = pid_header

    # Normalize column names: strip whitespace
    df.columns = [str(c).strip() for c in df.columns]

    # Ensure first two columns are named Frame and Time
    if len(df.columns) >= 2:
        new_cols = list(df.columns)
        new_cols[0] = "Frame"
        new_cols[1] = "Time"
        df.columns = new_cols

    # Convert Frame to numeric and trim to start at Frame == 0
    if "Frame" in df.columns:
        df["Frame"] = pd.to_numeric(df["Frame"], errors="coerce")
        start_idx = df.index[df["Frame"] == 0]
        if len(start_idx) > 0:
            df = df.loc[start_idx[0]:].reset_index(drop=True)

    return df


def remove_unsupported_pids(
    df: pd.DataFrame, 
    pid_info: Dict[str, Dict[str, str]]
) -> pd.DataFrame:
    """
    Remove columns that contain 'Not supported' values.
    
    Handles duplicate column names safely and also removes
    the corresponding entries from pid_info.
    
    Args:
        df: DataFrame to clean
        pid_info: PID metadata dictionary (will be modified)
        
    Returns:
        DataFrame with unsupported columns removed
    """
    cols_to_drop: Set[str] = set()
    
    for col in df.columns.unique():
        data = df[col]
        
        # Handle case where column name is duplicated (returns DataFrame)
        if isinstance(data, pd.DataFrame):
            obj_cols = data.select_dtypes(include=['object'])
            if not obj_cols.empty:
                mask = obj_cols.astype(str).apply(
                    lambda x: x.str.contains("Not supported", case=False, regex=False)
                )
                if mask.any().any():
                    cols_to_drop.add(col)
        else:
            # Handle single column (Series)
            if data.dtype == 'object':
                if data.astype(str).str.contains("Not supported", case=False, regex=False).any():
                    cols_to_drop.add(col)
    
    if cols_to_drop:
        df = df.drop(columns=list(cols_to_drop))
        # Also remove from pid_info
        for col in cols_to_drop:
            pid_info.pop(col, None)
                
    return df


def _clean_column_apostrophes(df: pd.DataFrame, col_name: str) -> None:
    """
    Remove leading apostrophes from string values in a specific column.
    Modifies the DataFrame in-place.
    """
    if col_name not in df.columns:
        return
        
    if df[col_name].dtype == 'object':
        df[col_name] = df[col_name].apply(
            lambda x: x[1:] if isinstance(x, str) and x.startswith("'") else x
        )
