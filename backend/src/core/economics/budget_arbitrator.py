"""
BudgetArbitrator - Negotiates compute costs vs. security risk.
Tech: Economic Game Theory
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ArbitrationResult:
    decision: str
    allocated_budget: float
    risk_accepted: float

class BudgetArbitrator:
    """
    Uses Game Theory to negotiate between the Security Agent and the Finance Agent.
    """
    def __init__(self):
        self.nash_equilibrium_threshold = 0.6

    def negotiate(self, security_risk_score: float, estimated_cost: float) -> ArbitrationResult:
        """
        Arbitrates the resource allocation.
        risk_score: 0.0 to 1.0 (1.0 is highest risk)
        cost: estimated units
        """
        logger.info(f"Negotiating: Risk={security_risk_score}, Cost={estimated_cost}")

        # Payoff matrix simulation
        # Security wants to minimize risk (maximize budget)
        # Finance wants to minimize cost (minimize budget)

        if security_risk_score > 0.8:
            # High risk overrides cost (Security wins)
            return ArbitrationResult("APPROVED_URGENT", estimated_cost, security_risk_score)

        # Simplified utility calculation
        utility = (security_risk_score * 1000) - estimated_cost

        if utility > 0:
            return ArbitrationResult("APPROVED", estimated_cost, security_risk_score)
        else:
             return ArbitrationResult("DENIED", 0.0, security_risk_score)

budget_arbitrator = BudgetArbitrator()
