"""
Shadow-Execution Environment - The Digital Twin Runner.

Feature: Before applying a security patch or a tool update to production,
TSM99 spins up a "Digital Twin" (a clone of your infra), runs the action,
and checks the OutcomeScorer.

Human Replacement: Replaces the manual QA and Staging approval process.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..outcomes.scorer import ActionOutcome, OutcomeScore, OutcomeScorer

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Result of a shadow execution simulation."""
    outcome: ActionOutcome
    score: OutcomeScore
    simulated_at: datetime = field(default_factory=datetime.now)

    @property
    def passed(self) -> bool:
        """Did the simulation pass the bar?"""
        return self.score.is_positive and self.outcome.success


class ShadowRunner:
    """
    Executes actions in a shadow environment (Digital Twin).

    This component:
    1. Provisions a temporary 'Digital Twin' of the infrastructure.
    2. Executes the proposed action against it.
    3. Scores the outcome using the standardized OutcomeScorer.
    4. Tears down the twin.
    """

    def __init__(
        self,
        tool_executor: Callable[[str, Dict[str, Any]], ActionOutcome],
        scorer: Optional[OutcomeScorer] = None,
    ):
        self.tool_executor = tool_executor
        self.scorer = scorer or OutcomeScorer()

    def simulate(self, tool_name: str, args: Dict[str, Any]) -> SimulationResult:
        """
        Run a simulation of the action.

        Args:
            tool_name: The tool to run.
            args: Arguments for the tool.

        Returns:
            SimulationResult containing outcome and score.
        """
        logger.info(f"Starting shadow simulation for tool: {tool_name}")

        # 1. Provision Digital Twin (Mocked for this implementation)
        self._provision_digital_twin()

        # 2. Prepare Shadow Arguments
        # In a real implementation, this might route traffic to the twin IP
        # or set specific env vars. Here we verify the tool handles '_shadow_mode'.
        shadow_args = args.copy()
        shadow_args["_execution_mode"] = "shadow"

        # 3. Execute Action
        try:
            outcome = self.tool_executor(tool_name, shadow_args)
        except Exception as e:
            logger.error(f"Simulation execution failed: {e}")
            # Create a failure outcome if the executor raised directly
            outcome = ActionOutcome(
                action_id=f"sim-{datetime.now().timestamp()}",
                incident_id="simulation",
                tool_used=tool_name,
                args=args,
                success=False,
                error=str(e)
            )

        # 4. Score Outcome
        score = self.scorer.score(
            outcome,
            context={"environment": "shadow", "simulation": True}
        )

        # 5. Teardown
        self._teardown_digital_twin()

        logger.info(
            f"Simulation complete. Score: {score.score} ({score.category.value}). "
            f"Passed: {score.is_positive}"
        )

        return SimulationResult(outcome=outcome, score=score)

    def _provision_digital_twin(self):
        """Provision the isolated environment."""
        # In a full implementation, this calls Terraform/Docker/Cloud API
        logger.debug("Provisioning Digital Twin (Mock)... DONE")

    def _teardown_digital_twin(self):
        """Clean up the isolated environment."""
        logger.debug("Tearing down Digital Twin (Mock)... DONE")
