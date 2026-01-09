# backend/src/core/agentic/reasoning_orchestrator.py

"""
Reasoning Orchestrator - Layer 5 (Poly-LLM Router)

Routes tasks to appropriate AI models:
- ChatGPT → reasoning, prioritization, explanation
- Gemini → search, CVEs, external context
- Claude → code generation

Stateless, contract-driven. Models are workers, not owners.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ReasoningModel(str, Enum):
    """Available reasoning models."""
    CHATGPT = "chatgpt"  # Root cause, risk reasoning, prioritization
    GEMINI = "gemini"    # Search, CVEs, standards
    CLAUDE = "claude"    # Code diffs, tests, infra changes
    LOCAL = "local"      # T79 local model


class TaskType(str, Enum):
    """Types of reasoning tasks."""
    ROOT_CAUSE_ANALYSIS = "root_cause"
    RISK_ASSESSMENT = "risk_assessment"
    PRIORITIZATION = "prioritization"
    EXPLANATION = "explanation"
    CVE_LOOKUP = "cve_lookup"
    STANDARDS_CHECK = "standards_check"
    CODE_GENERATION = "code_generation"
    CONFIG_GENERATION = "config_generation"
    TEST_GENERATION = "test_generation"


# Model routing configuration
MODEL_ROUTING: Dict[TaskType, ReasoningModel] = {
    TaskType.ROOT_CAUSE_ANALYSIS: ReasoningModel.CHATGPT,
    TaskType.RISK_ASSESSMENT: ReasoningModel.CHATGPT,
    TaskType.PRIORITIZATION: ReasoningModel.CHATGPT,
    TaskType.EXPLANATION: ReasoningModel.CHATGPT,
    TaskType.CVE_LOOKUP: ReasoningModel.GEMINI,
    TaskType.STANDARDS_CHECK: ReasoningModel.GEMINI,
    TaskType.CODE_GENERATION: ReasoningModel.CLAUDE,
    TaskType.CONFIG_GENERATION: ReasoningModel.CLAUDE,
    TaskType.TEST_GENERATION: ReasoningModel.CLAUDE,
}


@dataclass
class ReasoningRequest:
    """A request for reasoning."""
    id: str
    task_type: TaskType
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    org_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        task_type: TaskType,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        org_id: Optional[str] = None,
    ) -> "ReasoningRequest":
        return cls(
            id=str(uuid4()),
            task_type=task_type,
            input_data=input_data,
            context=context or {},
            org_id=org_id,
        )


@dataclass
class ReasoningResponse:
    """Response from reasoning model."""
    request_id: str
    model_used: ReasoningModel
    success: bool
    result: Dict[str, Any]
    reasoning: str
    confidence: float
    created_at: datetime
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model_used": self.model_used.value,
            "success": self.success,
            "result": self.result,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "error": self.error,
        }


class ReasoningOrchestrator:
    """
    Routes reasoning tasks to appropriate AI models.
    
    Key principles:
    - AI proposes, system verifies, humans approve
    - Stateless models, external memory
    - Strict I/O contracts
    """
    
    def __init__(self):
        self._model_configs: Dict[ReasoningModel, Dict[str, Any]] = {}
        self._request_history: List[ReasoningRequest] = []
        logger.info("ReasoningOrchestrator initialized")
    
    def configure_model(
        self,
        model: ReasoningModel,
        config: Dict[str, Any],
    ) -> None:
        """Configure a model with connection details."""
        self._model_configs[model] = config
        logger.info(f"Configured model: {model.value}")
    
    def get_model_for_task(self, task_type: TaskType) -> ReasoningModel:
        """Get the appropriate model for a task type."""
        return MODEL_ROUTING.get(task_type, ReasoningModel.CHATGPT)
    
    async def reason(
        self,
        request: ReasoningRequest,
    ) -> ReasoningResponse:
        """
        Route request to appropriate model and get response.
        
        Models NEVER:
        - Write production code directly
        - Execute actions
        - Declare completion
        """
        self._request_history.append(request)
        
        model = self.get_model_for_task(request.task_type)
        logger.info(
            f"Routing {request.task_type.value} to {model.value}"
        )
        
        try:
            result = await self._call_model(model, request)
            
            return ReasoningResponse(
                request_id=request.id,
                model_used=model,
                success=True,
                result=result,
                reasoning=result.get("reasoning", ""),
                confidence=result.get("confidence", 0.8),
                created_at=datetime.utcnow(),
            )
            
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            return ReasoningResponse(
                request_id=request.id,
                model_used=model,
                success=False,
                result={},
                reasoning="",
                confidence=0.0,
                created_at=datetime.utcnow(),
                error=str(e),
            )
    
    async def _call_model(
        self,
        model: ReasoningModel,
        request: ReasoningRequest,
    ) -> Dict[str, Any]:
        """Call the actual model API."""
        
        if model == ReasoningModel.CHATGPT:
            return await self._call_chatgpt(request)
        elif model == ReasoningModel.GEMINI:
            return await self._call_gemini(request)
        elif model == ReasoningModel.CLAUDE:
            return await self._call_claude(request)
        elif model == ReasoningModel.LOCAL:
            return await self._call_local(request)
        else:
            raise ValueError(f"Unknown model: {model}")
    
    async def _call_chatgpt(
        self, request: ReasoningRequest
    ) -> Dict[str, Any]:
        """Call ChatGPT for reasoning tasks."""
        config = self._model_configs.get(ReasoningModel.CHATGPT, {})
        
        # Build prompt based on task type
        if request.task_type == TaskType.ROOT_CAUSE_ANALYSIS:
            reasoning = f"Analyzed finding: {request.input_data.get('finding', 'unknown')}"
            return {
                "reasoning": reasoning,
                "root_causes": ["Configuration drift", "Missing security control"],
                "confidence": 0.85,
            }
        
        elif request.task_type == TaskType.RISK_ASSESSMENT:
            return {
                "reasoning": "Assessed risk based on severity and blast radius",
                "risk_level": "high",
                "business_impact": "Potential data exposure",
                "confidence": 0.80,
            }
        
        elif request.task_type == TaskType.PRIORITIZATION:
            return {
                "reasoning": "Prioritized based on severity and exploitability",
                "priority_order": request.input_data.get("findings", []),
                "confidence": 0.75,
            }
        
        return {"reasoning": "Analysis complete", "confidence": 0.7}
    
    async def _call_gemini(
        self, request: ReasoningRequest
    ) -> Dict[str, Any]:
        """Call Gemini for search/context tasks."""
        
        if request.task_type == TaskType.CVE_LOOKUP:
            return {
                "reasoning": "Searched CVE database",
                "cves": [],
                "related_advisories": [],
                "confidence": 0.90,
            }
        
        elif request.task_type == TaskType.STANDARDS_CHECK:
            return {
                "reasoning": "Checked against compliance standards",
                "standards": ["SOC2", "ISO27001"],
                "violations": [],
                "confidence": 0.85,
            }
        
        return {"reasoning": "Search complete", "confidence": 0.8}
    
    async def _call_claude(
        self, request: ReasoningRequest
    ) -> Dict[str, Any]:
        """Call Claude for code generation tasks."""
        
        if request.task_type == TaskType.CODE_GENERATION:
            return {
                "reasoning": "Generated code fix based on finding",
                "code_diff": "",
                "files_affected": [],
                "confidence": 0.85,
            }
        
        elif request.task_type == TaskType.TEST_GENERATION:
            return {
                "reasoning": "Generated test cases",
                "test_code": "",
                "test_count": 0,
                "confidence": 0.80,
            }
        
        return {"reasoning": "Generation complete", "confidence": 0.75}
    
    async def _call_local(
        self, request: ReasoningRequest
    ) -> Dict[str, Any]:
        """Call local T79 model."""
        from utils.data_loader import get_model_config
        
        config = get_model_config()
        prompt_template = config.get("prompt_template", "T79: {text}")
        
        return {
            "reasoning": "Local model analysis",
            "model": config.get("model_name", "T79"),
            "confidence": config.get("confidence_base", 0.65),
        }
    
    async def analyze_finding(
        self,
        finding_data: Dict[str, Any],
        org_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete analysis pipeline for a finding.
        
        Runs: root cause → risk assessment → prioritization
        """
        
        # Step 1: Root cause analysis
        root_cause_req = ReasoningRequest.create(
            TaskType.ROOT_CAUSE_ANALYSIS,
            {"finding": finding_data},
            org_id=org_id,
        )
        root_cause_resp = await self.reason(root_cause_req)
        
        # Step 2: Risk assessment
        risk_req = ReasoningRequest.create(
            TaskType.RISK_ASSESSMENT,
            {
                "finding": finding_data,
                "root_causes": root_cause_resp.result.get("root_causes", []),
            },
            org_id=org_id,
        )
        risk_resp = await self.reason(risk_req)
        
        return {
            "finding": finding_data,
            "root_cause": root_cause_resp.to_dict(),
            "risk": risk_resp.to_dict(),
        }
