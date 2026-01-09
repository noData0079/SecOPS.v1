"""
Crew Orchestration Module

Provides the Crew class for orchestrating multiple agents to work together
on complex tasks. Crews manage agent coordination, task execution, and
result aggregation.

Integrated from crewAI patterns.
"""

from __future__ import annotations

import uuid
import asyncio
import logging
from concurrent.futures import Future, ThreadPoolExecutor
from copy import copy as shallow_copy
from hashlib import md5
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from .agent import Agent
from .task import Task, TaskOutput, TaskStatus
from .process import Process
from .flow import FlowState

logger = logging.getLogger(__name__)


@dataclass
class UsageMetrics:
    """Track LLM usage metrics across the crew."""
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    
    def add(self, other: "UsageMetrics") -> None:
        """Add another UsageMetrics to this one."""
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        self.successful_requests += other.successful_requests
        self.failed_requests += other.failed_requests
        self.total_cost += other.total_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_cost": self.total_cost,
        }


@dataclass
class CrewOutput:
    """
    Represents the output of a crew execution.
    
    Attributes:
        raw: Raw string output
        json_output: Parsed JSON if applicable
        pydantic: Pydantic model if applicable
        tasks_output: Individual task outputs
        token_usage: Token usage metrics
    """
    
    raw: str
    json_output: Optional[Dict[str, Any]] = None
    pydantic: Optional[Any] = None
    tasks_output: List[TaskOutput] = field(default_factory=list)
    token_usage: Optional[UsageMetrics] = None
    
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
            "raw": self.raw,
            "json_output": self.json_output,
            "tasks_output": [t.to_dict() for t in self.tasks_output],
            "token_usage": self.token_usage.to_dict() if self.token_usage else None,
        }
    
    def __str__(self) -> str:
        return self.raw


