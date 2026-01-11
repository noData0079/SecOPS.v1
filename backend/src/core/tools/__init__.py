"""
Tool Intelligence Module

This is how autonomy becomes COMPETENT, not reckless.

Components:
- ToolMetrics: Usage tracking, blacklisting, cooldowns
- ToolRiskModel: Dynamic, context-aware risk scoring
- ToolSuccessMap: Learn which tools work in which contexts
"""

from .tool_metrics import (
    ToolMetrics,
    ToolMetric,
    tool_metrics,
)

from .tool_risk_model import (
    ToolRiskModel,
    RiskAssessment,
    tool_risk_model,
)

from .tool_success_map import (
    ToolSuccessMap,
    SuccessRecord,
    tool_success_map,
)


__all__ = [
    # Metrics
    "ToolMetrics",
    "ToolMetric",
    "tool_metrics",
    # Risk Model
    "ToolRiskModel",
    "RiskAssessment",
    "tool_risk_model",
    # Success Map
    "ToolSuccessMap",
    "SuccessRecord",
    "tool_success_map",
]
