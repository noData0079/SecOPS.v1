"""
Agent Definition Module

Provides the core Agent class for defining intelligent agents with specific roles,
goals, and capabilities. Agents can be equipped with tools and memory to perform
complex tasks autonomously.

Integrated from crewAI patterns.
"""

from __future__ import annotations

import uuid
import logging
from enum import Enum
from typing import Any, Callable, Optional, List, Dict, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, PrivateAttr

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Predefined agent roles for SecOps."""
    
    SECURITY_SCANNER = "security_scanner"
    SECURITY_ANALYST = "security_analyst"
    THREAT_HUNTER = "threat_hunter"
    INCIDENT_RESPONDER = "incident_responder"
    COMPLIANCE_AUDITOR = "compliance_auditor"
    VULNERABILITY_ASSESSOR = "vulnerability_assessor"
    REMEDIATION_ENGINEER = "remediation_engineer"
    CODE_REVIEWER = "code_reviewer"
    DEVOPS_ENGINEER = "devops_engineer"
    RISK_ANALYST = "risk_analyst"
    CUSTOM = "custom"


@dataclass
class AgentConfig:
    """Configuration for agent initialization."""
    
    role: str
    goal: str
    backstory: str = ""
    llm_model: str = "gpt-4"
    max_iterations: int = 25
    max_rpm: Optional[int] = None
    memory: bool = True
    verbose: bool = False
    allow_delegation: bool = True
    cache: bool = True
    max_retry_limit: int = 2
    respect_context_window: bool = True
    code_execution_mode: str = "safe"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
            "llm_model": self.llm_model,
            "max_iterations": self.max_iterations,
            "max_rpm": self.max_rpm,
            "memory": self.memory,
            "verbose": self.verbose,
            "allow_delegation": self.allow_delegation,
            "cache": self.cache,
            "max_retry_limit": self.max_retry_limit,
            "respect_context_window": self.respect_context_window,
            "code_execution_mode": self.code_execution_mode,
        }


class BaseTool(ABC):
    """Abstract base class for agent tools."""
    
    name: str
    description: str
    
    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool."""
        pass
    
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """Return the tool schema for LLM function calling."""
        pass


class Agent(BaseModel):
    """
    Represents an intelligent agent with specific capabilities.
    
    An agent is defined by its role, goal, and backstory, and can be equipped
    with tools and memory to perform complex tasks. Agents can work independently
    or as part of a crew.
    
    Attributes:
        role: The role of the agent (e.g., "Security Analyst")
        goal: What the agent is trying to achieve
        backstory: Background context for the agent's behavior
        tools: List of tools available to the agent
        llm: The language model powering the agent
        memory: Whether the agent should use memory
        verbose: Whether to enable verbose logging
        allow_delegation: Whether the agent can delegate to others
        max_iterations: Maximum iterations for task execution
        max_rpm: Maximum requests per minute
        cache: Whether to cache tool results
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = Field(description="The role of the agent")
    goal: str = Field(description="The goal the agent is trying to achieve")
    backstory: str = Field(default="", description="Background context for the agent")
    
    # Tools and capabilities
    tools: List[Any] = Field(default_factory=list, description="Tools available to the agent")
    llm: Optional[Any] = Field(default=None, description="Language model for the agent")
    function_calling_llm: Optional[Any] = Field(default=None, description="LLM for function calling")
    
    # Behavior settings
    memory: bool = Field(default=True, description="Whether to use memory")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    allow_delegation: bool = Field(default=True, description="Allow task delegation")
    allow_code_execution: bool = Field(default=False, description="Allow code execution")
    code_execution_mode: str = Field(default="safe", description="Code execution mode: safe, docker, unsafe")
    
    # Limits and constraints
    max_iterations: int = Field(default=25, description="Maximum iterations for task execution")
    max_rpm: Optional[int] = Field(default=None, description="Maximum requests per minute")
    max_retry_limit: int = Field(default=2, description="Maximum retries on failure")
    respect_context_window: bool = Field(default=True, description="Stay within context window")
    
    # Caching
    cache: bool = Field(default=True, description="Cache tool results")
    
    # Callbacks
    step_callback: Optional[Callable] = Field(default=None, description="Callback after each step")
    
    # Private attributes
    _cache_handler: Any = PrivateAttr(default=None)
    _rpm_controller: Any = PrivateAttr(default=None)
    _token_usage: Dict[str, int] = PrivateAttr(default_factory=dict)
    _execution_history: List[Dict[str, Any]] = PrivateAttr(default_factory=list)
    
    def __init__(self, **data: Any) -> None:
        """Initialize the agent."""
        super().__init__(**data)
        self._setup_agent()
    
    def _setup_agent(self) -> None:
        """Setup agent internals."""
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        self._execution_history = []
        logger.debug(f"Agent '{self.role}' initialized with goal: {self.goal}")
    
    @property
    def key(self) -> str:
        """Generate a unique key for this agent configuration."""
        import hashlib
        source = f"{self.role}|{self.goal}|{len(self.tools)}"
        return hashlib.md5(source.encode(), usedforsecurity=False).hexdigest()
    
    def set_cache_handler(self, handler: Any) -> None:
        """Set the cache handler for tool results."""
        self._cache_handler = handler
    
    def set_rpm_controller(self, controller: Any) -> None:
        """Set the RPM controller for rate limiting."""
        self._rpm_controller = controller
    
    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent's toolkit."""
        self.tools.append(tool)
        logger.debug(f"Tool added to agent '{self.role}': {getattr(tool, 'name', str(tool))}")
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool by name."""
        for i, tool in enumerate(self.tools):
            if getattr(tool, "name", "") == tool_name:
                self.tools.pop(i)
                logger.debug(f"Tool '{tool_name}' removed from agent '{self.role}'")
                return True
        return False
    
    def execute_task(
        self,
        task: Any,
        context: Optional[str] = None,
        tools: Optional[List[Any]] = None,
    ) -> Any:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: The task to execute
            context: Additional context for the task
            tools: Override tools for this specific task
            
        Returns:
            The task execution result
        """
        execution_tools = tools if tools is not None else self.tools
        
        self._execution_history.append({
            "task": str(task),
            "context": context,
            "tools_count": len(execution_tools),
        })
        
        # Placeholder for actual LLM execution
        # This would be replaced with actual implementation
        logger.info(f"Agent '{self.role}' executing task: {task}")
        
        return self._run_agent_loop(task, context, execution_tools)
    
    def _run_agent_loop(
        self,
        task: Any,
        context: Optional[str],
        tools: List[Any],
    ) -> Any:
        """
        Run the agent's reasoning loop.
        
        This implements a ReAct-style loop where the agent:
        1. Thinks about the task
        2. Decides on an action
        3. Executes the action
        4. Observes the result
        5. Repeats until task is complete
        """
        iterations = 0
        result = None
        
        while iterations < self.max_iterations:
            iterations += 1
            
            if self.verbose:
                logger.info(f"Agent '{self.role}' iteration {iterations}/{self.max_iterations}")
            
            # In actual implementation, this would:
            # 1. Call LLM to get next action
            # 2. Execute tool if needed
            # 3. Collect observation
            # 4. Check if task is complete
            
            # Placeholder: Mark as complete after first iteration
            result = {
                "status": "completed",
                "iterations": iterations,
                "agent": self.role,
                "task": str(task),
            }
            break
        
        if self.step_callback:
            self.step_callback(result)
        
        return result
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get the agent's token usage statistics."""
        return self._token_usage.copy()
    
    def reset(self) -> None:
        """Reset the agent's state."""
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        self._execution_history = []
        logger.debug(f"Agent '{self.role}' reset")
    
    def copy(self) -> "Agent":
        """Create a shallow copy of the agent."""
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools.copy(),
            llm=self.llm,
            memory=self.memory,
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            max_iterations=self.max_iterations,
            max_rpm=self.max_rpm,
            cache=self.cache,
        )
    
    def __repr__(self) -> str:
        return f"Agent(role='{self.role}', goal='{self.goal[:50]}...')"
    
    def __str__(self) -> str:
        return f"Agent: {self.role}"


