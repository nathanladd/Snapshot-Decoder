"""
Quick Charts package - Declarative chart definitions.

This package contains pure data definitions for quick charts,
with no UI references or side effects.

================================================================================
WHAT IS THIS FILE?  (`__init__.py`)
================================================================================
The name `__init__.py` is special to Python, not to this app. Any folder that
contains a file with this exact name is treated as a *package* -- something you
can `import`. So because this file exists, other code can write:

    from domain.quick_charts import QUICK_CHART_REGISTRY

Without an `__init__.py`, `domain/quick_charts/` would just be a plain folder and
that import would fail.

Is it a "dunder"?  Yes. "Dunder" = "Double UNDERscore" -- any name wrapped in two
underscores on each side (`__init__`, `__all__`, `__name__`). It's just Python's
naming convention for names that have a *special meaning to the language itself*.
You don't call `__init__.py` directly; Python runs it automatically the first
time the package is imported. (Note: a class's `__init__` *method* is a different
thing that happens to share the dunder name -- this file is unrelated to that.)

================================================================================
WHAT DOES THIS PARTICULAR `__init__.py` DO?
================================================================================
Two jobs, both about convenience for the rest of the app:

1. RE-EXPORT (the imports below). It pulls the most-used names up from the deeper
   modules (`definitions.py`, `builders.py`, `v1_charts.py`, ...) so callers can
   import them from the package's "front door" instead of memorizing which inner
   file each one lives in. Compare:
       from domain.quick_charts import QuickChartDef          # easy (this file)
       from domain.quick_charts.definitions import QuickChartDef   # the long way
   Both work; the first is nicer, and this file is what makes it possible.

2. BUILD THE REGISTRY. It merges the per-architecture chart dictionaries
   (V1/V2/EUD/Reference) into ONE lookup table, `QUICK_CHART_REGISTRY`, keyed by
   `action_id`. This code runs once, on first import, so the registry is assembled
   exactly one time and shared everywhere. (See "action_id - The Quick Chart Join
   Key" for how that key threads through the whole app.)
"""

# --- Job 1: re-export the package's public names from the inner modules ---
# These imports run top-to-bottom the moment the package is first imported.
from domain.quick_charts.definitions import QuickChartDef, BarChartDef, BubbleChartDef, StatusChartDef
from domain.quick_charts.builders import ChartConfigBuilder
from domain.quick_charts.v1_charts import V1_CHARTS
from domain.quick_charts.v2_charts import V2_CHARTS
from domain.quick_charts.eud_charts import EUD_CHARTS
from domain.quick_charts.reference_charts import REFERENCE_CHARTS

# --- Job 2: merge the four per-architecture dicts into one flat lookup table ---
# Start empty, then .update() copies each dict's {action_id: definition} pairs in.
# Later updates would overwrite an earlier key, so action_ids must stay unique
# across V1/V2/EUD/Reference (they all share this one registry).
QUICK_CHART_REGISTRY: dict[str, QuickChartDef] = {}
QUICK_CHART_REGISTRY.update(V1_CHARTS)
QUICK_CHART_REGISTRY.update(V2_CHARTS)
QUICK_CHART_REGISTRY.update(EUD_CHARTS)
QUICK_CHART_REGISTRY.update(REFERENCE_CHARTS)

# `__all__` (also a dunder) is the package's official "public API" list. It only
# affects the wildcard form `from domain.quick_charts import *`, which then binds
# exactly these names. It also signals intent to readers and tools: "these are the
# names meant for outside use." Names NOT listed here are still importable
# explicitly -- `__all__` is a curated front door, not a lock.
__all__ = [
    "QuickChartDef",
    "BarChartDef", 
    "BubbleChartDef",
    "StatusChartDef",
    "ChartConfigBuilder",
    "V1_CHARTS",
    "V2_CHARTS",
    "EUD_CHARTS",
    "REFERENCE_CHARTS",
    "QUICK_CHART_REGISTRY",
]
