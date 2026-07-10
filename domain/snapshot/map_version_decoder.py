"""
ECU Map Version decoding.

Decodes Bobcat ECU Map Version strings from the snapshot header
(e.g. "DL01_LEL00_B14_UNE52D") into engine displacement, machine
subtype, and horsepower setting.

Format:
    <BaseEngineType>_<Subtype><HP>_<software version...>
    - BaseEngineType: 2 letters (DL = V1, DM = V2) + 2 digits
      (01 = 1.8L, 02 = 2.4L, 03 = 3.4L)
    - Subtype: 3 letters (LEL = Loader, LEE = MX, LEU = Toolcat,
      LEV = Versahandler)
    - HP: 2-digit relative horsepower setting (00 = highest)
    - Remainder is the ECU software version and is ignored.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

# BaseEngineType letter prefix -> engine version
ENGINE_VERSIONS = {
    "DL": "V1",
    "DM": "V2",
}

# BaseEngineType digits -> displacement
DISPLACEMENTS = {
    "01": "1.8L",
    "02": "2.4L",
    "03": "3.4L",
}

# Subtype code -> machine family
SUBTYPES = {
    "LEL": "Loader",
    "LEE": "MX",
    "LEU": "Toolcat",
    "LEV": "Versahandler",
}

# Header labels that carry the map version (see HEADER_LABELS in domain/constants.py)
_MAP_VERSION_LABELS = ("ECU Map Version", "Map Version")

# <2 letters><2 digits>_<3 letters><2 digits>[_<ignored software version>]
_MAP_VERSION_PATTERN = re.compile(r"^([A-Z]{2})(\d{2})_([A-Z]{3})(\d{2})(?:_.*)?$")


@dataclass
class EcuMapInfo:
    """Decoded fields from a Bobcat ECU Map Version string."""
    map_version: str          # Raw string as read from the header
    base_engine_type: str     # e.g. "DL01"
    engine_version: str       # "V1" or "V2"
    displacement: str         # e.g. "1.8L"
    subtype_code: str         # e.g. "LEL" (raw code, even if unrecognized)
    subtype: str              # e.g. "Loader" (falls back to the raw code)
    horsepower: str           # 2-digit relative setting, e.g. "00"

    @property
    def subtype_recognized(self) -> bool:
        """True if the subtype code matched a known machine family."""
        return self.subtype_code in SUBTYPES


def decode_map_version(value: str) -> Optional[EcuMapInfo]:
    """
    Decode an ECU Map Version string into an EcuMapInfo.

    Returns None if the string does not match the Bobcat map version
    format or uses an unknown engine prefix/displacement code. An
    unknown subtype code still decodes, with the raw code as subtype.
    """
    if not value:
        return None

    normalized = value.strip().upper()
    match = _MAP_VERSION_PATTERN.match(normalized)
    if not match:
        return None

    prefix, digits, subtype_code, horsepower = match.groups()

    engine_version = ENGINE_VERSIONS.get(prefix)
    displacement = DISPLACEMENTS.get(digits)
    if engine_version is None or displacement is None:
        return None

    return EcuMapInfo(
        map_version=value.strip(),
        base_engine_type=prefix + digits,
        engine_version=engine_version,
        displacement=displacement,
        subtype_code=subtype_code,
        subtype=SUBTYPES.get(subtype_code, subtype_code),
        horsepower=horsepower,
    )


def find_map_version(header_list: List[Tuple[str, str]]) -> str:
    """
    Find the ECU Map Version value in the parsed header list.

    Args:
        header_list: List of (label, value) tuples from parse_header

    Returns:
        Map version string if found, empty string otherwise
    """
    for label, value in header_list:
        if label in _MAP_VERSION_LABELS:
            return value
    return ""
