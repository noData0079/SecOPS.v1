from fastapi import APIRouter, Header, HTTPException, status, Depends
from pydantic import BaseModel
import os
from src.core.security.kill_switch import kill_switch
from src.core.training.orchestrator import get_orchestrator

router = APIRouter()

# Simple dependency to check admin key
def verify_admin(authorization: str = Header(None)):
    admin_key = os.getenv("ADMIN_KEY", "admin123")
    if not authorization:
        raise HTTPException(status_code=403, detail="Missing Authorization Header")
    
    token = authorization.replace("Bearer ", "")
    if token != admin_key:
        raise HTTPException(status_code=403, detail="Invalid Admin Key")
    return True

class KillSwitchState(BaseModel):
    active: bool

@router.get("/kill-switch", response_model=KillSwitchState, dependencies=[Depends(verify_admin)])
def get_kill_switch_status():
    """Get current status of the global kill switch."""
    return {"active": kill_switch.is_active()}

@router.post("/kill-switch", response_model=KillSwitchState, dependencies=[Depends(verify_admin)])
def toggle_kill_switch(state: KillSwitchState):
    """Enable or disable the global kill switch."""
    if state.active:
        kill_switch.activate()
    else:
        kill_switch.deactivate()
    return {"active": kill_switch.is_active()}

@router.post("/training/start")
async def start_training(
    dependencies=[Depends(verify_admin)]
):
    """
    Start recursive training run.
    """
    orchestrator = get_orchestrator()
    if orchestrator.is_training:
        raise HTTPException(status_code=409, detail="Training already in progress")

    # Run in background (in real app, use BackgroundTasks)
    import asyncio
    asyncio.create_task(orchestrator.start_training_run())
    return {"status": "started", "message": "Training initiated in background"}

@router.post("/training/stop")
async def stop_training(
    dependencies=[Depends(verify_admin)]
):
    """
    Stop recursive training run.
    """
    orchestrator = get_orchestrator()
    orchestrator.stop_training_run()
    return {"status": "stopped", "message": "Training stop signal sent"}

@router.get("/training/status")
async def get_training_status(
    dependencies=[Depends(verify_admin)]
):
    """
    Get training status.
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_status()
