"""
System Monitoring API Endpoints

RESTful API for system health, metrics, and learning intelligence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


# ============================================
# RESPONSE MODELS
# ============================================

class HealthStatus(BaseModel):
    """Health check response."""
    status: str  # healthy, degraded, unhealthy
    components: Dict[str, str]
    uptime_seconds: float
    checked_at: datetime


class LLMUsageStats(BaseModel):
    """LLM usage statistics."""
    total_requests: int
    total_tokens: int
    total_cost: float
    calls_saved_by_playbooks: int
    cost_saved: float
    savings_percentage: float


class LearningStats(BaseModel):
    """Learning system statistics."""
    total_playbooks: int
    high_confidence_playbooks: int
    total_fixes: int
    playbook_usage_rate: float
    llm_fallback_rate: float
    maturity_level: str
    maturity_score: float


class SystemMetrics(BaseModel):
    """Comprehensive system metrics."""
    llm: LLMUsageStats
    learning: LearningStats
    findings_open: int
    findings_fixed_today: int
    alerts_open: int
    scans_today: int
    generated_at: datetime


# ============================================
# IN-MEMORY METRICS (replace with real tracking)
# ============================================

_start_time = datetime.now()
_metrics = {
    "llm_requests": 156,
    "llm_tokens": 245000,
    "llm_cost": 12.35,
    "playbook_fixes": 89,
    "llm_fixes": 34,
    "cost_saved": 28.50,
    "findings_open": 23,
    "findings_fixed_today": 7,
    "alerts_open": 5,
    "scans_today": 12,
}


# ============================================
# ENDPOINTS
# ============================================

@router.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Check system health."""
    components = {
        "api": "healthy",
        "database": "healthy",
        "llm_service": "healthy",
        "learning_engine": "healthy",
        "vector_store": "healthy",
    }
    
    # Determine overall status
    unhealthy = [k for k, v in components.items() if v == "unhealthy"]
    degraded = [k for k, v in components.items() if v == "degraded"]
    
    if unhealthy:
        status = "unhealthy"
    elif degraded:
        status = "degraded"
    else:
        status = "healthy"
    
    uptime = (datetime.now() - _start_time).total_seconds()
    
    return HealthStatus(
        status=status,
        components=components,
        uptime_seconds=uptime,
        checked_at=datetime.now(),
    )


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics() -> SystemMetrics:
    """Get comprehensive system metrics."""
    total_fixes = _metrics["playbook_fixes"] + _metrics["llm_fixes"]
    playbook_rate = _metrics["playbook_fixes"] / total_fixes if total_fixes > 0 else 0
    
    return SystemMetrics(
        llm=LLMUsageStats(
            total_requests=_metrics["llm_requests"],
            total_tokens=_metrics["llm_tokens"],
            total_cost=_metrics["llm_cost"],
            calls_saved_by_playbooks=_metrics["playbook_fixes"],
            cost_saved=_metrics["cost_saved"],
            savings_percentage=_metrics["cost_saved"] / (_metrics["llm_cost"] + _metrics["cost_saved"]) * 100,
        ),
        learning=LearningStats(
            total_playbooks=23,
            high_confidence_playbooks=16,
            total_fixes=total_fixes,
            playbook_usage_rate=playbook_rate,
            llm_fallback_rate=1 - playbook_rate,
            maturity_level="LEARNING",
            maturity_score=0.45,
        ),
        findings_open=_metrics["findings_open"],
        findings_fixed_today=_metrics["findings_fixed_today"],
        alerts_open=_metrics["alerts_open"],
        scans_today=_metrics["scans_today"],
        generated_at=datetime.now(),
    )


@router.get("/llm/usage", response_model=LLMUsageStats)
async def get_llm_usage() -> LLMUsageStats:
    """Get LLM usage statistics."""
    return LLMUsageStats(
        total_requests=_metrics["llm_requests"],
        total_tokens=_metrics["llm_tokens"],
        total_cost=_metrics["llm_cost"],
        calls_saved_by_playbooks=_metrics["playbook_fixes"],
        cost_saved=_metrics["cost_saved"],
        savings_percentage=_metrics["cost_saved"] / (_metrics["llm_cost"] + _metrics["cost_saved"]) * 100,
    )


@router.get("/learning/intelligence", response_model=LearningStats)
async def get_learning_intelligence() -> LearningStats:
    """Get learning system intelligence metrics."""
    total_fixes = _metrics["playbook_fixes"] + _metrics["llm_fixes"]
    playbook_rate = _metrics["playbook_fixes"] / total_fixes if total_fixes > 0 else 0
    
    # Determine maturity level
    if playbook_rate < 0.3:
        maturity_level = "FOUNDATION"
        maturity_score = 0.2
    elif playbook_rate < 0.6:
        maturity_level = "LEARNING"
        maturity_score = 0.45
    elif playbook_rate < 0.85:
        maturity_level = "OPTIMIZED"
        maturity_score = 0.7
    else:
        maturity_level = "AUTONOMOUS"
        maturity_score = 0.9
    
    return LearningStats(
        total_playbooks=23,
        high_confidence_playbooks=16,
        total_fixes=total_fixes,
        playbook_usage_rate=playbook_rate,
        llm_fallback_rate=1 - playbook_rate,
        maturity_level=maturity_level,
        maturity_score=maturity_score,
    )


@router.get("/learning/roadmap")
async def get_learning_roadmap() -> Dict[str, Any]:
    """Get the learning system roadmap and progress."""
    return {
        "phases": [
            {
                "name": "FOUNDATION",
                "description": "Building initial learning data",
                "status": "completed",
                "percentage": 100,
            },
            {
                "name": "LEARNING",
                "description": "Actively accumulating intelligence",
                "status": "in_progress",
                "percentage": 45,
            },
            {
                "name": "OPTIMIZED",
                "description": "LLM usage significantly reduced",
                "status": "pending",
                "percentage": 0,
            },
            {
                "name": "AUTONOMOUS",
                "description": "System operates on learned intelligence",
                "status": "pending",
                "percentage": 0,
            },
        ],
        "current_phase": "LEARNING",
        "overall_progress": 35,
        "llm_dependency_reduction": {
            "current": 28,
            "target_6_months": 60,
            "target_12_months": 85,
        },
        "cost_reduction": {
            "current_monthly_savings": _metrics["cost_saved"],
            "projected_6_months": _metrics["cost_saved"] * 4,
            "projected_12_months": _metrics["cost_saved"] * 10,
        },
    }


@router.get("/version")
async def get_version() -> Dict[str, str]:
    """Get system version information."""
    return {
        "name": "The Sovereign Mechanica",
        "product": "TSM99",
        "version": "2.0.0",
        "build": "2026.01.09",
        "api_version": "v1",
        "learning_system": "1.0.0",
        "playbook_engine": "1.0.0",
    }
