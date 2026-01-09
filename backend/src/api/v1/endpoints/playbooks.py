"""
Playbooks API Endpoints

RESTful API for managing security fix playbooks.
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ApprovalPolicy(str, Enum):
    AUTO_APPLY = "auto_apply"
    AUTO_WITH_LOG = "auto_with_log"
    HUMAN_REVIEW = "human_review"
    SENIOR_REVIEW = "senior_review"


class PlaybookCreate(BaseModel):
    """Create a new playbook."""
    finding_type: str = Field(..., description="e.g., SQL_INJECTION")
    language: Optional[str] = Field(default=None)
    framework: Optional[str] = Field(default=None)
    description: str = Field(default="")
    fix_template: str = Field(..., description="Fix code/pattern")
    confidence: float = Field(default=0.5, ge=0, le=1)
    approval_policy: ApprovalPolicy = Field(default=ApprovalPolicy.HUMAN_REVIEW)
    test_requirements: List[str] = Field(default_factory=list)


class PlaybookResponse(BaseModel):
    """Playbook response."""
    playbook_id: str
    finding_type: str
    language: Optional[str]
    framework: Optional[str]
    description: str
    fix_template: str
    confidence: float
    approval_policy: ApprovalPolicy
    test_requirements: List[str]
    usage_count: int
    success_rate: float
    created_at: datetime
    updated_at: datetime
    source: str


class PlaybookUpdate(BaseModel):
    """Update a playbook."""
    description: Optional[str] = None
    fix_template: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    approval_policy: Optional[ApprovalPolicy] = None


class PlaybooksList(BaseModel):
    """List of playbooks."""
    items: List[PlaybookResponse]
    total: int


class PlaybookMatch(BaseModel):
    """Matched playbook for a finding."""
    playbook_id: str
    finding_type: str
    confidence: float
    match_score: float
    requires_review: bool


# ============================================
# IN-MEMORY STORAGE
# ============================================

_playbooks: Dict[str, Dict[str, Any]] = {}


def _init_built_in_playbooks():
    """Initialize built-in playbooks."""
    if _playbooks:
        return
    
    playbooks = [
        {
            "playbook_id": "PB-SQLI-001",
            "finding_type": "SQL_INJECTION",
            "language": "nodejs",
            "framework": "express",
            "description": "SQL Injection fix using parameterized queries",
            "fix_template": "db.query('SELECT * FROM users WHERE id = ?', [userId])",
            "confidence": 0.94,
            "approval_policy": ApprovalPolicy.AUTO_APPLY,
            "test_requirements": ["sql_injection_test"],
            "usage_count": 47,
            "success_rate": 0.96,
            "source": "built-in",
        },
        {
            "playbook_id": "PB-XSS-001",
            "finding_type": "XSS",
            "language": "javascript",
            "framework": "react",
            "description": "XSS fix using DOMPurify sanitization",
            "fix_template": "const clean = DOMPurify.sanitize(userInput);",
            "confidence": 0.91,
            "approval_policy": ApprovalPolicy.AUTO_APPLY,
            "test_requirements": ["xss_test"],
            "usage_count": 32,
            "success_rate": 0.94,
            "source": "built-in",
        },
        {
            "playbook_id": "PB-SECRET-001",
            "finding_type": "HARDCODED_SECRET",
            "language": None,
            "framework": None,
            "description": "Replace hardcoded secrets with environment variables",
            "fix_template": "const API_KEY = process.env.API_KEY;",
            "confidence": 0.95,
            "approval_policy": ApprovalPolicy.HUMAN_REVIEW,
            "test_requirements": ["secret_scan"],
            "usage_count": 89,
            "success_rate": 0.98,
            "source": "built-in",
        },
    ]
    
    now = datetime.now()
    for pb in playbooks:
        pb["created_at"] = now
        pb["updated_at"] = now
        _playbooks[pb["playbook_id"]] = pb


_init_built_in_playbooks()


# ============================================
# ENDPOINTS
# ============================================

@router.post("", response_model=PlaybookResponse, status_code=201)
async def create_playbook(playbook: PlaybookCreate) -> PlaybookResponse:
    """Create a new playbook."""
    playbook_id = f"PB-{playbook.finding_type[:4]}-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now()
    
    playbook_data = {
        "playbook_id": playbook_id,
        "finding_type": playbook.finding_type,
        "language": playbook.language,
        "framework": playbook.framework,
        "description": playbook.description,
        "fix_template": playbook.fix_template,
        "confidence": playbook.confidence,
        "approval_policy": playbook.approval_policy,
        "test_requirements": playbook.test_requirements,
        "usage_count": 0,
        "success_rate": 0.0,
        "created_at": now,
        "updated_at": now,
        "source": "custom",
    }
    
    _playbooks[playbook_id] = playbook_data
    logger.info(f"Created playbook: {playbook_id}")
    
    return PlaybookResponse(**playbook_data)


@router.get("", response_model=PlaybooksList)
async def list_playbooks(
    finding_type: Optional[str] = None,
    language: Optional[str] = None,
    min_confidence: float = Query(0, ge=0, le=1),
) -> PlaybooksList:
    """List all playbooks with optional filters."""
    all_playbooks = list(_playbooks.values())
    
    if finding_type:
        all_playbooks = [p for p in all_playbooks if p["finding_type"] == finding_type]
    if language:
        all_playbooks = [p for p in all_playbooks if p["language"] == language]
    if min_confidence > 0:
        all_playbooks = [p for p in all_playbooks if p["confidence"] >= min_confidence]
    
    all_playbooks.sort(key=lambda p: p["confidence"], reverse=True)
    
    return PlaybooksList(
        items=[PlaybookResponse(**p) for p in all_playbooks],
        total=len(all_playbooks),
    )


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: str = Path(..., description="Playbook ID"),
) -> PlaybookResponse:
    """Get a specific playbook."""
    if playbook_id not in _playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    return PlaybookResponse(**_playbooks[playbook_id])


@router.patch("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: str = Path(..., description="Playbook ID"),
    update: PlaybookUpdate = Body(...),
) -> PlaybookResponse:
    """Update a playbook."""
    if playbook_id not in _playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    playbook = _playbooks[playbook_id]
    
    if update.description is not None:
        playbook["description"] = update.description
    if update.fix_template is not None:
        playbook["fix_template"] = update.fix_template
    if update.confidence is not None:
        playbook["confidence"] = update.confidence
    if update.approval_policy is not None:
        playbook["approval_policy"] = update.approval_policy
    
    playbook["updated_at"] = datetime.now()
    
    return PlaybookResponse(**playbook)


@router.delete("/{playbook_id}", status_code=204)
async def delete_playbook(
    playbook_id: str = Path(..., description="Playbook ID"),
) -> None:
    """Delete a playbook."""
    if playbook_id not in _playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    if _playbooks[playbook_id].get("source") == "built-in":
        raise HTTPException(status_code=403, detail="Cannot delete built-in playbooks")
    
    del _playbooks[playbook_id]
    logger.info(f"Deleted playbook: {playbook_id}")


@router.post("/match", response_model=List[PlaybookMatch])
async def find_matching_playbooks(
    finding_type: str = Body(..., embed=True),
    language: Optional[str] = Body(default=None, embed=True),
    framework: Optional[str] = Body(default=None, embed=True),
) -> List[PlaybookMatch]:
    """Find playbooks that match a finding."""
    matches = []
    
    for pb in _playbooks.values():
        if pb["finding_type"] != finding_type:
            continue
        
        match_score = 0.5  # Base match
        
        # Language match
        if language and pb["language"]:
            if pb["language"] == language:
                match_score += 0.25
        elif pb["language"] is None:
            match_score += 0.1  # Generic playbook
        
        # Framework match
        if framework and pb["framework"]:
            if pb["framework"] == framework:
                match_score += 0.25
        elif pb["framework"] is None:
            match_score += 0.1
        
        final_score = match_score * pb["confidence"]
        
        matches.append(PlaybookMatch(
            playbook_id=pb["playbook_id"],
            finding_type=pb["finding_type"],
            confidence=pb["confidence"],
            match_score=final_score,
            requires_review=final_score < 0.8,
        ))
    
    # Sort by match score
    matches.sort(key=lambda m: m.match_score, reverse=True)
    
    return matches


@router.get("/stats/summary")
async def get_playbooks_stats() -> Dict[str, Any]:
    """Get playbook statistics."""
    all_playbooks = list(_playbooks.values())
    
    by_type = {}
    total_usage = 0
    
    for pb in all_playbooks:
        ft = pb["finding_type"]
        by_type[ft] = by_type.get(ft, 0) + 1
        total_usage += pb["usage_count"]
    
    high_confidence = len([p for p in all_playbooks if p["confidence"] >= 0.9])
    
    return {
        "total_playbooks": len(all_playbooks),
        "by_finding_type": by_type,
        "high_confidence_count": high_confidence,
        "total_usage": total_usage,
        "built_in_count": len([p for p in all_playbooks if p.get("source") == "built-in"]),
        "custom_count": len([p for p in all_playbooks if p.get("source") == "custom"]),
    }
