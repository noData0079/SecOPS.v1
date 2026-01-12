"""
Resource Janitor - FinOps Governor

Manages wallet, monitors "zombie" resources, and autonomously decommissions them.
Generates Autonomous Savings Reports.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)

@dataclass
class CloudResource:
    resource_id: str
    resource_type: str  # "ec2", "rds", "gpu_instance", "s3_bucket"
    state: str          # "running", "stopped", "deleted"
    last_active: float
    cost_per_hour: float

class ResourceJanitor:
    """
    Autonomous cloud-cost optimization.
    """

    def __init__(self):
        self.resources: Dict[str, CloudResource] = {}
        self.total_savings = 0.0

    def scan_and_clean(self) -> Dict[str, Any]:
        """
        Scans for zombie resources and cleans them up.
        Returns a savings report.
        """
        logger.info("Resource Janitor: Starting scan...")

        actions = []
        cycle_savings = 0.0

        for r_id, res in list(self.resources.items()):
            if res.state != "running":
                continue

            if self._is_zombie(res):
                self._decommission(res)
                savings = res.cost_per_hour * 24 * 30 # Monthly savings estimate
                cycle_savings += savings
                self.total_savings += savings
                actions.append({
                    "resource_id": r_id,
                    "action": "decommission",
                    "reason": "Zombie resource (idle)",
                    "estimated_monthly_savings": savings
                })

        report = {
            "timestamp": time.time(),
            "actions": actions,
            "total_cycle_savings": cycle_savings,
            "cumulative_savings": self.total_savings
        }

        if actions:
            logger.info(f"Janitor Report: Saved ${cycle_savings:.2f}/mo. Actions: {len(actions)}")

        return report

    def _is_zombie(self, res: CloudResource) -> bool:
        """
        Determines if a resource is unused.
        """
        idle_time = time.time() - res.last_active

        # Policy: GPU instance idle for > 1 hour
        if res.resource_type == "gpu_instance" and idle_time > 3600:
            return True

        # Policy: Standard instance idle for > 24 hours
        if res.resource_type == "ec2" and idle_time > 86400:
            return True

        return False

    def _decommission(self, res: CloudResource):
        """
        Decommissions the resource.
        """
        res.state = "deleted"
        logger.info(f"Decommissioned {res.resource_id} ({res.resource_type})")

    # -- Mocking tools --
    def register_resource(self, r_id: str, r_type: str, cost: float, last_active_delta: float = 0):
        """Registers a mock resource."""
        self.resources[r_id] = CloudResource(
            resource_id=r_id,
            resource_type=r_type,
            state="running",
            last_active=time.time() - last_active_delta,
            cost_per_hour=cost
        )

# Global instance
resource_janitor = ResourceJanitor()
