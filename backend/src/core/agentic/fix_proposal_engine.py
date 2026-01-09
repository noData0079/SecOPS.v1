# backend/src/core/agentic/fix_proposal_engine.py

"""
Fix Proposal Engine - Layer 6b

Generates:
- Code diffs
- Infra/config changes
- Rollback plans

Still NO execution here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .code_context_engine import CodeContextEngine, ImpactAnalysis

logger = logging.getLogger(__name__)


class FixType(str, Enum):
    """Types of fixes."""
    CODE_CHANGE = "code_change"
    CONFIG_CHANGE = "config_change"
    INFRA_CHANGE = "infra_change"
    DEPENDENCY_UPDATE = "dependency_update"
    POLICY_UPDATE = "policy_update"
    ROLLBACK = "rollback"


class FixRiskLevel(str, Enum):
    """Risk levels for fixes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CodeDiff:
    """A code diff for a fix."""
    file_path: str
    original_content: str
    proposed_content: str
    diff_lines: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "original_lines": len(self.original_content.splitlines()),
            "proposed_lines": len(self.proposed_content.splitlines()),
            "diff": self.diff_lines,
        }


@dataclass
class RollbackPlan:
    """Plan for rolling back a fix."""
    id: str
    description: str
    steps: List[str]
    automated: bool
    estimated_time_minutes: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "steps": self.steps,
            "automated": self.automated,
            "estimated_time_minutes": self.estimated_time_minutes,
        }


