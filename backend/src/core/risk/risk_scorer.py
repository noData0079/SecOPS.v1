# backend/src/core/risk/risk_scorer.py

"""Risk scoring engine with CVSS integration and business impact assessment."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskCategory(str, Enum):
    """Risk categories."""
    VULNERABILITY = "vulnerability"
    CONFIGURATION = "configuration"
    COMPLIANCE = "compliance"
    ACCESS = "access"
    DATA = "data"
    OPERATIONAL = "operational"
    SUPPLY_CHAIN = "supply_chain"


@dataclass
class RiskFactor:
    """A factor contributing to risk."""
    name: str
    category: RiskCategory
    weight: float  # 0.0 to 1.0
    score: float  # 0.0 to 10.0
    description: str = ""
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    
    @property
    def weighted_score(self) -> float:
        return self.weight * self.score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "weight": self.weight,
            "score": self.score,
            "weighted_score": self.weighted_score,
            "description": self.description,
            "evidence": self.evidence,
            "remediation": self.remediation,
        }


@dataclass
class RiskScore:
    """Aggregated risk score for an asset or finding."""
    asset_id: str
    asset_name: str
    overall_score: float  # 0.0 to 10.0
    risk_level: RiskLevel
    factors: List[RiskFactor] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    business_impact: float = 5.0  # 0.0 to 10.0
    exploitability: float = 5.0  # 0.0 to 10.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "overall_score": round(self.overall_score, 2),
            "risk_level": self.risk_level.value,
            "factors": [f.to_dict() for f in self.factors],
            "factors_count": len(self.factors),
            "by_category": self._factors_by_category(),
            "calculated_at": self.calculated_at.isoformat(),
            "business_impact": self.business_impact,
            "exploitability": self.exploitability,
            "metadata": self.metadata,
        }
    
    def _factors_by_category(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for f in self.factors:
            counts[f.category.value] = counts.get(f.category.value, 0) + 1
        return counts


class RiskScorer:
    """
    Risk scoring engine for security assessments.
    
    Features:
    - CVSS-based vulnerability scoring
    - Business impact multipliers
    - Asset criticality weighting
    - Aggregated risk calculations
    - Historical trend analysis
    """
    
    # Default weights for different risk categories
    DEFAULT_CATEGORY_WEIGHTS = {
        RiskCategory.VULNERABILITY: 1.0,
        RiskCategory.CONFIGURATION: 0.8,
        RiskCategory.COMPLIANCE: 0.7,
        RiskCategory.ACCESS: 0.9,
        RiskCategory.DATA: 1.0,
        RiskCategory.OPERATIONAL: 0.6,
        RiskCategory.SUPPLY_CHAIN: 0.85,
    }
    
    # Score thresholds for risk levels
    RISK_THRESHOLDS = {
        RiskLevel.CRITICAL: 9.0,
        RiskLevel.HIGH: 7.0,
        RiskLevel.MEDIUM: 4.0,
        RiskLevel.LOW: 1.0,
        RiskLevel.INFO: 0.0,
    }
    
    def __init__(
        self,
        category_weights: Optional[Dict[RiskCategory, float]] = None,
        business_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize risk scorer.
        
        Args:
            category_weights: Custom category weights
            business_context: Business context for impact calculations
        """
        self.category_weights = category_weights or self.DEFAULT_CATEGORY_WEIGHTS.copy()
        self.business_context = business_context or {}
        self._history: List[RiskScore] = []
        
        logger.info("RiskScorer initialized")
    
    def calculate_risk(
        self,
        asset_id: str,
        asset_name: str,
        factors: List[RiskFactor],
        business_impact: float = 5.0,
        asset_criticality: float = 5.0,
    ) -> RiskScore:
        """
        Calculate overall risk score for an asset.
        
        Args:
            asset_id: Unique asset identifier
            asset_name: Human-readable asset name
            factors: List of risk factors
            business_impact: Business impact score (0-10)
            asset_criticality: Asset criticality score (0-10)
            
        Returns:
            RiskScore with aggregated risk
        """
        if not factors:
            return RiskScore(
                asset_id=asset_id,
                asset_name=asset_name,
                overall_score=0.0,
                risk_level=RiskLevel.INFO,
                business_impact=business_impact,
            )
        
        # Calculate weighted score
        total_weight = sum(f.weight * self.category_weights.get(f.category, 1.0) for f in factors)
        weighted_sum = sum(
            f.weighted_score * self.category_weights.get(f.category, 1.0)
            for f in factors
        )
        
        if total_weight > 0:
            base_score = weighted_sum / total_weight
        else:
            base_score = sum(f.score for f in factors) / len(factors)
        
        # Apply business impact and criticality multipliers
        impact_multiplier = 0.5 + (business_impact / 20)  # 0.5 to 1.0
        criticality_multiplier = 0.5 + (asset_criticality / 20)  # 0.5 to 1.0
        
        overall_score = min(10.0, base_score * impact_multiplier * criticality_multiplier)
        
        # Calculate exploitability
        vuln_factors = [f for f in factors if f.category == RiskCategory.VULNERABILITY]
        exploitability = sum(f.score for f in vuln_factors) / len(vuln_factors) if vuln_factors else 5.0
        
        # Determine risk level
        risk_level = self._get_risk_level(overall_score)
        
        score = RiskScore(
            asset_id=asset_id,
            asset_name=asset_name,
            overall_score=overall_score,
            risk_level=risk_level,
            factors=factors,
            business_impact=business_impact,
            exploitability=exploitability,
        )
        
        self._history.append(score)
        logger.info(f"Calculated risk for {asset_name}: {overall_score:.2f} ({risk_level.value})")
        
        return score
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score."""
        for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
            if score >= self.RISK_THRESHOLDS[level]:
                return level
        return RiskLevel.INFO
    
    def calculate_cvss_score(
        self,
        attack_vector: str = "N",
        attack_complexity: str = "L",
        privileges_required: str = "N",
        user_interaction: str = "N",
        scope: str = "U",
        confidentiality_impact: str = "H",
        integrity_impact: str = "H",
        availability_impact: str = "H",
    ) -> float:
        """
        Calculate CVSS v3.1 base score.
        
        Args:
            attack_vector: N(etwork), A(djacent), L(ocal), P(hysical)
            attack_complexity: L(ow), H(igh)
            privileges_required: N(one), L(ow), H(igh)
            user_interaction: N(one), R(equired)
            scope: U(nchanged), C(hanged)
            confidentiality_impact: N(one), L(ow), H(igh)
            integrity_impact: N(one), L(ow), H(igh)
            availability_impact: N(one), L(ow), H(igh)
            
        Returns:
            CVSS base score (0.0 to 10.0)
        """
        # Metric values
        AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
        AC = {"L": 0.77, "H": 0.44}
        PR_U = {"N": 0.85, "L": 0.62, "H": 0.27}
        PR_C = {"N": 0.85, "L": 0.68, "H": 0.5}
        UI = {"N": 0.85, "R": 0.62}
        C = {"N": 0, "L": 0.22, "H": 0.56}
        I = {"N": 0, "L": 0.22, "H": 0.56}
        A = {"N": 0, "L": 0.22, "H": 0.56}
        
        # Get values
        av = AV.get(attack_vector.upper(), 0.85)
        ac = AC.get(attack_complexity.upper(), 0.77)
        
        PR = PR_C if scope.upper() == "C" else PR_U
        pr = PR.get(privileges_required.upper(), 0.85)
        
        ui = UI.get(user_interaction.upper(), 0.85)
        c = C.get(confidentiality_impact.upper(), 0.56)
        i = I.get(integrity_impact.upper(), 0.56)
        a = A.get(availability_impact.upper(), 0.56)
        
        # Calculate ISS (Impact Sub-Score)
        iss = 1 - ((1 - c) * (1 - i) * (1 - a))
        
        # Calculate Impact
        if scope.upper() == "U":
            impact = 6.42 * iss
        else:
            impact = 7.52 * (iss - 0.029) - 3.25 * pow((iss - 0.02), 15)
        
        # Calculate Exploitability
        exploitability = 8.22 * av * ac * pr * ui
        
        # Calculate Base Score
        if impact <= 0:
            return 0.0
        
        if scope.upper() == "U":
            base_score = min(10, exploitability + impact)
        else:
            base_score = min(10, 1.08 * (exploitability + impact))
        
        # Round up to 1 decimal place
        return math.ceil(base_score * 10) / 10
    
    def create_vulnerability_factor(
        self,
        name: str,
        cvss_score: float,
        description: str = "",
        remediation: Optional[str] = None,
    ) -> RiskFactor:
        """
        Create a risk factor from a vulnerability.
        
        Args:
            name: Vulnerability name
            cvss_score: CVSS score (0-10)
            description: Vulnerability description
            remediation: Remediation guidance
            
        Returns:
            RiskFactor
        """
        # Weight based on CVSS score
        if cvss_score >= 9.0:
            weight = 1.0
        elif cvss_score >= 7.0:
            weight = 0.9
        elif cvss_score >= 4.0:
            weight = 0.7
        else:
            weight = 0.5
        
        return RiskFactor(
            name=name,
            category=RiskCategory.VULNERABILITY,
            weight=weight,
            score=cvss_score,
            description=description,
            remediation=remediation,
        )
    
    def create_compliance_factor(
        self,
        name: str,
        framework: str,
        control_id: str,
        compliant: bool,
        description: str = "",
    ) -> RiskFactor:
        """
        Create a risk factor from a compliance check.
        
        Args:
            name: Check name
            framework: Compliance framework (e.g., SOC2, HIPAA)
            control_id: Control identifier
            compliant: Whether control is satisfied
            description: Check description
            
        Returns:
            RiskFactor
        """
        score = 0.0 if compliant else 6.0
        weight = 0.7
        
        return RiskFactor(
            name=name,
            category=RiskCategory.COMPLIANCE,
            weight=weight,
            score=score,
            description=description,
            evidence=f"{framework} control {control_id}",
        )
    
    def aggregate_scores(self, scores: List[RiskScore]) -> Dict[str, Any]:
        """
        Aggregate multiple risk scores into summary statistics.
        
        Args:
            scores: List of RiskScore objects
            
        Returns:
            Aggregated statistics
        """
        if not scores:
            return {
                "total_assets": 0,
                "avg_risk_score": 0.0,
                "max_risk_score": 0.0,
                "by_risk_level": {},
            }
        
        total = len(scores)
        avg = sum(s.overall_score for s in scores) / total
        max_score = max(s.overall_score for s in scores)
        
        by_level = {level.value: 0 for level in RiskLevel}
        for s in scores:
            by_level[s.risk_level.value] += 1
        
        return {
            "total_assets": total,
            "avg_risk_score": round(avg, 2),
            "max_risk_score": round(max_score, 2),
            "by_risk_level": by_level,
            "critical_count": by_level.get("critical", 0),
            "high_count": by_level.get("high", 0),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    def get_trend(self, asset_id: str, lookback: int = 10) -> List[Dict[str, Any]]:
        """
        Get historical risk trend for an asset.
        
        Args:
            asset_id: The asset ID
            lookback: Number of historical scores to include
            
        Returns:
            List of historical scores
        """
        asset_history = [s for s in self._history if s.asset_id == asset_id]
        recent = asset_history[-lookback:] if len(asset_history) > lookback else asset_history
        
        return [
            {
                "score": round(s.overall_score, 2),
                "level": s.risk_level.value,
                "timestamp": s.calculated_at.isoformat(),
            }
            for s in recent
        ]
