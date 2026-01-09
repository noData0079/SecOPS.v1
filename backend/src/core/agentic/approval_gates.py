# backend/src/core/agentic/approval_gates.py

"""
Approval & Policy Gate - Layer 7

Human + policy control:
- Auto-approve low risk
- Require approval for sensitive paths
- Enforce org rules

Enables machine-speed execution with human control.
"""

from __future__ import annotations

import logging
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
import uuid

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class RiskLevel(str, Enum):
    """Risk levels for actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalPolicy:
    """Policy for approval requirements."""
    
    auto_approve_low_risk: bool = True
    auto_approve_medium_risk: bool = False
    require_approval_high_risk: bool = True
    require_approval_critical: bool = True
    approval_timeout_seconds: int = 3600  # 1 hour
    
    # Sensitive paths that always require approval
    sensitive_paths: List[str] = field(default_factory=lambda: [
        "production",
        "main",
        "master",
        "/etc/",
        "secrets",
        ".env",
    ])
    
    # Auto-approve actions from trusted sources
    trusted_sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "auto_approve_low_risk": self.auto_approve_low_risk,
            "auto_approve_medium_risk": self.auto_approve_medium_risk,
            "require_approval_high_risk": self.require_approval_high_risk,
            "require_approval_critical": self.require_approval_critical,
            "approval_timeout_seconds": self.approval_timeout_seconds,
            "sensitive_paths": self.sensitive_paths,
            "trusted_sources": self.trusted_sources,
        }


@dataclass
class ApprovalRequest:
    """A request for approval."""
    
    id: str
    agent_id: str
    action_data: Dict[str, Any]
    context: Dict[str, Any]
    risk_level: RiskLevel
    status: ApprovalStatus
    created_at: datetime
    expires_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "action": self.action_data,
            "context": self.context,
            "risk_level": self.risk_level.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason,
        }


class ApprovalGate:
    """
    Manages human approval for actions.
    
    Key principle: Machine speed with human control.
    """
    
    def __init__(self, policy: Optional[ApprovalPolicy] = None):
        """Initialize approval gate."""
        self.policy = policy or ApprovalPolicy()
        self._requests: Dict[str, ApprovalRequest] = {}
        self._notification_handlers: List[Callable] = []
        logger.info("ApprovalGate initialized")
    
    def set_policy(self, policy: ApprovalPolicy) -> None:
        """Update approval policy."""
        self.policy = policy
        logger.info("Approval policy updated")
    
    def register_notification_handler(self, handler: Callable) -> None:
        """Register a handler for approval notifications."""
        self._notification_handlers.append(handler)
    
    def _is_sensitive_path(self, action_data: Dict[str, Any]) -> bool:
        """Check if action involves sensitive paths."""
        # Check various fields that might contain paths
        fields_to_check = [
            action_data.get("file_path", ""),
            action_data.get("target", ""),
            action_data.get("environment", ""),
            str(action_data.get("parameters", {})),
        ]
        
        combined = " ".join(fields_to_check).lower()
        
        for sensitive in self.policy.sensitive_paths:
            if sensitive.lower() in combined:
                return True
        
        return False
    
    def _get_risk_level(self, action: Any) -> RiskLevel:
        """Determine risk level from action."""
        risk_str = getattr(action, 'risk_level', 'medium')
        if isinstance(risk_str, str):
            risk_str = risk_str.lower()
            if risk_str == "critical":
                return RiskLevel.CRITICAL
            elif risk_str == "high":
                return RiskLevel.HIGH
            elif risk_str == "low":
                return RiskLevel.LOW
        return RiskLevel.MEDIUM
    
    async def check_approval(
        self,
        agent_id: str,
        action: Any,
        context: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """
        Check if action needs approval or can proceed.
        
        Returns:
            Tuple of (approved, approval_request_id)
            - (True, None) if auto-approved
            - (False, request_id) if pending approval
        """
        risk_level = self._get_risk_level(action)
        action_data = action.to_dict() if hasattr(action, 'to_dict') else {"action": str(action)}
        
        # Check for sensitive paths
        is_sensitive = self._is_sensitive_path(action_data)
        if is_sensitive:
            logger.info("Action involves sensitive path, requiring approval")
            request = await self._create_request(agent_id, action_data, context, RiskLevel.HIGH)
            return (False, request.id)
        
        # Check risk-based auto-approval
        if risk_level == RiskLevel.LOW and self.policy.auto_approve_low_risk:
            logger.info("Action auto-approved (low risk)")
            return (True, None)
        
        if risk_level == RiskLevel.MEDIUM and self.policy.auto_approve_medium_risk:
            logger.info("Action auto-approved (medium risk, policy allows)")
            return (True, None)
        
        # Check trusted sources
        source = context.get("source", "")
        if source in self.policy.trusted_sources:
            logger.info(f"Action auto-approved (trusted source: {source})")
            return (True, None)
        
        # Requires explicit approval
        request = await self._create_request(agent_id, action_data, context, risk_level)
        return (False, request.id)
    
    async def _create_request(
        self,
        agent_id: str,
        action_data: Dict[str, Any],
        context: Dict[str, Any],
        risk_level: RiskLevel,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        now = datetime.utcnow()
        expires = now + timedelta(seconds=self.policy.approval_timeout_seconds)
        
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            action_data=action_data,
            context=context,
            risk_level=risk_level,
            status=ApprovalStatus.PENDING,
            created_at=now,
            expires_at=expires,
        )
        
        self._requests[request.id] = request
        
        logger.info(
            f"Approval request created: {request.id} "
            f"(risk: {risk_level.value})"
        )
        
        # Notify handlers
        for handler in self._notification_handlers:
            try:
                await handler(request)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
        
        return request
    
    async def approve(
        self,
        approval_id: str,
        approver: str = "system",
    ) -> bool:
        """Approve a pending request."""
        if approval_id not in self._requests:
            logger.warning(f"Approval not found: {approval_id}")
            return False
        
        request = self._requests[approval_id]
        
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"Approval not pending: {approval_id}")
            return False
        
        # Check expiration
        if datetime.utcnow() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_at = datetime.utcnow()
        request.approved_by = approver
        
        logger.info(f"Approval granted: {approval_id} by {approver}")
        return True
    
    async def reject(
        self,
        approval_id: str,
        reason: str = "",
        rejector: str = "system",
    ) -> bool:
        """Reject a pending request."""
        if approval_id not in self._requests:
            logger.warning(f"Approval not found: {approval_id}")
            return False
        
        request = self._requests[approval_id]
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejected_at = datetime.utcnow()
        request.rejected_by = rejector
        request.rejection_reason = reason
        
        logger.info(f"Approval rejected: {approval_id} - {reason}")
        return True
    
    async def check_status(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get status of an approval request."""
        request = self._requests.get(approval_id)
        
        if request and request.status == ApprovalStatus.PENDING:
            # Check for expiration
            if datetime.utcnow() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
        
        return request
    
    async def is_approved(self, approval_id: str) -> bool:
        """Check if a request is approved."""
        request = await self.check_status(approval_id)
        return request is not None and request.status == ApprovalStatus.APPROVED
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        pending = []
        for request in self._requests.values():
            if request.status == ApprovalStatus.PENDING:
                # Check expiration
                if datetime.utcnow() > request.expires_at:
                    request.status = ApprovalStatus.EXPIRED
                else:
                    pending.append(request)
        return pending
    
    def get_approval_history(self, limit: int = 100) -> List[ApprovalRequest]:
        """Get approval history."""
        return list(self._requests.values())[-limit:]
