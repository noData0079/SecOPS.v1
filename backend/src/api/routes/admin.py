from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.core.security.kill_switch import kill_switch
from src.api.deps import require_admin, db_session
from src.db.models import User
from src.db.schemas.admin import AuditEvent
from src.db.schemas.billing import BillingRecord

router = APIRouter()

class KillSwitchState(BaseModel):
    active: bool

@router.get("/kill-switch", response_model=KillSwitchState, dependencies=[Depends(require_admin)])
def get_kill_switch_status():
    """Get current status of the global kill switch."""
    return {"active": kill_switch.is_active()}

@router.post("/kill-switch", response_model=KillSwitchState, dependencies=[Depends(require_admin)])
def toggle_kill_switch(state: KillSwitchState):
    """Enable or disable the global kill switch."""
    if state.active:
        kill_switch.activate()
    else:
        kill_switch.deactivate()
    return {"active": kill_switch.is_active()}


@router.get("/overview", dependencies=[Depends(require_admin)])
def get_admin_overview(db: Session = Depends(db_session)):
    """
    Get platform health, active users, and system load.
    """
    user_count = db.execute(select(func.count(User.id))).scalar() or 0
    # agents_count = db.execute(select(func.count(Agent.id))).scalar() or 0 # Agent model not imported yet

    return {
        "platform_health": "stable",
        "active_users": user_count,
        "system_load": 0.45,
        "active_agents": 3 # Placeholder until Agent model is available
    }


@router.get("/users", dependencies=[Depends(require_admin)])
def get_admin_users(db: Session = Depends(db_session)):
    """
    List all users.
    """
    users = db.execute(select(User)).scalars().all()
    return {
        "users": [
            {"id": u.id, "email": u.email, "role": "user", "status": "active" if u.is_active else "inactive"}
            for u in users
        ]
    }


@router.get("/projects", dependencies=[Depends(require_admin)])
def get_admin_projects():
    """
    List all projects/tenants.
    """
    return {
        "projects": [
            {"id": "proj_A", "name": "Alpha Ops", "risk_level": "low"},
            {"id": "proj_B", "name": "Beta Dev", "risk_level": "medium"},
        ]
    }


@router.get("/audit", dependencies=[Depends(require_admin)])
def get_admin_audit_logs(db: Session = Depends(db_session)):
    """
    Fetch immutable audit logs.
    """
    logs = db.execute(select(AuditEvent).limit(50)).scalars().all()
    return {
        "logs": [
            {"id": l.id, "event": l.event_type, "actor": l.actor_id, "outcome": l.outcome, "timestamp": l.created_at}
            for l in logs
        ]
    }


@router.get("/policies", dependencies=[Depends(require_admin)])
def get_admin_policies():
    """
    Manage policy rules and permissions.
    """
    return {
        "policies": [
            {"id": "pol_1", "name": "No Delete Prod", "mode": "enforce"},
            {"id": "pol_2", "name": "Require Approval > $50", "mode": "audit"},
        ]
    }


@router.get("/billing", dependencies=[Depends(require_admin)])
def get_admin_billing(db: Session = Depends(db_session)):
    """
    Billing overview and cost breakdown.
    """
    total_cost = db.execute(select(func.sum(BillingRecord.total_cost))).scalar() or 0.0

    return {
        "current_period_cost": total_cost,
        "currency": "USD",
        "breakdown": [
            {"item": "LLM Tokens", "cost": total_cost * 0.8},
            {"item": "Storage", "cost": total_cost * 0.2},
        ]
    }