class Crew(BaseModel):
    """
    Represents a team of agents working together on tasks.
    
    A Crew orchestrates multiple agents to complete a series of tasks,
    managing communication, delegation, and result aggregation.
    
    Attributes:
        name: Name of the crew
        agents: List of agents in the crew
        tasks: List of tasks to execute
        process: Execution process (sequential, hierarchical, parallel)
        verbose: Enable verbose logging
        memory: Enable crew memory
        cache: Enable result caching
        max_rpm: Maximum requests per minute
        manager_llm: LLM for manager agent in hierarchical mode
        manager_agent: Custom manager agent
        planning: Enable task planning before execution
        planning_llm: LLM for planning
        step_callback: Callback after each step
        task_callback: Callback after each task
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(default="crew", description="Crew name")
    
    # Team composition
    agents: List[Agent] = Field(default_factory=list, description="Agents in the crew")
    tasks: List[Task] = Field(default_factory=list, description="Tasks to execute")
    
    # Execution settings
    process: Process = Field(default=Process.sequential, description="Execution process")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    
    # Memory and caching
    memory: bool = Field(default=False, description="Enable crew memory")
    cache: bool = Field(default=True, description="Enable result caching")
    
    # Rate limiting
    max_rpm: Optional[int] = Field(default=None, description="Max requests per minute")
    
    # Hierarchical mode settings
    manager_llm: Optional[Any] = Field(default=None, description="Manager LLM")
    manager_agent: Optional[Agent] = Field(default=None, description="Custom manager")
    
    # Planning
    planning: bool = Field(default=False, description="Enable planning")
    planning_llm: Optional[Any] = Field(default=None, description="Planning LLM")
    
    # Callbacks
    step_callback: Optional[Callable] = Field(default=None, description="Step callback")
    task_callback: Optional[Callable] = Field(default=None, description="Task callback")
    before_kickoff_callbacks: List[Callable] = Field(default_factory=list)
    after_kickoff_callbacks: List[Callable] = Field(default_factory=list)
    
    # Output settings
    output_log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Private state
    _usage_metrics: UsageMetrics = PrivateAttr(default_factory=UsageMetrics)
    _execution_logs: List[Dict[str, Any]] = PrivateAttr(default_factory=list)
    _inputs: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, **data: Any) -> None:
        """Initialize the crew."""
        super().__init__(**data)
        self._usage_metrics = UsageMetrics()
        self._execution_logs = []
        self._inputs = None
        self._validate_crew()
    
    def _validate_crew(self) -> None:
        """Validate crew configuration."""
        if self.process == Process.hierarchical:
            if not self.manager_llm and not self.manager_agent:
                raise ValueError(
                    "Hierarchical process requires either manager_llm or manager_agent"
                )
            if self.manager_agent and self.manager_agent in self.agents:
                raise ValueError("Manager agent should not be in the agents list")
        
        if self.process == Process.sequential:
            for task in self.tasks:
                if task.agent is None:
                    raise ValueError(
                        f"Sequential process requires all tasks to have agents. "
                        f"Task missing agent: {task.description[:50]}"
                    )
    
    @property
    def key(self) -> str:
        """Generate a unique key for this crew configuration."""
        source = [agent.key for agent in self.agents] + [task.key for task in self.tasks]
        return md5("|".join(source).encode(), usedforsecurity=False).hexdigest()
    
    @property
    def usage_metrics(self) -> UsageMetrics:
        """Get the crew's usage metrics."""
        return self._usage_metrics
    
    def kickoff(
        self,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> CrewOutput:
        """
        Start the crew execution.
        
        Args:
            inputs: Input data to pass to tasks
            
        Returns:
            CrewOutput containing all results
        """
        self._inputs = inputs or {}
        
        # Run before callbacks
        for callback in self.before_kickoff_callbacks:
            self._inputs = callback(self._inputs) or self._inputs
        
        logger.info(f"Crew '{self.name}' starting with process: {self.process.value}")
        
        try:
            if self.process == Process.sequential:
                result = self._run_sequential()
            elif self.process == Process.hierarchical:
                result = self._run_hierarchical()
            elif self.process == Process.parallel:
                result = self._run_parallel()
            else:
                raise ValueError(f"Unknown process: {self.process}")
            
            # Run after callbacks
            for callback in self.after_kickoff_callbacks:
                result = callback(result) or result
            
            return result
            
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            raise
    
    async def kickoff_async(
        self,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> CrewOutput:
        """Start the crew execution asynchronously."""
        return await asyncio.to_thread(self.kickoff, inputs)
    
    def kickoff_for_each(
        self,
        inputs_list: List[Dict[str, Any]],
    ) -> List[CrewOutput]:
        """
        Execute the crew for each set of inputs.
        
        Args:
            inputs_list: List of input dictionaries
            
        Returns:
            List of CrewOutput for each execution
        """
        results = []
        for inputs in inputs_list:
            crew_copy = self.copy()
            result = crew_copy.kickoff(inputs)
            results.append(result)
            self._usage_metrics.add(crew_copy._usage_metrics)
        return results
    
    def _run_sequential(self) -> CrewOutput:
        """Execute tasks sequentially."""
        task_outputs = []
        
        for i, task in enumerate(self.tasks):
            logger.info(f"Executing task {i+1}/{len(self.tasks)}: {task.description[:50]}...")
            
            # Interpolate inputs
            if self._inputs:
                task.description = task.interpolate_inputs(self._inputs)
            
            try:
                output = task.execute()
                task_outputs.append(output)
                
                if self.task_callback:
                    self.task_callback(output)
                    
            except Exception as e:
                logger.error(f"Task failed: {e}")
                raise
        
        # Aggregate results
        final_output = self._aggregate_outputs(task_outputs)
        
        return CrewOutput(
            raw=final_output,
            tasks_output=task_outputs,
            token_usage=self._usage_metrics,
        )
    
    def _run_hierarchical(self) -> CrewOutput:
        """Execute tasks with manager coordination."""
        manager = self.manager_agent or self._create_manager_agent()
        task_outputs = []
        
        for task in self.tasks:
            # Manager decides which agent should handle the task
            assigned_agent = self._manager_assign_task(manager, task)
            
            if self._inputs:
                task.description = task.interpolate_inputs(self._inputs)
            
            # Override the task's agent with the assigned one
            original_agent = task.agent
            task.agent = assigned_agent
            
            try:
                output = task.execute()
                task_outputs.append(output)
            finally:
                task.agent = original_agent
        
        final_output = self._aggregate_outputs(task_outputs)
        
        return CrewOutput(
            raw=final_output,
            tasks_output=task_outputs,
            token_usage=self._usage_metrics,
        )
    
    def _run_parallel(self) -> CrewOutput:
        """Execute independent tasks in parallel."""
        task_outputs = []
        
        # Group tasks by dependencies
        independent_tasks = [t for t in self.tasks if not t.context]
        dependent_tasks = [t for t in self.tasks if t.context]
        
        # Execute independent tasks in parallel
        with ThreadPoolExecutor(max_workers=len(independent_tasks) or 1) as executor:
            futures = []
            for task in independent_tasks:
                if self._inputs:
                    task.description = task.interpolate_inputs(self._inputs)
                futures.append(executor.submit(task.execute))
            
            for future in futures:
                try:
                    output = future.result()
                    task_outputs.append(output)
                except Exception as e:
                    logger.error(f"Parallel task failed: {e}")
        
        # Execute dependent tasks sequentially
        for task in dependent_tasks:
            if self._inputs:
                task.description = task.interpolate_inputs(self._inputs)
            output = task.execute()
            task_outputs.append(output)
        
        final_output = self._aggregate_outputs(task_outputs)
        
        return CrewOutput(
            raw=final_output,
            tasks_output=task_outputs,
            token_usage=self._usage_metrics,
        )
    
    def _create_manager_agent(self) -> Agent:
        """Create a manager agent for hierarchical execution."""
        return Agent(
            role="Crew Manager",
            goal="Coordinate team members to complete all tasks efficiently",
            backstory="You are an experienced project manager skilled at delegating tasks to the right team members.",
            llm=self.manager_llm,
            verbose=self.verbose,
        )
    
    def _manager_assign_task(self, manager: Agent, task: Task) -> Agent:
        """Have the manager assign a task to an agent."""
        # In a full implementation, this would use the manager LLM
        # to decide which agent is best suited for the task.
        # For now, use task's assigned agent or first available.
        if task.agent:
            return task.agent
        
        # Simple heuristic: match agent roles to task descriptions
        for agent in self.agents:
            if agent.role.lower() in task.description.lower():
                return agent
        
        # Default to first agent
        return self.agents[0] if self.agents else None
    
    def _aggregate_outputs(self, task_outputs: List[TaskOutput]) -> str:
        """Aggregate task outputs into a final result."""
        if not task_outputs:
            return ""
        
        # Return the last task's output as the final result
        return task_outputs[-1].raw if task_outputs else ""
    
    def train(
        self,
        n_iterations: int,
        filename: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Train the crew for improved performance.
        
        Args:
            n_iterations: Number of training iterations
            filename: File to save training data
            inputs: Training inputs
        """
        logger.info(f"Training crew for {n_iterations} iterations")
        
        for i in range(n_iterations):
            logger.info(f"Training iteration {i+1}/{n_iterations}")
            
            # Enable human feedback for training
            for task in self.tasks:
                task.human_input = True
            
            # Run the crew
            self.kickoff(inputs)
        
        logger.info(f"Training complete. Data saved to {filename}")
    
    def test(
        self,
        n_iterations: int,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Test the crew performance.
        
        Args:
            n_iterations: Number of test iterations
            inputs: Test inputs
            
        Returns:
            Test results with metrics
        """
        results = []
        
        for i in range(n_iterations):
            try:
                output = self.kickoff(inputs)
                results.append({
                    "iteration": i + 1,
                    "success": True,
                    "output": output.raw[:200],
                })
            except Exception as e:
                results.append({
                    "iteration": i + 1,
                    "success": False,
                    "error": str(e),
                })
        
        return {
            "total_iterations": n_iterations,
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results,
        }
    
    def copy(self) -> "Crew":
        """Create a shallow copy of the crew."""
        return Crew(
            name=self.name,
            agents=[a.copy() for a in self.agents],
            tasks=[t.copy() for t in self.tasks],
            process=self.process,
            verbose=self.verbose,
            memory=self.memory,
            cache=self.cache,
            max_rpm=self.max_rpm,
            manager_llm=self.manager_llm,
            planning=self.planning,
        )
    
    def __repr__(self) -> str:
        return f"Crew(name='{self.name}', agents={len(self.agents)}, tasks={len(self.tasks)})"


# Pre-built SecOps crews
def create_security_assessment_crew(
    target: str,
    llm: Optional[Any] = None,
    verbose: bool = False,
) -> Crew:
    """
    Create a pre-configured security assessment crew.
    
    This crew includes:
    - Security Scanner Agent
    - Security Analyst Agent  
    - Remediation Agent
    
    With tasks for:
    - Vulnerability scanning
    - Finding analysis
    - Remediation proposals
    """
    from .agent import (
        create_security_scanner_agent,
        create_security_analyst_agent,
        create_remediation_agent,
    )
    from .task import create_security_scan_task, create_analysis_task, create_remediation_task
    
    # Create agents
    scanner = create_security_scanner_agent(llm=llm)
    analyst = create_security_analyst_agent(llm=llm)
    remediator = create_remediation_agent(llm=llm)
    
    # Create tasks
    scan_task = create_security_scan_task(target=target, agent=scanner)
    analysis_task = create_analysis_task(context_tasks=[scan_task], agent=analyst)
    remediation_task = create_remediation_task(context_tasks=[analysis_task], agent=remediator)
    
    return Crew(
        name=f"Security Assessment - {target}",
        agents=[scanner, analyst, remediator],
        tasks=[scan_task, analysis_task, remediation_task],
        process=Process.sequential,
        verbose=verbose,
        memory=True,
    )


def create_incident_response_crew(
    incident_id: str,
    llm: Optional[Any] = None,
    verbose: bool = False,
) -> Crew:
    """
    Create a pre-configured incident response crew.
    """
    from .agent import Agent
    from .task import Task
    
    # Incident response agents
    triage_agent = Agent(
        role="Incident Triage Specialist",
        goal="Quickly assess and classify security incidents",
        llm=llm,
    )
    
    investigator = Agent(
        role="Security Investigator",
        goal="Conduct thorough investigation of security incidents",
        llm=llm,
    )
    
    responder = Agent(
        role="Incident Responder",
        goal="Contain and remediate security incidents",
        llm=llm,
        allow_code_execution=True,
    )
    
    # Incident response tasks
    triage_task = Task(
        description=f"Triage incident {incident_id}. Assess severity, scope, and initial indicators of compromise.",
        expected_output="Incident classification with severity rating and initial findings",
        agent=triage_agent,
    )
    
    investigate_task = Task(
        description=f"Investigate incident {incident_id}. Determine root cause, attack vector, and full scope of impact.",
        expected_output="Detailed investigation report with timeline and affected assets",
        agent=investigator,
        context=[triage_task],
    )
    
    respond_task = Task(
        description=f"Respond to incident {incident_id}. Contain the threat and initiate remediation.",
        expected_output="Containment actions taken and remediation plan",
        agent=responder,
        context=[investigate_task],
        human_input=True,  # Require approval for response actions
    )
    
    return Crew(
        name=f"Incident Response - {incident_id}",
        agents=[triage_agent, investigator, responder],
        tasks=[triage_task, investigate_task, respond_task],
        process=Process.sequential,
        verbose=verbose,
    )
