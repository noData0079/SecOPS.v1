"""
Resource Arbiter - Autonomous Resource Management for TSM99.

Manages system resources (GPU, memory) and arbitrates between tasks
to protect the Sovereign Core.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ResourceStatus:
    gpu_memory_used_percent: float
    system_memory_used_percent: float
    cpu_usage_percent: float
    is_critical_state: bool


class ResourceArbiter:
    """
    Arbitrates resource usage to protect the Sovereign Core.

    Features:
    - Monitors resource usage (GPU, RAM)
    - Enforces "Sovereign Core" protection (killing non-critical tasks)
    - Decides if new tasks can run
    """

    def __init__(self, simulation_file: Optional[Path] = None):
        # Use a path relative to this file or fallback to a safe location
        base_path = Path(__file__).resolve().parent.parent.parent.parent.parent # up to backend/
        self.simulation_file = simulation_file or (base_path / "data/simulated_gpu_usage")

        # Critical thresholds
        self.gpu_critical_threshold = 90.0
        self.memory_critical_threshold = 90.0

        # Protected task categories (Sovereign Core)
        self.protected_categories = {"security", "sovereign_core", "critical_infra"}

    def monitor_resources(self) -> ResourceStatus:
        """
        Monitor system resources.

        In this environment, we simulate GPU usage via a file or env var
        since we don't have real GPU access.
        """
        gpu_usage = 0.0

        # Check simulation file
        if self.simulation_file.exists():
            try:
                content = self.simulation_file.read_text().strip()
                gpu_usage = float(content)
            except Exception:
                pass

        # Check env var (override)
        if os.environ.get("SIMULATED_GPU_USAGE"):
            try:
                gpu_usage = float(os.environ["SIMULATED_GPU_USAGE"])
            except ValueError:
                pass

        is_critical = gpu_usage > self.gpu_critical_threshold

        return ResourceStatus(
            gpu_memory_used_percent=gpu_usage,
            system_memory_used_percent=50.0, # Placeholder
            cpu_usage_percent=30.0, # Placeholder
            is_critical_state=is_critical
        )

    def should_allow_task(self, task_category: str) -> bool:
        """
        Decide if a task should run based on current resources.

        Args:
            task_category: Category of the task (security, reliability, etc.)

        Returns:
            True if allowed, False if denied (to protect core)
        """
        status = self.monitor_resources()

        if not status.is_critical_state:
            return True

        # If critical, only allow protected categories
        if task_category in self.protected_categories:
            logger.info(f"Allowing critical task {task_category} despite low resources")
            return True

        logger.warning(
            f"Denying task {task_category} due to critical resource usage "
            f"(GPU: {status.gpu_memory_used_percent}%)"
        )
        return False

# Global instance
resource_arbiter = ResourceArbiter()
