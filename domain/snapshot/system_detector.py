"""
Engine system detection logic.

Detects the presence of specific engine systems (EGR, DOC, DPF, SCR, etc.)
based on PIDs found in the snapshot data.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, Tuple
import pandas as pd

from domain.constants import SYSTEM_PIDS, V1_SCR_TEMP_PIDS, V1_SCR_DIFF_THRESHOLD, V1_SCR_TEMP_DIFF_MIN_PCT
from infrastructure.logging_config import log_debug, log_info, log_warning


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

    # Fraction of valid rows where the V1 SCR inlet/outlet temps differed.
    # None when the temperature comparison did not run (PIDs absent or no
    # valid rows). Populated for display/diagnostics even when below threshold.
    scr_temp_diff_pct: Optional[float] = None

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
    
    log_debug(f"System Detection: Found {len(columns_lower)} total columns in snapshot")
    
    systems = DetectedSystems()
    
    for system_name, pids in SYSTEM_PIDS.items():
        # Find which PIDs from this system are present
        matched = [pid for pid in pids if pid.lower() in columns_lower]
        missing = [pid for pid in pids if pid.lower() not in columns_lower]
        
        # The SCR entry in SYSTEM_PIDS is the V2 PID (scr_pupmpp); V1 SCR is
        # detected separately below via temperature comparison.
        label = "V2 SCR" if system_name == "scr" else system_name.upper()

        if matched:
            # Set the corresponding attribute to True
            setattr(systems, system_name, True)
            systems.matched_pids[system_name] = matched
            log_info(f"System Detection: {label} DETECTED - Found PIDs: {matched}")
        else:
            log_warning(f"System Detection: {label} NOT DETECTED - Missing PIDs: {missing}")

    # V1 engines have no dedicated SCR PID, so fall back to comparing the SCR
    # inlet/outlet temperatures. Only needed when SCR was not already found above.
    if not systems.scr:
        scr_present, diff_pct = detect_scr_by_temperature(df)
        systems.scr_temp_diff_pct = diff_pct
        if scr_present:
            systems.scr = True
            systems.matched_pids["scr"] = list(V1_SCR_TEMP_PIDS.values())

    return systems


def detect_scr_by_temperature(
    df: pd.DataFrame,
    threshold: float = V1_SCR_DIFF_THRESHOLD,
) -> Tuple[bool, Optional[float]]:
    """
    Detect an SCR on V1 engines by comparing inlet and outlet temperatures.

    V1 snapshots lack a dedicated SCR PID (unlike V2's scr_pupmpp). However, an
    engine with a real SCR shows its inlet and outlet temperatures diverging as
    exhaust passes through, while an engine without one leaves both readings
    pegged at the same value. This computes the fraction of rows (where both
    temps are present) on which the two differ; a high fraction means the SCR
    is real and should be switched on.

    Args:
        df: Cleaned snapshot DataFrame
        threshold: Minimum fraction of differing rows to conclude an SCR exists

    Returns:
        Tuple of (scr_present, diff_fraction). diff_fraction is None when the
        comparison could not run (one or both temp PIDs absent, or no rows had
        both values present).
    """
    # Map lowercased -> actual column name to match PIDs case-insensitively.
    columns_by_lower = {col.lower().strip(): col for col in df.columns}

    inlet_col = columns_by_lower.get(V1_SCR_TEMP_PIDS["inlet"].lower())
    outlet_col = columns_by_lower.get(V1_SCR_TEMP_PIDS["outlet"].lower())

    if inlet_col is None or outlet_col is None:
        log_debug(
            "V1 SCR Temp Detection: inlet/outlet temp PIDs not both present "
            f"({V1_SCR_TEMP_PIDS['inlet']}, {V1_SCR_TEMP_PIDS['outlet']}) - skipping"
        )
        return False, None

    inlet = pd.to_numeric(df[inlet_col], errors="coerce")
    outlet = pd.to_numeric(df[outlet_col], errors="coerce")

    # Only rows where both temps are real numbers are comparable.
    valid = inlet.notna() & outlet.notna()
    valid_count = int(valid.sum())

    if valid_count == 0:
        log_warning(
            "V1 SCR Temp Detection: temp PIDs present but no rows had both values - skipping"
        )
        return False, None

    avg = (inlet[valid] + outlet[valid]) / 2
    rel_diff = (inlet[valid] - outlet[valid]).abs() / avg.abs()
    different_count = int((rel_diff > V1_SCR_TEMP_DIFF_MIN_PCT).sum())
    diff_fraction = different_count / valid_count
    scr_present = diff_fraction >= threshold

    log_info(
        f"V1 SCR Temp Detection: inlet/outlet differ by >{V1_SCR_TEMP_DIFF_MIN_PCT:.0%} on "
        f"{diff_fraction:.1%} of {valid_count} valid rows (threshold {threshold:.0%}) -> "
        f"V1 SCR {'DETECTED' if scr_present else 'NOT detected'}"
    )

    return scr_present, diff_fraction


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
