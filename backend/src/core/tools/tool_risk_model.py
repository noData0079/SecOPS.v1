"""
Tool Risk Model - Dynamic risk scoring per context.

Enables:
- Context-aware risk assessment
- Blast radius estimation
- Safe tool selection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessment:
    """Risk assessment for a tool use."""
    tool: str
    context: Dict[str, Any]
    
    # Risk scores (0-1)
    base_risk: float = 0.5
    contextual_risk: float = 0.5
    historical_risk: float = 0.5
    
    # Final
    final_risk: float = 0.5
    risk_level: str = "medium"  # none, low, medium, high
    
    # Blast radius
    blast_radius: str = "local"  # local, service, cluster, global
    affected_services: List[str] = field(default_factory=list)
    
    # Recommendations
    requires_approval: bool = False
    recommended_alternatives: List[str] = field(default_factory=list)


class ToolRiskModel:
    """
    Dynamic risk assessment for tools.
    
    Risk is NOT static. It depends on:
    - Environment (prod vs dev)
    - Current system state
    - Historical outcomes
    - Time of day (change freeze, etc.)
    """
    
    def __init__(self):
        # Base risk levels (static)
        self.base_risks: Dict[str, float] = {
            "get_logs": 0.0,
            "run_diagnostic": 0.1,
            "restart_service": 0.3,
            "scale_pod": 0.4,
            "update_config": 0.5,
            "apply_patch": 0.7,
            "rollback_deploy": 0.8,
            "escalate": 0.0,
        }
        
        # Blast radius by tool
        self.blast_radius: Dict[str, str] = {
            "get_logs": "local",
            "run_diagnostic": "local",
            "restart_service": "service",
            "scale_pod": "service",
            "update_config": "service",
            "apply_patch": "service",
            "rollback_deploy": "cluster",
            "escalate": "none",
        }
        
        # Historical data (updated by learning)
        self.historical_failure_rates: Dict[str, float] = {}
    
    def assess(
        self,
        tool: str,
        context: Dict[str, Any],
    ) -> RiskAssessment:
        """
        Assess risk for a tool in a given context.
        
        Context should include:
        - environment: "production", "staging", "development"
        - service: which service is affected
        - time: current time (for change freeze detection)
        - incident_severity: how critical is the current incident
        """
        assessment = RiskAssessment(tool=tool, context=context)
        
        # 1. Base risk
        assessment.base_risk = self.base_risks.get(tool, 0.5)
        
        # 2. Contextual risk modifiers
        contextual_modifier = 0.0
        
        # Production is riskier
        if context.get("environment") == "production":
            contextual_modifier += 0.2
        elif context.get("environment") == "development":
            contextual_modifier -= 0.2
        
        # Change freeze periods
        if context.get("change_freeze", False):
            contextual_modifier += 0.3
        
        # Peak hours
        if context.get("peak_hours", False):
            contextual_modifier += 0.1
        
        # Critical incident might justify risk
        if context.get("incident_severity") == "critical":
            contextual_modifier -= 0.15  # More acceptable to take risks
        
        assessment.contextual_risk = max(0, min(1, 
            assessment.base_risk + contextual_modifier
        ))
        
        # 3. Historical risk
        historical_rate = self.historical_failure_rates.get(tool, 0.2)
        assessment.historical_risk = historical_rate
        
        # 4. Final risk (weighted average)
        assessment.final_risk = (
            0.3 * assessment.base_risk +
            0.4 * assessment.contextual_risk +
            0.3 * assessment.historical_risk
        )
        
        # 5. Risk level
        if assessment.final_risk < 0.2:
            assessment.risk_level = "none"
        elif assessment.final_risk < 0.4:
            assessment.risk_level = "low"
        elif assessment.final_risk < 0.7:
            assessment.risk_level = "medium"
        else:
            assessment.risk_level = "high"
        
        # 6. Blast radius
        assessment.blast_radius = self.blast_radius.get(tool, "local")
        
        # 7. Approval requirements
        assessment.requires_approval = (
            assessment.risk_level == "high" or
            (assessment.risk_level == "medium" and context.get("environment") == "production")
        )
        
        # 8. Alternatives
        if assessment.risk_level == "high":
            assessment.recommended_alternatives = self._get_safer_alternatives(tool)
        
        logger.info(
            f"Risk assessment for {tool}: {assessment.risk_level} "
            f"(final={assessment.final_risk:.2f})"
        )
        
        return assessment
    
    def _get_safer_alternatives(self, tool: str) -> List[str]:
        """Get safer alternatives to a high-risk tool."""
        alternatives_map = {
            "rollback_deploy": ["scale_pod", "restart_service"],
            "apply_patch": ["run_diagnostic", "escalate"],
        }
        return alternatives_map.get(tool, ["escalate"])
    
    def update_historical(self, tool: str, failure_rate: float):
        """Update historical failure rate for a tool."""
        self.historical_failure_rates[tool] = failure_rate
    
    def get_safest_tool(
        self,
        available_tools: List[str],
        context: Dict[str, Any],
    ) -> Optional[str]:
        """Get the safest available tool."""
        assessments = [
            (tool, self.assess(tool, context))
            for tool in available_tools
        ]
        
        # Sort by risk
        assessments.sort(key=lambda x: x[1].final_risk)
        
        if assessments:
            return assessments[0][0]
        return None


# Global instance
tool_risk_model = ToolRiskModel()


__all__ = [
    "ToolRiskModel",
    "RiskAssessment",
    "tool_risk_model",
]
