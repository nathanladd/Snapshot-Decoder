"""
Engine system detection logic.

Detects the presence of specific engine systems (EGR, DOC, DPF, SCR, etc.)
based on PIDs found in the snapshot data.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, Tuple
import pandas as pd

from domain.constants import (
    SYSTEM_PIDS,
    V1_SCR_TEMP_PIDS,
    V1_SCR_DIFF_THRESHOLD,
    V1_SCR_TEMP_DIFF_MIN_PCT,
    V1_SCR_TEMP_SWING_MIN_PCT,
)
from domain.snapshot.map_version_decoder import EcuMapInfo
from infrastructure.logging_config import log_debug, log_info, log_warning

# V1 SCR temperature detection only applies to this displacement, and only
# below this horsepower code (00 = highest). See detect_systems().
V1_SCR_DISPLACEMENT = "3.4L"
V1_SCR_MAX_HP_CODE = 4


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

    # True when SCR was detected via the temperature fallback on an engine we
    # could not verify (ECU map version absent/unrecognized). Signals the UI to
    # note the SCR result is based on temperature sensors only.
    scr_temp_unverified: bool = False

    # Store which PIDs matched for each system (for debugging/display)
    matched_pids: dict[str, list[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.matched_pids:
            self.matched_pids = {}


def detect_systems(
    df: pd.DataFrame,
    map_info: Optional[EcuMapInfo] = None,
) -> DetectedSystems:
    """
    Detect which engine systems are present in the snapshot.

    Checks all column names against the SYSTEM_PIDS mapping to determine
    which systems are present.

    Args:
        df: Cleaned snapshot DataFrame
        map_info: Decoded ECU map info, used to gate V1 SCR temperature
            detection. When None (map version absent/unrecognized) the V1
            SCR temperature fallback is skipped.

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
        should_run, unverified = _v1_scr_temp_decision(map_info)
        if should_run:
            scr_present, diff_pct = detect_scr_by_temperature(df)
            systems.scr_temp_diff_pct = diff_pct
            if scr_present:
                systems.scr = True
                systems.scr_temp_unverified = unverified
                systems.matched_pids["scr"] = list(V1_SCR_TEMP_PIDS.values())

    return systems


def _v1_scr_temp_decision(map_info: Optional[EcuMapInfo]) -> Tuple[bool, bool]:
    """
    Decide whether to run V1 SCR temperature detection, and how to trust it.

    Returns ``(should_run, unverified)``:

    - Verified 3.4L engines with a horsepower code below V1_SCR_MAX_HP_CODE
      (00 = highest) run the check as a trusted result -> (True, False).
    - When the ECU map version is absent or unrecognized we cannot confirm the
      engine, so the check still runs but the result is flagged unverified so
      the UI can note it is based on temperature sensors only -> (True, True).
    - A known engine that does not qualify (wrong displacement, or a
      horsepower code at/above the limit) is skipped -> (False, False).
    """
    if map_info is None:
        log_debug(
            "V1 SCR Temp Detection: no ECU map info - running unverified "
            "(temperature sensors only)"
        )
        return True, True

    if map_info.displacement != V1_SCR_DISPLACEMENT:
        log_debug(
            f"V1 SCR Temp Detection: displacement {map_info.displacement} is not "
            f"{V1_SCR_DISPLACEMENT} - skipping"
        )
        return False, False

    hp_code = map_info.horsepower_code
    if hp_code is None or hp_code >= V1_SCR_MAX_HP_CODE:
        log_debug(
            f"V1 SCR Temp Detection: horsepower code {map_info.horsepower!r} is not "
            f"below {V1_SCR_MAX_HP_CODE:02d} - skipping"
        )
        return False, False

    return True, False


def detect_scr_by_temperature(
    df: pd.DataFrame,
    threshold: float = V1_SCR_DIFF_THRESHOLD,
) -> Tuple[bool, Optional[float]]:
    """
    Detect an SCR on V1 engines by comparing inlet and outlet temperatures.

    V1 snapshots lack a dedicated SCR PID (unlike V2's scr_pupmpp), so SCR
    presence is inferred from the inlet/outlet temperatures via two signals:

    1. Divergence: an engine with a real SCR usually shows inlet and outlet
       diverging as exhaust passes through, while an engine without one leaves
       both pegged at the same value. If the two differ by more than
       V1_SCR_TEMP_DIFF_MIN_PCT on at least ``threshold`` of the valid rows,
       the SCR is real.
    2. Swing (fallback): some real SCRs keep inlet and outlet within 5% of each
       other, so signal 1 fails. But the pair still heats up and cools down over
       the run, whereas a no-SCR engine sits pegged at a constant temperature.
       If the paired (averaged) temperature swings across the snapshot by at
       least V1_SCR_TEMP_SWING_MIN_PCT, the SCR is real.

    Either signal is sufficient to switch the SCR on.

    Args:
        df: Cleaned snapshot DataFrame
        threshold: Minimum fraction of differing rows for the divergence signal

    Returns:
        Tuple of (scr_present, diff_fraction). diff_fraction is the fraction of
        rows that diverged (signal 1), or None when the comparison could not run
        (one or both temp PIDs absent, or no rows had both values present).
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

    # Signal 1: inlet vs outlet divergence per row.
    rel_diff = (inlet[valid] - outlet[valid]).abs() / avg.abs()
    different_count = int((rel_diff > V1_SCR_TEMP_DIFF_MIN_PCT).sum())
    diff_fraction = different_count / valid_count
    diverge_detected = diff_fraction >= threshold

    # Signal 2 (fallback): the paired temperature swinging across the snapshot.
    temp_mean = avg.mean()
    temp_swing = (avg.max() - avg.min()) / abs(temp_mean) if temp_mean else 0.0
    swing_detected = temp_swing >= V1_SCR_TEMP_SWING_MIN_PCT

    scr_present = bool(diverge_detected or swing_detected)

    log_info(
        f"V1 SCR Temp Detection: inlet/outlet differ by >{V1_SCR_TEMP_DIFF_MIN_PCT:.0%} on "
        f"{diff_fraction:.1%} of {valid_count} valid rows (threshold {threshold:.0%}); "
        f"paired temp swing {temp_swing:.1%} (threshold {V1_SCR_TEMP_SWING_MIN_PCT:.0%}) -> "
        f"V1 SCR {'DETECTED' if scr_present else 'NOT detected'}"
        f"{' [swing]' if swing_detected and not diverge_detected else ''}"
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