@dataclass
class FixProposal:
    """A proposed fix for a finding."""
    
    id: str
    finding_id: str
    fix_type: FixType
    risk_level: FixRiskLevel
    title: str
    description: str
    rationale: str
    code_diffs: List[CodeDiff]
    impact: Optional[ImpactAnalysis]
    rollback_plan: RollbackPlan
    estimated_effort_minutes: int
    auto_approvable: bool
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "fix_type": self.fix_type.value,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "code_diffs": [d.to_dict() for d in self.code_diffs],
            "impact": self.impact.to_dict() if self.impact else None,
            "rollback_plan": self.rollback_plan.to_dict(),
            "estimated_effort_minutes": self.estimated_effort_minutes,
            "auto_approvable": self.auto_approvable,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class FixProposalEngine:
    """
    Generates fix proposals with full context.
    
    Key principle: Generate proposals, don't execute.
    """
    
    def __init__(self, code_context: Optional[CodeContextEngine] = None):
        self._code_context = code_context or CodeContextEngine()
        self._proposals: List[FixProposal] = []
        logger.info("FixProposalEngine initialized")
    
    async def generate_proposal(
        self,
        finding_id: str,
        finding_data: Dict[str, Any],
        fix_suggestion: Dict[str, Any],
    ) -> FixProposal:
        """
        Generate a fix proposal for a finding.
        
        fix_suggestion comes from reasoning orchestrator.
        """
        
        fix_type = self._determine_fix_type(finding_data, fix_suggestion)
        target_files = fix_suggestion.get("files_affected", [])
        
        # Get impact analysis if we have target files
        impact = None
        if target_files and self._code_context:
            impact = await self._code_context.analyze_impact(target_files[0])
        
        # Generate code diffs
        code_diffs = await self._generate_diffs(finding_data, fix_suggestion)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(
            finding_data, impact, code_diffs
        )
        
        # Generate rollback plan
        rollback = self._generate_rollback_plan(fix_type, code_diffs)
        
        # Determine auto-approvability
        auto_approve = self._is_auto_approvable(risk_level, impact)
        
        proposal = FixProposal(
            id=str(uuid4()),
            finding_id=finding_id,
            fix_type=fix_type,
            risk_level=risk_level,
            title=fix_suggestion.get("title", f"Fix for {finding_id}"),
            description=fix_suggestion.get("description", ""),
            rationale=fix_suggestion.get("reasoning", ""),
            code_diffs=code_diffs,
            impact=impact,
            rollback_plan=rollback,
            estimated_effort_minutes=self._estimate_effort(code_diffs),
            auto_approvable=auto_approve,
            created_at=datetime.utcnow(),
        )
        
        self._proposals.append(proposal)
        logger.info(f"Generated proposal {proposal.id} for finding {finding_id}")
        
        return proposal
    
    def _determine_fix_type(
        self,
        finding: Dict[str, Any],
        suggestion: Dict[str, Any],
    ) -> FixType:
        """Determine the type of fix needed."""
        category = finding.get("category", "")
        
        if "config" in category.lower():
            return FixType.CONFIG_CHANGE
        if "infra" in category.lower():
            return FixType.INFRA_CHANGE
        if "dependency" in category.lower():
            return FixType.DEPENDENCY_UPDATE
        if "policy" in category.lower():
            return FixType.POLICY_UPDATE
        
        return FixType.CODE_CHANGE
    
    async def _generate_diffs(
        self,
        finding: Dict[str, Any],
        suggestion: Dict[str, Any],
    ) -> List[CodeDiff]:
        """Generate code diffs for the fix."""
        diffs = []
        
        # Get proposed changes from suggestion
        code_diff = suggestion.get("code_diff", "")
        files = suggestion.get("files_affected", [])
        
        for file_path in files:
            diff = CodeDiff(
                file_path=file_path,
                original_content="",  # Would load actual content
                proposed_content=code_diff,
                diff_lines=code_diff.splitlines() if code_diff else [],
            )
            diffs.append(diff)
        
        return diffs
    
    def _calculate_risk_level(
        self,
        finding: Dict[str, Any],
        impact: Optional[ImpactAnalysis],
        diffs: List[CodeDiff],
    ) -> FixRiskLevel:
        """Calculate risk level of the fix."""
        
        # Base on blast radius
        if impact and impact.blast_radius > 20:
            return FixRiskLevel.CRITICAL
        if impact and impact.blast_radius > 10:
            return FixRiskLevel.HIGH
        if impact and impact.blast_radius > 5:
            return FixRiskLevel.MEDIUM
        
        # Large diffs are riskier
        total_lines = sum(
            len(d.diff_lines) for d in diffs
        )
        if total_lines > 100:
            return FixRiskLevel.HIGH
        if total_lines > 50:
            return FixRiskLevel.MEDIUM
        
        return FixRiskLevel.LOW
    
    def _generate_rollback_plan(
        self,
        fix_type: FixType,
        diffs: List[CodeDiff],
    ) -> RollbackPlan:
        """Generate a rollback plan for the fix."""
        
        if fix_type == FixType.CODE_CHANGE:
            steps = [
                "Revert commit using git revert",
                "Re-run tests to verify rollback",
                "Deploy previous version",
            ]
            automated = True
            time = 5
            
        elif fix_type == FixType.CONFIG_CHANGE:
            steps = [
                "Restore previous configuration from backup",
                "Apply configuration changes",
                "Verify service health",
            ]
            automated = True
            time = 10
            
        elif fix_type == FixType.INFRA_CHANGE:
            steps = [
                "Trigger infrastructure rollback",
                "Verify resource state",
                "Update DNS/routing if needed",
            ]
            automated = False
            time = 30
            
        else:
            steps = [
                "Identify affected changes",
                "Execute manual rollback",
                "Verify system state",
            ]
            automated = False
            time = 60
        
        return RollbackPlan(
            id=str(uuid4()),
            description=f"Rollback plan for {fix_type.value}",
            steps=steps,
            automated=automated,
            estimated_time_minutes=time,
        )
    
    def _is_auto_approvable(
        self,
        risk_level: FixRiskLevel,
        impact: Optional[ImpactAnalysis],
    ) -> bool:
        """Determine if fix can be auto-approved."""
        
        # Only low-risk fixes can be auto-approved
        if risk_level != FixRiskLevel.LOW:
            return False
        
        # Small blast radius
        if impact and impact.blast_radius > 3:
            return False
        
        return True
    
    def _estimate_effort(self, diffs: List[CodeDiff]) -> int:
        """Estimate effort in minutes for the fix."""
        total_lines = sum(len(d.diff_lines) for d in diffs)
        
        # Rough estimate: 1 minute per 5 lines
        return max(5, total_lines // 5)
    
    async def get_proposals_for_finding(
        self, finding_id: str
    ) -> List[FixProposal]:
        """Get all proposals for a finding."""
        return [p for p in self._proposals if p.finding_id == finding_id]
    
    async def get_auto_approvable_proposals(self) -> List[FixProposal]:
        """Get all auto-approvable proposals."""
        return [p for p in self._proposals if p.auto_approvable]
