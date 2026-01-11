"""
Predictive Threat Simulation (Digital Twin)

Purpose: Models the system state and runs simulated attacks ("Shadow Wars")
to identify vulnerabilities without harming production.

Scope: Logical Simulation (State-Machine based), CPU-friendly.
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SystemState:
    """Represents the Digital Twin's current configuration."""
    firewall_active: bool = True
    db_encryption_active: bool = True
    auth_service_status: str = "healthy" # healthy, degraded, compromised
    open_ports: List[int] = field(default_factory=lambda: [80, 443])
    known_vulnerabilities: List[str] = field(default_factory=list)

@dataclass
class AttackVector:
    """Represents a simulated threat."""
    name: str
    target_component: str
    success_probability: float
    required_condition: dict # e.g. {"firewall_active": False}

@dataclass
class SimulationResult:
    attack_name: str
    success: bool
    compromised_assets: List[str]
    remediation_plan: Optional[str] = None

class DigitalTwin:
    """
    The in-memory replica of the infrastructure's security posture.
    """
    def __init__(self, initial_state: SystemState = None):
        self.state = initial_state or SystemState()

    def apply_attack(self, attack: AttackVector) -> bool:
        """
        Simulates an attack against the current state.
        Returns True if the attack succeeded (system compromised).
        """
        # Check required conditions for attack to be viable
        for key, value in attack.required_condition.items():
            current_val = getattr(self.state, key, None)
            if current_val != value:
                logger.info(f"Attack {attack.name} failed: Condition {key}={value} not met (Current: {current_val})")
                return False

        # Probabilistic outcome
        if random.random() < attack.success_probability:
            logger.warning(f"Attack {attack.name} SUCCEEDED against {attack.target_component}!")
            return True

        return False

class ChaosAgent:
    """
    The entity responsible for running Shadow Wars.
    """
    def __init__(self, twin: DigitalTwin):
        self.twin = twin
        self.attacks_library = [
            AttackVector(
                name="SQLInjection_Unencrypted",
                target_component="database",
                success_probability=0.9,
                required_condition={"db_encryption_active": False}
            ),
            AttackVector(
                name="PortScan_22",
                target_component="network",
                success_probability=0.5,
                required_condition={"firewall_active": False} # Simplified logic
            )
        ]

    def run_simulation(self) -> List[SimulationResult]:
        """
        Runs the full suite of attacks against the digital twin.
        """
        results = []
        for attack in self.attacks_library:
            success = self.twin.apply_attack(attack)
            result = SimulationResult(
                attack_name=attack.name,
                success=success,
                compromised_assets=[attack.target_component] if success else []
            )

            if success:
                result.remediation_plan = self._generate_remediation(attack)

            results.append(result)
        return results

    def _generate_remediation(self, attack: AttackVector) -> str:
        """
        Generates a text-based plan to fix the found vulnerability.
        """
        if attack.name == "SQLInjection_Unencrypted":
            return "Enable Database Encryption immediately."
        if attack.name == "PortScan_22":
            return "Enable Firewall and close unused ports."
        return "Investigate security logs."
