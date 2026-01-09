"""
Security Findings API Endpoints

RESTful API for managing security findings, playbooks, and the learning system.
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

router = APIRouter(prefix="/findings", tags=["findings"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"
    FALSE_POSITIVE = "false_positive"


class FindingCreate(BaseModel):
    """Create a new security finding."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    finding_type: str = Field(..., description="e.g., SQL_INJECTION, XSS")
    severity: Severity = Field(default=Severity.MEDIUM)
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    source: str = Field(default="manual", description="scanner, manual, ai")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FindingResponse(BaseModel):
    """Security finding response."""
    finding_id: str
    title: str
    description: str
    finding_type: str
    severity: Severity
    status: FindingStatus
    file_path: Optional[str]
    line_number: Optional[int]
    code_snippet: Optional[str]
    source: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    fixed_at: Optional[datetime]


class FindingUpdate(BaseModel):
    """Update a security finding."""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[Severity] = None
    status: Optional[FindingStatus] = None


class FixRequest(BaseModel):
    """Request to fix a finding."""
    use_playbook: bool = Field(default=True, description="Try playbook first")
    force_llm: bool = Field(default=False, description="Force LLM usage")
    auto_apply: bool = Field(default=False, description="Auto-apply if confident")


class FixResponse(BaseModel):
    """Fix execution response."""
    fix_id: str
    finding_id: str
    fix_source: str  # playbook, llm, manual
    playbook_id: Optional[str]
    fix_suggestion: str
    confidence: float
    auto_applied: bool
    requires_review: bool
    created_at: datetime


class FindingsList(BaseModel):
    """Paginated list of findings."""
    items: List[FindingResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================
# IN-MEMORY STORAGE (replace with database)
# ============================================

_findings: Dict[str, Dict[str, Any]] = {}
_fixes: Dict[str, Dict[str, Any]] = {}


# ============================================
# ENDPOINTS
# ============================================

@router.post("", response_model=FindingResponse, status_code=201)
async def create_finding(finding: FindingCreate) -> FindingResponse:
    """Create a new security finding."""
    finding_id = str(uuid.uuid4())
    now = datetime.now()
    
    finding_data = {
        "finding_id": finding_id,
        "title": finding.title,
        "description": finding.description,
        "finding_type": finding.finding_type,
        "severity": finding.severity,
        "status": FindingStatus.OPEN,
        "file_path": finding.file_path,
        "line_number": finding.line_number,
        "code_snippet": finding.code_snippet,
        "source": finding.source,
        "metadata": finding.metadata,
        "created_at": now,
        "updated_at": now,
        "fixed_at": None,
    }
    
    _findings[finding_id] = finding_data
    logger.info(f"Created finding: {finding_id}")
    
    return FindingResponse(**finding_data)


@router.get("", response_model=FindingsList)
async def list_findings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[Severity] = None,
    status: Optional[FindingStatus] = None,
    finding_type: Optional[str] = None,
) -> FindingsList:
    """List security findings with pagination and filters."""
    all_findings = list(_findings.values())
    
    # Apply filters
    if severity:
        all_findings = [f for f in all_findings if f["severity"] == severity]
    if status:
        all_findings = [f for f in all_findings if f["status"] == status]
    if finding_type:
        all_findings = [f for f in all_findings if f["finding_type"] == finding_type]
    
    # Sort by created_at descending
    all_findings.sort(key=lambda f: f["created_at"], reverse=True)
    
    # Paginate
    total = len(all_findings)
    start = (page - 1) * page_size
    end = start + page_size
    items = all_findings[start:end]
    
    return FindingsList(
        items=[FindingResponse(**f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str = Path(..., description="Finding ID"),
) -> FindingResponse:
    """Get a specific finding by ID."""
    if finding_id not in _findings:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return FindingResponse(**_findings[finding_id])


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str = Path(..., description="Finding ID"),
    update: FindingUpdate = Body(...),
) -> FindingResponse:
    """Update a finding."""
    if finding_id not in _findings:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    finding = _findings[finding_id]
    
    if update.title is not None:
        finding["title"] = update.title
    if update.description is not None:
        finding["description"] = update.description
    if update.severity is not None:
        finding["severity"] = update.severity
    if update.status is not None:
        finding["status"] = update.status
        if update.status == FindingStatus.FIXED:
            finding["fixed_at"] = datetime.now()
    
    finding["updated_at"] = datetime.now()
    
    return FindingResponse(**finding)


@router.delete("/{finding_id}", status_code=204)
async def delete_finding(
    finding_id: str = Path(..., description="Finding ID"),
) -> None:
    """Delete a finding."""
    if finding_id not in _findings:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    del _findings[finding_id]
    logger.info(f"Deleted finding: {finding_id}")


@router.post("/{finding_id}/fix", response_model=FixResponse)
async def request_fix(
    finding_id: str = Path(..., description="Finding ID"),
    request: FixRequest = Body(...),
) -> FixResponse:
    """
    Request a fix for a finding.
    
    The system will:
    1. Check for matching playbooks if use_playbook=True
    2. Fall back to LLM if no playbook or force_llm=True
    3. Auto-apply if confident and auto_apply=True
    """
    if finding_id not in _findings:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    finding = _findings[finding_id]
    fix_id = str(uuid.uuid4())
    now = datetime.now()
    
    # Simulate fix decision (in production, use LearningLoopOrchestrator)
    fix_source = "playbook" if request.use_playbook else "llm"
    playbook_id = None
    confidence = 0.85
    fix_suggestion = f"Apply standard fix for {finding['finding_type']}"
    
    if request.force_llm:
        fix_source = "llm"
        confidence = 0.75
        fix_suggestion = f"LLM-generated fix for {finding['finding_type']}"
    
    auto_applied = request.auto_apply and confidence > 0.9
    requires_review = confidence < 0.85
    
    fix_data = {
        "fix_id": fix_id,
        "finding_id": finding_id,
        "fix_source": fix_source,
        "playbook_id": playbook_id,
        "fix_suggestion": fix_suggestion,
        "confidence": confidence,
        "auto_applied": auto_applied,
        "requires_review": requires_review,
        "created_at": now,
    }
    
    _fixes[fix_id] = fix_data
    
    # Update finding status
    finding["status"] = FindingStatus.IN_PROGRESS
    finding["updated_at"] = now
    
    logger.info(f"Created fix: {fix_id} for finding: {finding_id}")
    
    return FixResponse(**fix_data)


@router.get("/stats/summary")
async def get_findings_stats() -> Dict[str, Any]:
    """Get summary statistics of findings."""
    all_findings = list(_findings.values())
    
    by_severity = {}
    by_status = {}
    by_type = {}
    
    for f in all_findings:
        sev = f["severity"].value if hasattr(f["severity"], "value") else f["severity"]
        stat = f["status"].value if hasattr(f["status"], "value") else f["status"]
        ft = f["finding_type"]
        
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_status[stat] = by_status.get(stat, 0) + 1
        by_type[ft] = by_type.get(ft, 0) + 1
    
    return {
        "total": len(all_findings),
        "by_severity": by_severity,
        "by_status": by_status,
        "by_type": by_type,
        "generated_at": datetime.now().isoformat(),
    }