# Pre-configured SecOps agents
def create_security_scanner_agent(
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
    **kwargs: Any,
) -> Agent:
    """Create a pre-configured security scanning agent."""
    return Agent(
        role="Security Scanner",
        goal="Identify security vulnerabilities, misconfigurations, and compliance issues across infrastructure and applications",
        backstory="""You are an expert security scanner with deep knowledge of cloud security,
        application security, and compliance frameworks. You systematically analyze systems
        to identify potential security issues and risks.""",
        tools=tools or [],
        llm=llm,
        allow_code_execution=True,
        code_execution_mode="safe",
        **kwargs,
    )


def create_security_analyst_agent(
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
    **kwargs: Any,
) -> Agent:
    """Create a pre-configured security analysis agent."""
    return Agent(
        role="Security Analyst",
        goal="Analyze security findings, assess risk levels, and provide prioritized recommendations",
        backstory="""You are a seasoned security analyst with expertise in threat analysis,
        risk assessment, and security operations. You excel at contextualizing findings
        and providing actionable intelligence.""",
        tools=tools or [],
        llm=llm,
        **kwargs,
    )


def create_remediation_agent(
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
    **kwargs: Any,
) -> Agent:
    """Create a pre-configured remediation agent."""
    return Agent(
        role="Remediation Engineer",
        goal="Develop and execute fixes for identified security issues",
        backstory="""You are an expert at developing secure code fixes and infrastructure
        remediations. You understand security best practices and can implement changes
        that address vulnerabilities while maintaining system functionality.""",
        tools=tools or [],
        llm=llm,
        allow_code_execution=True,
        code_execution_mode="docker",
        **kwargs,
    )


def create_compliance_auditor_agent(
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
    **kwargs: Any,
) -> Agent:
    """Create a pre-configured compliance auditor agent."""
    return Agent(
        role="Compliance Auditor",
        goal="Verify compliance with security frameworks and regulatory requirements",
        backstory="""You are a compliance expert with thorough knowledge of security
        frameworks including CIS, SOC2, HIPAA, PCI-DSS, and GDPR. You systematically
        verify compliance and document findings.""",
        tools=tools or [],
        llm=llm,
        **kwargs,
    )
