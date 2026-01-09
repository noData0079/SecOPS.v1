"""
Task Definition Module

Provides the Task class for defining executable units of work that agents
can perform. Tasks can have dependencies, conditions, outputs, and callbacks.

Integrated from crewAI patterns.
"""

from __future__ import annotations

import uuid
import logging
from enum import Enum
from typing import Any, Callable, Optional, List, Dict, Union, TYPE_CHECKING
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, PrivateAttr, model_validator

if TYPE_CHECKING:
    from .agent import Agent

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class TaskOutput:
    """
    Represents the output of a completed task.
    
    Attributes:
        description: The task description
        raw: The raw output string
        json_output: Parsed JSON output if applicable
        pydantic: Pydantic model output if applicable
        agent: The agent that executed the task
        output_format: The format of the output
    """
    
    description: str
    raw: str
    json_output: Optional[Dict[str, Any]] = None
    pydantic: Optional[Any] = None
    agent: Optional[str] = None
    output_format: str = "raw"
    
    @property
    def result(self) -> Any:
        """Get the most structured output available."""
        if self.pydantic:
            return self.pydantic
        if self.json_output:
            return self.json_output
        return self.raw
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "raw": self.raw,
            "json_output": self.json_output,
            "agent": self.agent,
            "output_format": self.output_format,
        }
    
    def __str__(self) -> str:
        return self.raw


