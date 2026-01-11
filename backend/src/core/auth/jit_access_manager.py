"""
JIT Access Manager - Identity-Aware Autonomy

Manages the IAM lifecycle, granting "Just-In-Time" permissions and revoking them automatically.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class AccessGrant:
    grant_id: str
    user_id: str
    resource: str
    role: str
    expires_at: float
    reason: str

class JITAccessManager:
    """
    Autonomously grants and revokes permissions.
    """

    def __init__(self):
        self.active_grants: Dict[str, AccessGrant] = {}

    def request_access(self, user_id: str, resource: str, role: str, duration_minutes: int, reason: str) -> Optional[str]:
        """
        Grants JIT access if policy allows.
        """
        logger.info(f"Access Request: {user_id} -> {resource} ({role}) for {duration_minutes}m. Reason: {reason}")

        # Policy Check (Simulated)
        if not self._check_policy(user_id, resource, role):
            logger.warning("Access Denied by Policy.")
            return None

        grant_id = str(uuid.uuid4())
        expires_at = time.time() + (duration_minutes * 60)

        grant = AccessGrant(
            grant_id=grant_id,
            user_id=user_id,
            resource=resource,
            role=role,
            expires_at=expires_at,
            reason=reason
        )

        self.active_grants[grant_id] = grant
        self._apply_permission(grant)

        logger.info(f"Access Granted: {grant_id}")
        return grant_id

    def revoke_access(self, grant_id: str):
        """
        Revokes a specific grant.
        """
        if grant_id in self.active_grants:
            grant = self.active_grants.pop(grant_id)
            self._remove_permission(grant)
            logger.info(f"Access Revoked: {grant_id}")

    def run_cleanup_cycle(self):
        """
        Checks for expired grants and revokes them.
        Should be run periodically.
        """
        now = time.time()
        expired_ids = [gid for gid, g in self.active_grants.items() if g.expires_at <= now]

        for gid in expired_ids:
            logger.info(f"Grant {gid} expired. Revoking...")
            self.revoke_access(gid)

    def _check_policy(self, user_id: str, resource: str, role: str) -> bool:
        """
        Evaluates if the user is allowed to request this access.
        """
        # Default allow for demo
        return True

    def _apply_permission(self, grant: AccessGrant):
        """
        Applies the permission to the underlying system (e.g., AWS IAM, K8s RBAC).
        """
        # Simulation
        logger.info(f"[Mock] Applied permission {grant.role} on {grant.resource} to {grant.user_id}")

    def _remove_permission(self, grant: AccessGrant):
        """
        Removes the permission.
        """
        # Simulation
        logger.info(f"[Mock] Removed permission {grant.role} on {grant.resource} from {grant.user_id}")

# Global instance
jit_access_manager = JITAccessManager()
