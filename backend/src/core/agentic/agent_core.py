# backend/src/core/agentic/agent_core.py

"""
Core agent architecture implementing the autonomous agent pattern.

Agents combine perception, reasoning, memory, and action systems into
a cohesive decision-making entity.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.llm import LLMRouter, TaskType
from .reasoning_loop import ReasoningLoop
from .memory_manager import MemoryManager
from.action_executor import ActionExecutor, Action
from .approval_gates import ApprovalGate

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """Agent lifecycle states."""
    
    INITIALIZING = "initializing"
    IDLE = "idle"
    PERCEIVING = "perceiving"  # Collecting signals
    REASONING = "reasoning"  # Planning and decision making
    AWAITING_APPROVAL = "awaiting_approval"  # Waiting for human approval
    EXECUTING = "executing"  # Performing actions
    REFLECTING = "reflecting"  # Analyzing results
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    max_iterations: int = 10
    require_approval_for_high_risk: bool = True
    auto_reflect: bool = True
    memory_ttl_seconds: int = 3600  # 1 hour default
    reasoning_temperature: float = 0.7


class Agent:
    """
    Autonomous agent with perception, reasoning, memory, and action capabilities.
    
    The agent follows a continuous loop:
    1. Perceive: Collect signals from the environment
    2. Reason: Plan actions using LLM-powered reasoning
    3. Approve: Get human approval for high-risk actions (optional)
    4. Act: Execute approved actions
    5. Reflect: Analyze results and update beliefs
    6. Repeat
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_router: Optional[LLMRouter] = None,
        memory_manager: Optional[MemoryManager] = None,
        action_executor: Optional[ActionExecutor] = None,
        approval_gate: Optional[ApprovalGate] = None,
    ):
        """
        Initialize agent.
        
        Args:
            config: Agent configuration
            llm_router: LLM router for reasoning (auto-created if None)
            memory_manager: Memory system (auto-created if None)
            action_executor: Action executor (auto-created if None)
            approval_gate: Approval gate (auto-created if None)
        """
        self.agent_id = str(uuid.uuid4())
        self.config = config
        
        # Core components
        self.llm_router = llm_router or LLMRouter()
        self.memory = memory_manager or MemoryManager(agent_id=self.agent_id)
        self.executor = action_executor or ActionExecutor()
        self.approval_gate = approval_gate or ApprovalGate()
        
        # Reasoning loop
        self.reasoning_loop = ReasoningLoop(
            llm_router=self.llm_router,
            memory_manager=self.memory
        )
        
        # State management
        self.state = AgentState.INITIALIZING
        self.current_goal: Optional[str] = None
        self.iteration_count = 0
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        
        # Execution history
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"Agent initialized: {self.config.name} ({self.agent_id})")
    
    def set_goal(self, goal: str) -> None:
        """Set the agent's current goal."""
        self.current_goal = goal
        self.memory.store_goal(goal)
        logger.info(f"Agent {self.config.name} goal set: {goal}")
    
    async def perceive(self, signals: Dict[str, Any]) -> None:
        """
        Perceive signals from the environment.
        
        Args:
            signals: Dict of signal type -> signal data
        """
        self.state = AgentState.PERCEIVING
        self.last_active = datetime.utcnow()
        
        # Store signals in memory
        await self.memory.store_perception(signals)
       
        logger.debug(f"Agent perceived {len(signals)} signals")
    
    async def reason(self) -> List[Action]:
        """
        Reason about the current situation and plan actions.
        
        Uses the reasoning loop to:
        - Understand the current state
        - Plan actions to achieve the goal
        - Evaluate potential outcomes
        
        Returns:
            List of planned actions
        """
        self.state = AgentState.REASONING
        self.last_active = datetime.utcnow()
        
        if not self.current_goal:
            logger.warning("No goal set for agent, cannot reason")
            return []
        
        # Get context from memory
        context = await self.memory.get_reasoning_context()
        
        # Generate plan using reasoning loop
        plan = await self.reasoning_loop.generate_plan(
            goal=self.current_goal,
            context=context,
            temperature=self.config.reasoning_temperature,
        )
        
        # Convert plan steps to actions
        actions = []
        for step in plan.steps:
            action = Action(
                action_type=step.action_type,
                description=step.description,
                parameters=step.parameters,
                risk_level=step.risk_level,
            )
            actions.append(action)
        
        # Store plan in memory
        await self.memory.store_plan(plan)
        
        logger.info(f"Agent planned {len(actions)} actions")
        return actions
    
    async def execute_actions(self, actions: List[Action]) -> List[Dict[str, Any]]:
        """
        Execute actions, with approval gates for high-risk actions.
        
        Args:
            actions: List of actions to execute
            
        Returns:
            List of execution results
        """
        results = []
        
        for i, action in enumerate(actions):
            # Check if approval is needed
            if action.risk_level == "high" and self.config.require_approval_for_high_risk:
                self.state = AgentState.AWAITING_APPROVAL
                
                # Request approval
                approved = await self.approval_gate.request_approval(
                    agent_id=self.agent_id,
                    action=action,
                    context={
                        "goal": self.current_goal,
                        "action_index": i,
                        "total_actions": len(actions),
                    }
                )
                
                if not approved:
                    logger.warning(f"Action {i+1} rejected by approval gate")
                    results.append({
                        "action": action.to_dict(),
                        "status": "rejected",
                        "message": "Rejected by approval gate",
                    })
                    continue
            
            # Execute action
            self.state = AgentState.EXECUTING
            self.last_active = datetime.utcnow()
            
            try:
                result = await self.executor.execute(action)
                results.append({
                    "action": action.to_dict(),
                    "status": "success",
                    "result": result.to_dict(),
                })
                
                # Store result in memory
                await self.memory.store_action_result(action, result)
                
            except Exception as e:
                logger.error(f"Action execution failed: {e}")
                results.append({
                    "action": action.to_dict(),
                    "status": "error",
                    "error": str(e),
                })
        
        return results
    
    async def reflect(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reflect on action results and update beliefs.
        
        Args:
            results: List of execution results
            
        Returns:
            Reflection summary
        """
        self.state = AgentState.REFLECTING
        self.last_active = datetime.utcnow()
        
        # Use LLM to analyze results
        reflection_prompt = f"""
        Goal: {self.current_goal}
        
        Actions taken and results:
        {results}
        
        Analyze:
        1. Were the actions effective in achieving the goal?
        2. What worked well?
        3. What could be improved?
        4. Should we continue, adjust strategy, or stop?
        """
        
        response = await self.llm_router.generate(
            prompt=reflection_prompt,
            task_type=TaskType.REASONING,
        )
        
        reflection = {
            "timestamp": datetime.utcnow().isoformat(),
            "results_analyzed": len(results),
            "analysis": response.content,
            "goal_achieved": "achieved" in response.content.lower(),  # Simple heuristic
        }
        
        # Store reflection
        await self.memory.store_reflection(reflection)
        
        return reflection
    
    async def run_iteration(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run one iteration of the agent loop.
        
        Args:
            signals: Environment signals to process
            
        Returns:
            Iteration summary
        """
        iteration_start = datetime.utcnow()
        self.iteration_count += 1
        
        logger.info(f"Agent iteration {self.iteration_count} starting")
        
        # Perceive
        await self.perceive(signals)
        
        # Reason
        actions = await self.reason()
        
        # Execute
        results = await self.execute_actions(actions)
        
        # Reflect
        reflection = await self.reflect(results)
        
        # Build summary
        iteration_summary = {
            "iteration": self.iteration_count,
            "duration_ms": (datetime.utcnow() - iteration_start).total_seconds() * 1000,
            "signals_perceived": len(signals),
            "actions_planned": len(actions),
            "actions_executed": sum(1 for r in results if r["status"] == "success"),
            "goal_achieved": reflection.get("goal_achieved", False),
            "state": self.state.value,
        }
        
        self.execution_history.append(iteration_summary)
        
        # Check if we should continue
        if reflection.get("goal_achieved") or self.iteration_count >= self.config.max_iterations:
            self.state = AgentState.IDLE
            logger.info(f"Agent completing after {self.iteration_count} iterations")
        
        return iteration_summary
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "state": self.state.value,
            "current_goal": self.current_goal,
            "iterations": self.iteration_count,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "capabilities": self.config.capabilities,
            "execution_history": self.execution_history[-10:],  # Last 10
        }
