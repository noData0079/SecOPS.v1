"""
Economics Module - Cost control for enterprise autonomy.

Autonomy without cost control = bankruptcy.

Components:
- EconomicGovernor: Budget enforcement, ROI-based prioritization
"""

from .governor import (
    EconomicGovernor,
    CostDecision,
    economic_governor,
)


__all__ = [
    "EconomicGovernor",
    "CostDecision",
    "economic_governor",
]
