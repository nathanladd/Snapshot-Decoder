"""
Quick Charts package - Declarative chart definitions.

This package contains pure data definitions for quick charts,
with no UI references or side effects.
"""

from domain.quick_charts.definitions import QuickChartDef, BarChartDef, BubbleChartDef, StatusChartDef
from domain.quick_charts.builders import ChartConfigBuilder
from domain.quick_charts.v1_charts import V1_CHARTS
from domain.quick_charts.v2_charts import V2_CHARTS
from domain.quick_charts.eud_charts import EUD_CHARTS
from domain.quick_charts.reference_charts import REFERENCE_CHARTS

# Combined registry of all quick chart definitions
QUICK_CHART_REGISTRY: dict[str, QuickChartDef] = {}
QUICK_CHART_REGISTRY.update(V1_CHARTS)
QUICK_CHART_REGISTRY.update(V2_CHARTS)
QUICK_CHART_REGISTRY.update(EUD_CHARTS)
QUICK_CHART_REGISTRY.update(REFERENCE_CHARTS)

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
