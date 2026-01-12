import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel

# We import the classes directly. In a real app we might use dependency injection.
from core.autonomy.gatekeeper import ApprovalQueueDB

logger = logging.getLogger(__name__)

router = APIRouter()

class ApprovalDecision(BaseModel):
    decision: str  # 'APPROVE' or 'DENY'
    notes: Optional[str] = None

@router.post("/approval/{action_id}/decide")
async def decision(action_id: str, payload: ApprovalDecision):
    db = ApprovalQueueDB() # Initialize with default path

    request = db.get_request(action_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if payload.decision == "APPROVE":
        # Update status to APPROVED. The AutonomyLoop (polling) will pick this up.
        db.update_status(action_id, "APPROVED", payload.notes)
        return {"status": "resumed"}

    elif payload.decision == "DENY":
        # Update status to DENIED. The AutonomyLoop will pick this up and treat as failure/block.
        db.update_status(action_id, "DENIED", payload.notes)
        return {"status": "blocked"}

    else:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be APPROVE or DENY.")
