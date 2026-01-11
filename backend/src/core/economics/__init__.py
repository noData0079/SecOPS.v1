"""
Economics Module - Cost control for enterprise autonomy.

Autonomy without cost control = bankruptcy.

Components:
- EconomicGovernor: Budget enforcement, ROI-based prioritization
- CloudOptimizer: FinOps automation for resource shutdown
"""

from .governor import (
    EconomicGovernor,
    CostDecision,
    economic_governor,
)
from .cloud_optimizer import (
    CloudOptimizer,
    CloudResource,
    cloud_optimizer,
)


__all__ = [
    "EconomicGovernor",
    "CostDecision",
    "economic_governor",
    "CloudOptimizer",
    "CloudResource",
    "cloud_optimizer",
]