class Task(BaseModel):
    """
    Represents a unit of work that an agent can execute.
    
    Tasks define what needs to be done, who should do it, and what the
    expected output should look like. Tasks can depend on other tasks
    and have conditional execution logic.
    
    Attributes:
        description: What the task should accomplish
        agent: The agent assigned to execute this task
        expected_output: Description of expected output format
        context: List of upstream tasks that provide context
        tools: Override tools for this specific task
        async_execution: Whether to execute asynchronously
        human_input: Whether to require human approval
        output_json: Pydantic model for JSON output parsing
        output_pydantic: Pydantic model for structured output
        output_file: File path to save output
        callback: Function to call after task completion
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(description="Task description")
    expected_output: str = Field(default="", description="Expected output format")
    
    # Assignment
    agent: Optional[Any] = Field(default=None, description="Assigned agent")
    
    # Context and dependencies
    context: Optional[List["Task"]] = Field(default=None, description="Context from other tasks")
    
    # Execution settings
    tools: Optional[List[Any]] = Field(default=None, description="Override tools")
    async_execution: bool = Field(default=False, description="Execute asynchronously")
    human_input: bool = Field(default=False, description="Require human approval")
    
    # Output configuration
    output_json: Optional[Any] = Field(default=None, description="JSON output model")
    output_pydantic: Optional[Any] = Field(default=None, description="Pydantic output model")
    output_file: Optional[str] = Field(default=None, description="Output file path")
    
    # Callbacks
    callback: Optional[Callable] = Field(default=None, description="Completion callback")
    
    # Retry settings
    max_retries: int = Field(default=2, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    
    # Guardrails
    guardrail: Optional[Callable] = Field(default=None, description="Output guardrail function")
    
    # Private state
    _output: Optional[TaskOutput] = PrivateAttr(default=None)
    _status: TaskStatus = PrivateAttr(default=TaskStatus.PENDING)
    _execution_attempts: int = PrivateAttr(default=0)
    _error: Optional[str] = PrivateAttr(default=None)
    
    def __init__(self, **data: Any) -> None:
        """Initialize the task."""
        super().__init__(**data)
        self._output = None
        self._status = TaskStatus.PENDING
        self._execution_attempts = 0
        self._error = None
    
    @property
    def key(self) -> str:
        """Generate a unique key for this task."""
        import hashlib
        source = f"{self.description}|{self.expected_output}"
        return hashlib.md5(source.encode(), usedforsecurity=False).hexdigest()
    
    @property
    def status(self) -> TaskStatus:
        """Get the current task status."""
        return self._status
    
    @property
    def output(self) -> Optional[TaskOutput]:
        """Get the task output."""
        return self._output
    
    @property
    def is_complete(self) -> bool:
        """Check if the task is completed."""
        return self._status == TaskStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if the task has failed."""
        return self._status == TaskStatus.FAILED
    
    def set_output(self, output: Any) -> None:
        """Set the task output."""
        if isinstance(output, TaskOutput):
            self._output = output
        else:
            self._output = TaskOutput(
                description=self.description,
                raw=str(output),
                agent=self.agent.role if self.agent else None,
            )
        self._status = TaskStatus.COMPLETED
    
    def set_failed(self, error: str) -> None:
        """Mark the task as failed."""
        self._status = TaskStatus.FAILED
        self._error = error
        logger.error(f"Task failed: {self.description[:50]}... Error: {error}")
    
    def reset(self) -> None:
        """Reset the task to pending state."""
        self._output = None
        self._status = TaskStatus.PENDING
        self._execution_attempts = 0
        self._error = None
    
    def get_context_output(self) -> str:
        """Get the combined output from context tasks."""
        if not self.context:
            return ""
        
        context_outputs = []
        for task in self.context:
            if task.output:
                context_outputs.append(f"# Context from: {task.description}\n{task.output.raw}")
        
        return "\n\n".join(context_outputs)
    
    def interpolate_inputs(self, inputs: Dict[str, Any]) -> str:
        """Interpolate inputs into the task description."""
        description = self.description
        for key, value in inputs.items():
            description = description.replace(f"{{{key}}}", str(value))
        return description
    
    def execute(
        self,
        agent: Optional[Any] = None,
        context: Optional[str] = None,
        tools: Optional[List[Any]] = None,
    ) -> TaskOutput:
        """
        Execute the task.
        
        Args:
            agent: Override the assigned agent
            context: Additional context string
            tools: Override tools
            
        Returns:
            TaskOutput containing the result
        """
        executing_agent = agent or self.agent
        if not executing_agent:
            raise ValueError("No agent assigned to execute this task")
        
        self._status = TaskStatus.IN_PROGRESS
        self._execution_attempts += 1
        
        try:
            # Combine context from dependencies
            full_context = self.get_context_output()
            if context:
                full_context = f"{full_context}\n\n{context}" if full_context else context
            
            # Execute through the agent
            result = executing_agent.execute_task(
                task=self.description,
                context=full_context,
                tools=tools or self.tools,
            )
            
            # Create the output
            output = TaskOutput(
                description=self.description,
                raw=str(result) if result else "",
                agent=executing_agent.role,
            )
            
            # Apply guardrail if set
            if self.guardrail:
                guard_result = self.guardrail(output)
                if not guard_result:
                    raise ValueError("Output failed guardrail check")
            
            self.set_output(output)
            
            # Call completion callback
            if self.callback:
                self.callback(output)
            
            # Save to file if configured
            if self.output_file:
                self._save_to_file(output)
            
            return output
            
        except Exception as e:
            if self._execution_attempts < self.max_retries:
                import time
                time.sleep(self.retry_delay)
                return self.execute(agent, context, tools)
            
            self.set_failed(str(e))
            raise
    
    def _save_to_file(self, output: TaskOutput) -> None:
        """Save output to file."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(output.raw)
            logger.debug(f"Task output saved to: {self.output_file}")
        except Exception as e:
            logger.warning(f"Failed to save output to file: {e}")
    
    def copy(self) -> "Task":
        """Create a copy of this task."""
        return Task(
            description=self.description,
            expected_output=self.expected_output,
            agent=self.agent,
            context=self.context.copy() if self.context else None,
            tools=self.tools.copy() if self.tools else None,
            async_execution=self.async_execution,
            human_input=self.human_input,
            output_file=self.output_file,
            callback=self.callback,
            max_retries=self.max_retries,
        )
    
    def __repr__(self) -> str:
        return f"Task(description='{self.description[:50]}...', status={self._status.value})"
    
    def __str__(self) -> str:
        return self.description


class ConditionalTask(Task):
    """
    A task that executes conditionally based on previous task outputs.
    
    The condition function receives the previous task's output and returns
    True if this task should execute, False otherwise.
    """
    
    condition: Callable[[TaskOutput], bool] = Field(
        description="Condition function that determines if task should execute"
    )
    
    def should_execute(self, previous_output: Optional[TaskOutput]) -> bool:
        """Check if this task should execute based on the condition."""
        if previous_output is None:
            return False
        
        try:
            return self.condition(previous_output)
        except Exception as e:
            logger.warning(f"Condition check failed: {e}")
            return False


# Task factory functions for common SecOps tasks
def create_security_scan_task(
    target: str,
    scan_type: str = "full",
    agent: Optional[Any] = None,
    **kwargs: Any,
) -> Task:
    """Create a security scanning task."""
    return Task(
        description=f"Perform a {scan_type} security scan on {target}. Identify vulnerabilities, misconfigurations, and compliance issues.",
        expected_output="A detailed security report with findings categorized by severity",
        agent=agent,
        **kwargs,
    )


def create_analysis_task(
    context_tasks: List[Task],
    focus_area: str = "risk",
    agent: Optional[Any] = None,
    **kwargs: Any,
) -> Task:
    """Create a security analysis task."""
    return Task(
        description=f"Analyze the security findings with focus on {focus_area}. Provide risk assessment and prioritized recommendations.",
        expected_output="Risk analysis report with prioritized action items",
        agent=agent,
        context=context_tasks,
        **kwargs,
    )


def create_remediation_task(
    context_tasks: List[Task],
    auto_fix: bool = False,
    agent: Optional[Any] = None,
    **kwargs: Any,
) -> Task:
    """Create a remediation task."""
    action = "Implement fixes for" if auto_fix else "Develop remediation proposals for"
    return Task(
        description=f"{action} the identified security issues. Ensure fixes don't break existing functionality.",
        expected_output="Remediation plan or implemented fixes with verification results",
        agent=agent,
        context=context_tasks,
        human_input=not auto_fix,  # Require human approval if auto-fix is off
        **kwargs,
    )
