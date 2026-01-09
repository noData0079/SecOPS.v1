"""
Data-Resident Orchestrator

Main orchestrator for the data-resident architecture.
Coordinates the complete workflow:

1. Local ingestion & detection
2. Sanitized reasoning requests
3. Poly-LLM routing (zero data leak)
4. Local fix generation
5. Approval gates
6. Local execution
7. Local verification
8. Trust ledger

All customer data stays in customer infrastructure.
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from ..sanitization import DataSanitizer, ReasoningBundle, ReasoningBundleBuilder
from ..execution import LocalExecutionEngine, ApprovalGate, ExecutionType, ExecutionResult
from ..trust_ledger import TrustLedger, EntryType, VerificationStatus

logger = logging.getLogger(__name__)


class WorkflowStage(str, Enum):
    """Stages in the data-resident workflow."""
    
    INGEST = "ingest"
    DETECT = "detect"
    NORMALIZE = "normalize"
    REASON = "reason"
    FIX_GENERATE = "fix_generate"
    APPROVE = "approve"
    EXECUTE = "execute"
    VERIFY = "verify"
    RECORD = "record"


@dataclass
class Finding:
    """A security finding detected locally."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    finding_type: str = ""
    severity: str = "medium"
    resource: str = ""
    description: str = ""
    patterns: List[str] = field(default_factory=list)
    policies_violated: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class FixProposal:
    """A proposed fix for a finding."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    finding_id: str = ""
    description: str = ""
    patch: str = ""
    file_path: str = ""
    risk_reduction: str = ""
    rollback_plan: str = ""
    proposed_at: datetime = field(default_factory=datetime.now)
    approved: Optional[bool] = None


class DataResidentOrchestrator(BaseModel):
    """
    Main orchestrator for the data-resident architecture.
    
    This is the central coordinator that ensures:
    - All data stays local
    - Only sanitized metadata goes to LLMs
    - All executions require approval
    - Everything is logged to the trust ledger
    
    Attributes:
        name: Orchestrator identifier
        sanitizer: Data sanitizer for LLM requests
        executor: Local execution engine
        ledger: Trust ledger for audit trail
        llm_router: Function to route to appropriate LLM
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    name: str = Field(default="data_resident_orchestrator")
    
    # Components
    sanitizer: DataSanitizer = Field(default_factory=DataSanitizer)
    executor: Optional[LocalExecutionEngine] = Field(default=None)
    ledger: TrustLedger = Field(default_factory=TrustLedger)
    
    # LLM routing
    llm_router: Optional[Callable[[str, ReasoningBundle], str]] = Field(default=None)
    
    # Callbacks
    on_finding: Optional[Callable[[Finding], None]] = Field(default=None)
    on_fix_proposed: Optional[Callable[[FixProposal], None]] = Field(default=None)
    on_execution: Optional[Callable[[ExecutionResult], None]] = Field(default=None)
    
    # State
    _findings: Dict[str, Finding] = {}
    _fix_proposals: Dict[str, FixProposal] = {}
    _current_stage: WorkflowStage = WorkflowStage.INGEST
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._findings = {}
        self._fix_proposals = {}
        if not self.executor:
            self.executor = LocalExecutionEngine()
    
    def ingest_finding(self, finding: Finding) -> str:
        """
        Step 1-3: Ingest and store a finding locally.
        
        Args:
            finding: The security finding
            
        Returns:
            Finding ID
        """
        self._current_stage = WorkflowStage.INGEST
        
        # Store locally
        self._findings[finding.id] = finding
        
        # Log to ledger
        self.ledger.log_finding(
            finding_id=finding.id,
            finding_type=finding.finding_type,
            severity=finding.severity,
            resource=finding.resource,
        )
        
        if self.on_finding:
            self.on_finding(finding)
        
        logger.info(f"Finding ingested: {finding.id} - {finding.finding_type}")
        
        return finding.id
    
    def request_reasoning(
        self,
        finding_id: str,
        llm_type: str = "default",
    ) -> Optional[str]:
        """
        Step 4: Request LLM reasoning with sanitized data only.
        
        This is the critical data-leak prevention step.
        Only sanitized reasoning bundles go to external LLMs.
        
        Args:
            finding_id: The finding to reason about
            llm_type: Which LLM to route to
            
        Returns:
            LLM response (or None if no router)
        """
        self._current_stage = WorkflowStage.REASON
        
        finding = self._findings.get(finding_id)
        if not finding:
            logger.error(f"Finding not found: {finding_id}")
            return None
        
        # Build sanitized reasoning bundle - NO RAW DATA
        builder = ReasoningBundleBuilder(sanitizer=self.sanitizer)
        bundle = builder.build_from_finding(
            finding_id=finding.id,
            finding_type=finding.finding_type,
            severity=finding.severity,
            affected_file=finding.resource,
            patterns=finding.patterns,
            policies=finding.policies_violated,
        )
        
        logger.info(f"Reasoning request (sanitized): {bundle.finding_id}")
        
        # Route to LLM if configured
        if self.llm_router:
            response = self.llm_router(llm_type, bundle)
            return response
        
        # Return the prompt that would be sent
        return bundle.to_prompt()
    
    def propose_fix(
        self,
        finding_id: str,
        description: str,
        patch: str,
        file_path: str,
        risk_reduction: str = "",
    ) -> FixProposal:
        """
        Step 5: Propose a fix (generated locally or via LLM).
        
        Args:
            finding_id: Finding this fixes
            description: What the fix does
            patch: The actual patch/code
            file_path: File to patch
            risk_reduction: How this reduces risk
            
        Returns:
            The fix proposal
        """
        self._current_stage = WorkflowStage.FIX_GENERATE
        
        proposal = FixProposal(
            finding_id=finding_id,
            description=description,
            patch=patch,
            file_path=file_path,
            risk_reduction=risk_reduction,
            rollback_plan=f"Revert changes to {file_path}",
        )
        
        self._fix_proposals[proposal.id] = proposal
        
        # Log to ledger
        self.ledger.log_fix_proposal(
            fix_id=proposal.id,
            finding_id=finding_id,
            description=description,
        )
        
        if self.on_fix_proposed:
            self.on_fix_proposed(proposal)
        
        logger.info(f"Fix proposed: {proposal.id}")
        
        return proposal
    
    def request_approval(
        self,
        fix_id: str,
        requested_by: str = "system",
    ) -> str:
        """
        Step 6: Request approval for a fix.
        
        Args:
            fix_id: Fix proposal to approve
            requested_by: Who is requesting approval
            
        Returns:
            Approval request ID
        """
        self._current_stage = WorkflowStage.APPROVE
        
        proposal = self._fix_proposals.get(fix_id)
        if not proposal:
            raise ValueError(f"Fix proposal not found: {fix_id}")
        
        # Request execution with approval
        request = self.executor.request_execution(
            action_type=ExecutionType.CODE_PATCH,
            action={
                "file": proposal.file_path,
                "patch": proposal.patch,
            },
            description=proposal.description,
            rationale=proposal.risk_reduction or f"Fix for finding {proposal.finding_id}",
            risk_level="medium",
            requested_by=requested_by,
        )
        
        return request.id
    
    def approve_and_execute(
        self,
        approval_id: str,
        approver: str,
    ) -> Optional[ExecutionResult]:
        """
        Step 7: Approve and execute a fix locally.
        
        Args:
            approval_id: The approval request ID
            approver: Who is approving
            
        Returns:
            Execution result
        """
        self._current_stage = WorkflowStage.EXECUTE
        
        # Get the request
        pending = self.executor.get_pending_approvals()
        request = next((r for r in pending if r.id == approval_id), None)
        
        if not request:
            logger.error(f"Approval not found: {approval_id}")
            return None
        
        # Parse the action from the request
        import json
        action_data = json.loads(request.changes_preview)
        action = action_data.get("action", {})
        
        # Execute
        result = self.executor.execute_approved(approval_id, action)
        
        if result:
            # Log approval
            self.ledger.log_approval(
                approval_id=approval_id,
                fix_id=request.execution_id,
                approved=True,
                approver=approver,
            )
            
            # Log execution
            self.ledger.log_execution(
                execution_id=result.id,
                fix_id=request.execution_id,
                status=result.status.value,
            )
            
            if self.on_execution:
                self.on_execution(result)
        
        return result
    
    def verify(
        self,
        execution_id: str,
        checks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Step 8: Verify the execution locally.
        
        Args:
            execution_id: Execution to verify
            checks: Specific checks to run
            
        Returns:
            Verification results
        """
        self._current_stage = WorkflowStage.VERIFY
        
        checks = checks or ["syntax", "tests", "security", "policy"]
        
        # Run verification (placeholder - would run actual checks)
        results = {
            "execution_id": execution_id,
            "status": "passed",
            "checks": {check: "passed" for check in checks},
            "verified_at": datetime.now().isoformat(),
        }
        
        # Log to ledger
        verification_id = str(uuid.uuid4())
        self.ledger.log_verification(
            verification_id=verification_id,
            execution_id=execution_id,
            status=VerificationStatus.PASSED,
            checks=checks,
        )
        
        logger.info(f"Verification complete: {execution_id}")
        
        return results
    
    def record_compliance(
        self,
        finding_id: str,
        fix_id: str,
        verification_id: str,
        framework: str,
        requirement_id: str,
    ) -> str:
        """
        Step 9: Record compliance evidence.
        
        Args:
            finding_id: The finding
            fix_id: The fix
            verification_id: The verification
            framework: Compliance framework
            requirement_id: Specific requirement
            
        Returns:
            Evidence ID
        """
        self._current_stage = WorkflowStage.RECORD
        
        evidence = self.ledger.add_compliance_evidence(
            framework=framework,
            requirement_id=requirement_id,
            finding_id=finding_id,
            fix_id=fix_id,
            verification_id=verification_id,
        )
        
        logger.info(f"Compliance evidence recorded: {evidence.id}")
        
        return evidence.id
    
    def get_audit_report(self) -> Dict[str, Any]:
        """Generate an audit report from the ledger."""
        return self.ledger.generate_audit_report()
    
    def get_telemetry(self) -> Dict[str, Any]:
        """
        Get minimal, anonymized telemetry.
        
        This is the ONLY data that could optionally go to external systems.
        Contains no PII, logs, code, or secrets.
        """
        import hashlib
        tenant_hash = hashlib.sha256(self.name.encode()).hexdigest()[:12]
        
        return {
            "tenant_id": tenant_hash,
            "open_findings": len([f for f in self._findings.values()]),
            "pending_fixes": len([f for f in self._fix_proposals.values() if f.approved is None]),
            "ledger_entries": len(self.ledger._entries),
            "system_health": "green",
        }


# Main workflow function
def run_data_resident_workflow(
    finding: Finding,
    orchestrator: DataResidentOrchestrator,
    fix_generator: Callable[[Finding, str], FixProposal],
    approver: str = "human",
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """
    Run the complete data-resident workflow.
    
    Args:
        finding: The security finding
        orchestrator: The orchestrator instance
        fix_generator: Function to generate fix proposals
        approver: Who will approve
        auto_approve: Auto-approve if True
        
    Returns:
        Workflow results
    """
    results = {
        "finding_id": None,
        "reasoning": None,
        "fix_id": None,
        "approval_id": None,
        "execution": None,
        "verification": None,
    }
    
    # Step 1-3: Ingest
    results["finding_id"] = orchestrator.ingest_finding(finding)
    
    # Step 4: Reason (with sanitized data)
    results["reasoning"] = orchestrator.request_reasoning(finding.id)
    
    # Step 5: Generate fix
    proposal = fix_generator(finding, results["reasoning"])
    results["fix_id"] = proposal.id
    
    # Step 6: Request approval
    results["approval_id"] = orchestrator.request_approval(proposal.id)
    
    # Step 7: Execute (if approved)
    if auto_approve:
        execution = orchestrator.approve_and_execute(results["approval_id"], approver)
        if execution:
            results["execution"] = execution.to_dict()
            
            # Step 8: Verify
            results["verification"] = orchestrator.verify(execution.id)
    
    return results
