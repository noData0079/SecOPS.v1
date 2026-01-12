import uuid
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from core.safety.risk_matrix import RiskMatrix, RiskLevel

logger = logging.getLogger(__name__)

class ApprovalQueueDB:
    """
    File-based persistence for approval requests.
    Stores requests in backend/data/approvals_queue/
    """
    def __init__(self, storage_path: str = "backend/data/approvals_queue"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, action_id: str) -> Path:
        return self.storage_path / f"{action_id}.json"

    def create_request(self, request: Dict[str, Any]):
        action_id = request['action_id']
        file_path = self._get_file_path(action_id)
        with open(file_path, 'w') as f:
            json.dump(request, f, indent=2)
        logger.info(f"Created approval request: {action_id}")

    def get_request(self, action_id: str) -> Optional[Dict[str, Any]]:
        file_path = self._get_file_path(action_id)
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading request {action_id}: {e}")
            return None

    def update_status(self, action_id: str, status: str, feedback: Optional[str] = None):
        request = self.get_request(action_id)
        if request:
            request['status'] = status
            if feedback:
                request['feedback'] = feedback
            self.create_request(request) # Overwrite
            logger.info(f"Updated request {action_id} to {status}")


class Gatekeeper:
    def __init__(self, risk_matrix: RiskMatrix, approval_queue_db: ApprovalQueueDB):
        self.risk_matrix = risk_matrix
        self.db = approval_queue_db

    def execute_or_wait(self, agent_id: str, tool_name: str, params: dict):
        # 1. Assess Risk
        risk_level = self.risk_matrix.evaluate(tool_name, params)

        # 2. IF SAFE: Execute immediately
        if risk_level == RiskLevel.SAFE:
            return {"status": "EXECUTING", "requires_approval": False}

        # 3. IF DANGEROUS: Suspend and Queue
        action_id = str(uuid.uuid4())

        approval_request = {
            "action_id": action_id,
            "agent_id": agent_id,
            "tool": tool_name,
            "params": params,
            "risk": risk_level.name,
            "reasoning": "AI detected high confidence threat but requires auth.",
            "status": "PENDING_APPROVAL",
            "timestamp": time.time()
        }

        # Save to DB for the Frontend to see
        self.db.create_request(approval_request)

        # Return PAUSED status. The caller (AutonomyLoop) should handle the waiting/polling.
        return {
            "status": "PAUSED",
            "requires_approval": True,
            "action_id": action_id,
            "message": f"Action paused. Waiting for human approval (Risk: {risk_level.name})"
        }
