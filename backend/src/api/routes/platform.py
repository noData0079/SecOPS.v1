import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from src.api.deps import get_current_user
from src.core.training.feedback_loop import get_feedback_collector
from pydantic import BaseModel

try:  # Optional runtime dependencies
    from src.extensions.k8s_healer.healer import k8s_healer
except Exception:  # noqa: BLE001
    k8s_healer = None

try:
    from src.extensions.db_repair import db_repair_agent
except Exception:  # noqa: BLE001
    db_repair_agent = None

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/platform",
    tags=["Platform"],
)


class FeedbackRequest(BaseModel):
    incident_id: str
    rating: int  # 1 (Thumbs Up) or -1 (Thumbs Down)
    comment: str | None = None


@router.post("/feedback", summary="Submit human feedback for model training")
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: Any = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Ingests user feedback ("Thumbs Up/Down") for Recursive Self-Improvement.
    These signals are used to fine-tune the model.
    """
    collector = get_feedback_collector()
    success = collector.collect_feedback(
        incident_id=feedback.incident_id,
        rating=feedback.rating,
        comment=feedback.comment
    )

    return {
        "status": "recorded" if success else "failed",
        "incident_id": feedback.incident_id
    }


@router.get("/status", summary="Lightweight platform status")
async def platform_status(current_user: Any = Depends(get_current_user)) -> Dict[str, Any]:
    """Minimal platform status endpoint used by tests."""

    org_id = getattr(current_user, "org_id", None)
    if org_id is None and isinstance(current_user, dict):
        org_id = current_user.get("org_id")

    return {
        "status": "ok",
        "org_id": org_id or "unknown-org",
        "environment": "test",
    }


@router.post("/k8s/heal", summary="Analyze and optionally heal k8s workloads")
async def k8s_heal(
    apply: bool = Query(
        False, description="Apply patches (true) or perform a dry-run (false)"
    ),
    current_user: Any = Depends(get_current_user),
) -> Dict[str, Any]:
    if not k8s_healer:
        return {"patched": False, "reason": "k8s healer unavailable"}

    _ = current_user
    result = await k8s_healer.heal(apply=apply)
    return result


@router.post("/database/repair", summary="Run DB auto-repair checks")
async def repair_db(autofix: bool = False, current_user: Any = Depends(get_current_user)) -> Dict[str, Any]:
    if not db_repair_agent:
        return {"patched": False, "reason": "db repair unavailable"}

    result = await db_repair_agent.run_full_check()
    if autofix:
        await db_repair_agent.apply_patches(result["patches"])

    return result
