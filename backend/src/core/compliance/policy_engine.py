# backend/src/core/compliance/policy_engine.py

"""Policy engine with Rego compatibility for compliance automation."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PolicyFramework(str, Enum):
    """Supported compliance frameworks."""
    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    CUSTOM = "custom"


@dataclass
class Policy:
    """A compliance policy."""
    id: str
    name: str
    framework: PolicyFramework
    description: str
    rules: List[Dict[str, Any]]
    severity: str = "medium"  # low, medium, high, critical
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "framework": self.framework.value,
            "description": self.description,
            "rules": self.rules,
            "severity": self.severity,
            "enabled": self.enabled,
            "metadata": self.metadata
        }


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    policy_id: str
    compliant: bool
    violations: List[Dict[str, Any]]
    evidence: List[str]
    timestamp: datetime
    details: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "compliant": self.compliant,
            "violations_count": len(self.violations),
            "violations": self.violations,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }


class PolicyEngine:
    """
    Policy engine for compliance automation.
    
    Supports Rego-compatible policy definitions and evaluation.
    """
    
    def __init__(self):
        """Initialize policy engine."""
        self.policies: Dict[str, Policy] = {}
        self.evaluation_history: List[PolicyResult] = []
        logger.info("PolicyEngine initialized")
    
    def load_policy(self, policy: Policy) -> None:
        """Load a policy into the engine."""
        self.policies[policy.id] = policy
        logger.info(f"Loaded policy: {policy.name} ({policy.framework.value})")
    
    def load_policies_from_framework(self, framework: PolicyFramework) -> int:
        """Load predefined policies for a compliance framework."""
        policies = self._get_framework_policies(framework)
        for policy in policies:
            self.load_policy(policy)
        logger.info(f"Loaded {len(policies)} policies for {framework.value}")
        return len(policies)
    
    def _get_framework_policies(self, framework: PolicyFramework) -> List[Policy]:
        """Get predefined policies for a framework."""
        if framework == PolicyFramework.SOC2:
            return self._get_soc2_policies()
        elif framework == PolicyFramework.HIPAA:
            return self._get_hipaa_policies()
        elif framework == PolicyFramework.GDPR:
            return self._get_gdpr_policies()
        elif framework == PolicyFramework.PCI_DSS:
            return self._get_pci_policies()
        elif framework == PolicyFramework.ISO27001:
            return self._get_iso27001_policies()
        return []
    
    def _get_soc2_policies(self) -> List[Policy]:
        """SOC2 compliance policies."""
        return [
            Policy(
                id="soc2_access_control_001",
                name="Multi-Factor Authentication Required",
                framework=PolicyFramework.SOC2,
                description="All users must have MFA enabled for access to production systems",
                rules=[
                    {"type": "user_check", "condition": "mfa_enabled == true"},
                    {"type": "system_check", "condition": "enforce_mfa == true"}
                ],
                severity="high",
                metadata={"category": "access_control", "control": "CC6.1"}
            ),
            Policy(
                id="soc2_data_encryption_001",
                name="Data Encryption at Rest",
                framework=PolicyFramework.SOC2,
                description="All sensitive data must be encrypted at rest",
                rules=[
                    {"type": "storage_check", "condition": "encryption_enabled == true"},
                    {"type": "key_management", "condition": "key_rotation_enabled == true"}
                ],
                severity="critical",
                metadata={"category": "data_protection", "control": "CC6.7"}
            ),
            Policy(
                id="soc2_logging_001",
                name="Audit Logging Enabled",
                framework=PolicyFramework.SOC2,
                description="All access to sensitive data must be logged",
                rules=[
                    {"type": "logging_check", "condition": "audit_logs_enabled == true"},
                    {"type": "retention_check", "condition": "log_retention_days >= 90"}
                ],
                severity="high",
                metadata={"category": "monitoring", "control": "CC7.2"}
            )
        ]
    
    def _get_hipaa_policies(self) -> List[Policy]:
        """HIPAA compliance policies."""
        return [
            Policy(
                id="hipaa_phi_encryption_001",
                name="PHI Encryption Required",
                framework=PolicyFramework.HIPAA,
                description="Protected Health Information must be encrypted",
                rules=[
                    {"type": "data_classification", "condition": "phi_identified == true"},
                    {"type": "encryption_check", "condition": "encryption_enabled == true"}
                ],
                severity="critical",
                metadata={"section": "164.312(a)(2)(iv)"}
            ),
            Policy(
                id="hipaa_access_control_001",
                name="PHI Access Controls",
                framework=PolicyFramework.HIPAA,
                description="Access to PHI must be restricted to authorized personnel",
                rules=[
                    {"type": "access_control", "condition": "role_based_access == true"},
                    {"type": "access_logging", "condition": "audit_trail == true"}
                ],
                severity="high",
                metadata={"section": "164.312(a)(1)"}
            )
        ]
    
    def _get_gdpr_policies(self) -> List[Policy]:
        """GDPR compliance policies."""
        return [
            Policy(
                id="gdpr_data_minimization_001",
                name="Data Minimization",
                framework=PolicyFramework.GDPR,
                description="Only collect and process necessary personal data",
                rules=[
                    {"type": "data_inventory", "condition": "purpose_documented == true"},
                    {"type": "retention_check", "condition": "retention_policy_defined == true"}
                ],
                severity="medium",
                metadata={"article": "Article 5(1)(c)"}
            )
        ]
    
    def _get_pci_policies(self) -> List[Policy]:
        """PCI-DSS compliance policies."""
        return [
            Policy(
                id="pci_network_security_001",
                name="Firewall Configuration",
                framework=PolicyFramework.PCI_DSS,
                description="Firewalls must be properly configured",
                rules=[
                    {"type": "network_check", "condition": "firewall_enabled == true"},
                    {"type": "rule_check", "condition": "default_deny == true"}
                ],
                severity="high",
                metadata={"requirement": "1.1"}
            )
        ]
    
    def _get_iso27001_policies(self) -> List[Policy]:
        """ISO 27001 compliance policies."""
        return [
            Policy(
                id="iso27001_access_control_001",
                name="Access Control Policy",
                framework=PolicyFramework.ISO27001,
                description="Access control policy must be documented and enforced",
                rules=[
                    {"type": "policy_check", "condition": "access_policy_exists == true"},
                    {"type": "enforcement_check", "condition": "policy_enforced == true"}
                ],
                severity="medium",
                metadata={"control": "A.9.1.1"}
            )
        ]
    
    async def evaluate_policy(self, policy_id: str, context: Dict[str, Any]) -> PolicyResult:
        """
        Evaluate a policy against current state.
        
        Args:
            policy_id: ID of policy to evaluate
            context: Current system/data state
            
        Returns:
            PolicyResult with evaluation outcome
        """
        if policy_id not in self.policies:
            raise ValueError(f"Policy not found: {policy_id}")
        
        policy = self.policies[policy_id]
        
        if not policy.enabled:
            return PolicyResult(
                policy_id=policy_id,
                compliant=True,
                violations=[],
                evidence=[f"Policy {policy_id} is disabled"],
                timestamp=datetime.utcnow(),
                details="Policy evaluation skipped (disabled)"
            )
        
        # Evaluate each rule
        violations = []
        evidence = []
        
        for rule in policy.rules:
            rule_result = self._evaluate_rule(rule, context)
            
            if not rule_result["passed"]:
                violations.append({
                    "rule_type": rule["type"],
                    "condition": rule["condition"],
                    "actual": rule_result.get("actual"),
                    "message": rule_result.get("message", "Rule violation")
                })
            else:
                evidence.append(f"{rule['type']}: {rule['condition']} ✓")
        
        compliant = len(violations) == 0
        
        result = PolicyResult(
            policy_id=policy_id,
            compliant=compliant,
            violations=violations,
            evidence=evidence,
            timestamp=datetime.utcnow(),
            details=f"Evaluated {len(policy.rules)} rules, {len(violations)} violations found"
        )
        
        self.evaluation_history.append(result)
        logger.info(f"Policy {policy_id} evaluation: {'PASS' if compliant else 'FAIL'}")
        
        return result
    
    def _evaluate_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single rule against context."""
        rule_type = rule["type"]
        condition = rule["condition"]
        
        # Parse condition (simplified - in production, use proper Rego interpreter)
        # Format: "field == value" or "field >= value"
        try:
            if "==" in condition:
                field, expected = [p.strip() for p in condition.split("==")]
                actual = context.get(field)
                passed = str(actual).lower() == expected.lower()
            elif ">=" in condition:
                field, min_val = [p.strip() for p in condition.split(">=")]
                actual = context.get(field, 0)
                passed = int(actual) >= int(min_val)
            elif "<=" in condition:
                field, max_val = [p.strip() for p in condition.split("<=")]
                actual = context.get(field, 0)
                passed = int(actual) <= int(max_val)
            else:
                # Default: check if field exists and is truthy
                field = condition.strip()
                actual = context.get(field)
                passed = bool(actual)
            
            return {
                "passed": passed,
                "actual": actual,
                "expected": condition,
                "message": f"{rule_type} check: {condition}"
            }
        
        except Exception as e:
            logger.error(f"Error evaluating rule {rule_type}: {e}")
            return {
                "passed": False,
                "error": str(e),
                "message": f"Rule evaluation error: {e}"
            }
    
    async def evaluate_all_policies(self, context: Dict[str, Any]) -> List[PolicyResult]:
        """Evaluate all enabled policies."""
        results = []
        for policy_id in self.policies:
            result = await self.evaluate_policy(policy_id, context)
            results.append(result)
        return results
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a specific policy."""
        return self.policies.get(policy_id)
    
    def list_policies(self, framework: Optional[PolicyFramework] = None) -> List[Policy]:
        """List all policies, optionally filtered by framework."""
        policies = list(self.policies.values())
        if framework:
            policies = [p for p in policies if p.framework == framework]
        return policies
    
    def get_stats(self) -> Dict[str, Any]:
        """Get policy engine statistics."""
        total_evaluations = len(self.evaluation_history)
        compliant_evaluations = sum(1 for r in self.evaluation_history if r.compliant)
        
        return {
            "total_policies": len(self.policies),
            "enabled_policies": sum(1 for p in self.policies.values() if p.enabled),
            "total_evaluations": total_evaluations,
            "compliant_evaluations": compliant_evaluations,
            "compliance_rate": compliant_evaluations / total_evaluations if total_evaluations > 0 else 0,
            "frameworks": list(set(p.framework.value for p in self.policies.values()))
        }
