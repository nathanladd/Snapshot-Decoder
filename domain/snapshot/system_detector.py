"""
Engine system detection logic.

Detects the presence of specific engine systems (EGR, DOC, DPF, SCR, etc.)
based on PIDs found in the snapshot data.
"""

from dataclasses import dataclass, field
from logging import warning
from typing import Set
import pandas as pd

from domain.constants import SYSTEM_PIDS
from infrastructure.logging_config import debug


@dataclass
class DetectedSystems:
    """
    Container for detected engine systems.
    
    Each boolean attribute indicates whether the corresponding system
    was detected in the snapshot based on the presence of identifying PIDs.
    """
    egr: bool = False
    doc: bool = False
    dpf: bool = False
    scr: bool = False
    air_throttle: bool = False
    mdp: bool = False
    # turbo: bool = False
    
    # Store which PIDs matched for each system (for debugging/display)
    matched_pids: dict[str, list[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.matched_pids:
            self.matched_pids = {}


def detect_systems(df: pd.DataFrame) -> DetectedSystems:
    """
    Detect which engine systems are present in the snapshot.
    
    Checks all column names against the SYSTEM_PIDS mapping to determine
    which systems are present.
    
    Args:
        df: Cleaned snapshot DataFrame
        
    Returns:
        DetectedSystems dataclass with boolean flags for each system
    """
    # Get all column names as lowercase set for matching
    columns_lower: Set[str] = set(
        col.lower().strip() for col in df.columns
    )
    
    debug(f"System Detection: Found {len(columns_lower)} total columns in snapshot")
    
    systems = DetectedSystems()
    
    for system_name, pids in SYSTEM_PIDS.items():
        # Find which PIDs from this system are present
        matched = [pid for pid in pids if pid.lower() in columns_lower]
        missing = [pid for pid in pids if pid.lower() not in columns_lower]
        
        if matched:
            # Set the corresponding attribute to True
            setattr(systems, system_name, True)
            systems.matched_pids[system_name] = matched
            info(f"System Detection: {system_name.upper()} DETECTED - Found PIDs: {matched}")
        else:
            warning(f"System Detection: {system_name.upper()} NOT DETECTED - Missing PIDs: {missing}")
    
    return systems


def get_system_summary(systems: DetectedSystems) -> str:
    """
    Generate a human-readable summary of detected systems.
    
    Args:
        systems: DetectedSystems instance
        
    Returns:
        Formatted string listing detected systems
    """
    detected = []
    
    if systems.egr:
        detected.append("EGR")
    if systems.doc:
        detected.append("DOC")
    if systems.dpf:
        detected.append("DPF")
    if systems.scr:
        detected.append("SCR")
    if systems.air_throttle:
        detected.append("Air Throttle")
    if systems.mdp:
        detected.append("MDP")
    # if systems.turbo:
    #     detected.append("Turbo")
    
    if detected:
        return "Detected systems: " + ", ".join(detected)
    else:
        return "No aftertreatment systems detected"
