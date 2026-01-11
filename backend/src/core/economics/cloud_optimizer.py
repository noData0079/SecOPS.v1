"""
Cloud Optimizer - FinOps Autonomy

Monitors spend and optimizes resources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CloudResource:
    resource_id: str
    resource_type: str  # "ec2", "rds", "gpu_instance"
    state: str          # "running", "stopped"
    cpu_usage_pct: float
    idle_time_hours: float
    cost_per_hour: float
    tags: Dict[str, str]


class CloudOptimizer:
    """
    Monitors cloud resources and shuts down waste.

    Features:
    - Idle resource detection
    - GPU instance watchdog
    - Automated shutdown
    - Spend reporting
    """

    def __init__(self):
        # Mocked cloud state
        self.resources: Dict[str, CloudResource] = {}
        self.total_saved = 0.0

    def scan_resources(self) -> List[str]:
        """
        Scan for idle resources and take action.
        Returns a list of actions taken.
        """
        actions_taken = []

        for r_id, resource in list(self.resources.items()):
            if resource.state != "running":
                continue

            if self._should_shutdown(resource):
                self.shutdown_resource(r_id)
                saved = resource.cost_per_hour * 24  # Estimate daily savings
                self.total_saved += saved
                actions_taken.append(f"Shutdown {resource.resource_type} {r_id} (Idle {resource.idle_time_hours}h). Est. savings: ${saved:.2f}/day")

        if actions_taken:
            self.send_summary_report(actions_taken)

        return actions_taken

    def _should_shutdown(self, resource: CloudResource) -> bool:
        """Determine if a resource should be shut down."""
        # Policy: Shutdown GPU instances if idle > 1 hour
        if "gpu" in resource.resource_type.lower() and resource.idle_time_hours > 1.0:
            return True

        # Policy: Shutdown regular instances if idle > 4 hours
        if resource.idle_time_hours > 4.0:
            return True

        return False

    def shutdown_resource(self, resource_id: str):
        """Simulate shutting down a resource."""
        if resource_id in self.resources:
            self.resources[resource_id].state = "stopped"
            logger.info(f"CloudOptimizer shutting down {resource_id}")

    def send_summary_report(self, actions: List[str]):
        """Simulate sending a report."""
        report = "CLOUD OPTIMIZER REPORT:\n" + "\n".join(actions)
        logger.info(report)
        # In real system: email or slack webhook

    # -- Methods to mock/populate data for testing --
    def add_resource(self, resource: CloudResource):
        self.resources[resource.resource_id] = resource


# Global instance
cloud_optimizer = CloudOptimizer()
