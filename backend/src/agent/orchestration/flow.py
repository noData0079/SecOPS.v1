"""
Flow Orchestration Module

Provides flow-based orchestration for complex multi-step workflows
with state management and conditional routing.

Integrated from crewAI Flow patterns.
"""

from __future__ import annotations

import uuid
import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FlowStatus(str, Enum):
    """Flow execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FlowState:
    """
    Represents the state of a flow execution.
    
    This class maintains the current state of a flow including
    intermediate results, execution history, and any errors.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: FlowStatus = FlowStatus.PENDING
    current_step: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the flow state."""
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the flow state."""
        return self.data.get(key, default)
    
    def add_result(self, step: str, result: Any) -> None:
        """Add a step result."""
        self.results[step] = result
        self.history.append({
            "step": step,
            "result": str(result)[:200],  # Truncate for history
            "timestamp": str(uuid.uuid4())[:8],  # Placeholder for timestamp
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "current_step": self.current_step,
            "data": self.data,
            "results": self.results,
            "history": self.history,
            "error": self.error,
        }


class FlowStep(ABC):
    """Abstract base class for flow steps."""
    
    name: str
    
    @abstractmethod
    def execute(self, state: FlowState) -> Any:
        """Execute this step."""
        pass
    
    @abstractmethod
    def should_execute(self, state: FlowState) -> bool:
        """Check if this step should execute given the current state."""
        pass


@dataclass
class FunctionStep(FlowStep):
    """A flow step that executes a function."""
    
    name: str
    func: Callable[[FlowState], Any]
    condition: Optional[Callable[[FlowState], bool]] = None
    
    def execute(self, state: FlowState) -> Any:
        """Execute the function."""
        return self.func(state)
    
    def should_execute(self, state: FlowState) -> bool:
        """Check condition if provided."""
        if self.condition:
            return self.condition(state)
        return True


class Flow(BaseModel):
    """
    Represents a workflow with multiple steps and conditional routing.
    
    Flows provide a higher-level abstraction for orchestrating complex
    multi-step processes with state management, conditional execution,
    and error handling.
    
    Attributes:
        name: The name of this flow
        description: Description of what the flow does
        initial_state: Initial state data for the flow
        steps: List of steps in the flow
        on_error: Error handler function
        on_complete: Completion handler function
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="Flow name")
    description: str = Field(default="", description="Flow description")
    
    # State
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    
    # Steps (stored as list of callables with names)
    _steps: List[FunctionStep] = []
    _state: FlowState = None
    
    # Handlers
    on_error: Optional[Callable[[FlowState, Exception], None]] = Field(default=None)
    on_complete: Optional[Callable[[FlowState], None]] = Field(default=None)
    
    def __init__(self, **data: Any) -> None:
        """Initialize the flow."""
        super().__init__(**data)
        self._steps = []
        self._state = FlowState(data=self.initial_state.copy())
    
    @property
    def state(self) -> FlowState:
        """Get the current flow state."""
        return self._state
    
    def add_step(
        self,
        name: str,
        func: Callable[[FlowState], Any],
        condition: Optional[Callable[[FlowState], bool]] = None,
    ) -> "Flow":
        """
        Add a step to the flow.
        
        Args:
            name: Step name
            func: Function to execute
            condition: Optional condition for execution
            
        Returns:
            Self for chaining
        """
        step = FunctionStep(name=name, func=func, condition=condition)
        self._steps.append(step)
        return self
    
    def step(
        self,
        name: Optional[str] = None,
        condition: Optional[Callable[[FlowState], bool]] = None,
    ) -> Callable:
        """
        Decorator to add a step to the flow.
        
        Usage:
            @flow.step("process_data")
            def process(state: FlowState) -> Any:
                return state.get("data")
        """
        def decorator(func: Callable[[FlowState], Any]) -> Callable:
            step_name = name or func.__name__
            self.add_step(step_name, func, condition)
            return func
        return decorator
    
    def run(self, inputs: Optional[Dict[str, Any]] = None) -> FlowState:
        """
        Execute the flow.
        
        Args:
            inputs: Optional inputs to merge into initial state
            
        Returns:
            The final flow state
        """
        # Initialize state with inputs
        if inputs:
            self._state.data.update(inputs)
        
        self._state.status = FlowStatus.RUNNING
        
        try:
            for step in self._steps:
                self._state.current_step = step.name
                
                # Check if step should execute
                if not step.should_execute(self._state):
                    logger.debug(f"Skipping step: {step.name}")
                    continue
                
                logger.info(f"Executing flow step: {step.name}")
                
                # Execute the step
                result = step.execute(self._state)
                self._state.add_result(step.name, result)
            
            self._state.status = FlowStatus.COMPLETED
            
            if self.on_complete:
                self.on_complete(self._state)
            
        except Exception as e:
            self._state.status = FlowStatus.FAILED
            self._state.error = str(e)
            
            if self.on_error:
                self.on_error(self._state, e)
            else:
                raise
        
        return self._state
    
    async def run_async(self, inputs: Optional[Dict[str, Any]] = None) -> FlowState:
        """
        Execute the flow asynchronously.
        
        Args:
            inputs: Optional inputs to merge into initial state
            
        Returns:
            The final flow state
        """
        import asyncio
        return await asyncio.to_thread(self.run, inputs)
    
    def pause(self) -> None:
        """Pause the flow execution."""
        self._state.status = FlowStatus.PAUSED
    
    def resume(self) -> FlowState:
        """Resume a paused flow."""
        if self._state.status != FlowStatus.PAUSED:
            raise ValueError("Flow is not paused")
        
        self._state.status = FlowStatus.RUNNING
        
        # Find where we left off and continue
        current_index = 0
        for i, step in enumerate(self._steps):
            if step.name == self._state.current_step:
                current_index = i + 1
                break
        
        # Continue from the next step
        try:
            for step in self._steps[current_index:]:
                self._state.current_step = step.name
                
                if not step.should_execute(self._state):
                    continue
                
                result = step.execute(self._state)
                self._state.add_result(step.name, result)
            
            self._state.status = FlowStatus.COMPLETED
            
        except Exception as e:
            self._state.status = FlowStatus.FAILED
            self._state.error = str(e)
            raise
        
        return self._state
    
    def reset(self) -> None:
        """Reset the flow to initial state."""
        self._state = FlowState(data=self.initial_state.copy())
    
    def copy(self) -> "Flow":
        """Create a copy of this flow."""
        new_flow = Flow(
            name=self.name,
            description=self.description,
            initial_state=self.initial_state.copy(),
            on_error=self.on_error,
            on_complete=self.on_complete,
        )
        new_flow._steps = self._steps.copy()
        return new_flow


# Pre-built SecOps flows
def create_security_assessment_flow(
    target: str,
    scan_agent: Any,
    analyst_agent: Any,
    remediation_agent: Optional[Any] = None,
) -> Flow:
    """
    Create a complete security assessment flow.
    
    This flow performs:
    1. Security scanning
    2. Finding analysis
    3. Risk assessment
    4. Remediation proposals (if agent provided)
    """
    flow = Flow(
        name="Security Assessment",
        description=f"Complete security assessment for {target}",
        initial_state={"target": target},
    )
    
    @flow.step("scan")
    def scan_step(state: FlowState) -> Dict[str, Any]:
        target = state.get("target")
        # In real implementation, this would use the scan_agent
        return {"findings": [], "target": target}
    
    @flow.step("analyze")
    def analyze_step(state: FlowState) -> Dict[str, Any]:
        findings = state.results.get("scan", {}).get("findings", [])
        # In real implementation, this would use the analyst_agent
        return {"risk_score": 0.0, "priority_issues": []}
    
    @flow.step("assess_risk")
    def risk_step(state: FlowState) -> Dict[str, Any]:
        analysis = state.results.get("analyze", {})
        return {"risk_level": "low", "recommendations": []}
    
    if remediation_agent:
        @flow.step("propose_remediation")
        def remediation_step(state: FlowState) -> Dict[str, Any]:
            # In real implementation, this would use the remediation_agent
            return {"fixes": [], "estimated_effort": "low"}
    
    return flow
