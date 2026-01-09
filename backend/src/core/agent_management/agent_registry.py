# backend/src/core/agent_management/agent_registry.py

"""Agent registry for managing agent lifecycle, health, and task assignment."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent status states."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    TERMINATED = "terminated"


class AgentCapability(str, Enum):
    """Agent capabilities."""
    SECURITY_SCAN = "security_scan"
    COMPLIANCE_CHECK = "compliance_check"
    CODE_ANALYSIS = "code_analysis"
    VULNERABILITY_SCAN = "vulnerability_scan"
    REMEDIATION = "remediation"
    MONITORING = "monitoring"
    INCIDENT_RESPONSE = "incident_response"
    DEPLOYMENT = "deployment"


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    agent_id: str
    name: str
    agent_type: str
    status: AgentStatus
    capabilities: List[AgentCapability]
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    current_task: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "current_task": self.current_task,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
        }
    
    def is_available(self) -> bool:
        """Check if agent is available for tasks."""
        return self.status == AgentStatus.IDLE
    
    def is_healthy(self, heartbeat_timeout: int = 60) -> bool:
        """Check if agent is healthy based on heartbeat."""
        if self.status in [AgentStatus.OFFLINE, AgentStatus.TERMINATED]:
            return False
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() < heartbeat_timeout


@dataclass
class TaskAssignment:
    """A task assigned to an agent."""
    task_id: str
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


class AgentRegistry:
    """
    Central registry for managing AI agents.
    
    Features:
    - Agent registration and deregistration
    - Health monitoring with heartbeats
    - Capability-based task routing
    - Load balancing across agents
    - Agent lifecycle management
    """
    
    def __init__(self, heartbeat_timeout: int = 60):
        """
        Initialize agent registry.
        
        Args:
            heartbeat_timeout: Seconds before agent is considered offline
        """
        self._agents: Dict[str, AgentInfo] = {}
        self._tasks: Dict[str, TaskAssignment] = {}
        self._heartbeat_timeout = heartbeat_timeout
        self._health_check_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        logger.info("AgentRegistry initialized")
    
    async def start(self):
        """Start background health monitoring."""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Agent health monitoring started")
    
    async def stop(self):
        """Stop background health monitoring."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Agent health monitoring stopped")
    
    def register_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentInfo:
        """
        Register a new agent.
        
        Args:
            name: Human-readable agent name
            agent_type: Type of agent (e.g., "scanner", "remediator")
            capabilities: List of agent capabilities
            metadata: Additional agent metadata
            
        Returns:
            AgentInfo for the registered agent
        """
        agent_id = str(uuid.uuid4())
        
        agent = AgentInfo(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            status=AgentStatus.INITIALIZING,
            capabilities=capabilities,
            metadata=metadata or {},
        )
        
        self._agents[agent_id] = agent
        logger.info(f"Agent registered: {name} ({agent_id})")
        
        self._emit_event("agent_registered", agent)
        return agent
    
    def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent.
        
        Args:
            agent_id: The agent ID to deregister
            
        Returns:
            True if successful
        """
        if agent_id not in self._agents:
            return False
        
        agent = self._agents[agent_id]
        agent.status = AgentStatus.TERMINATED
        
        del self._agents[agent_id]
        logger.info(f"Agent deregistered: {agent.name} ({agent_id})")
        
        self._emit_event("agent_deregistered", agent)
        return True
    
    def update_status(self, agent_id: str, status: AgentStatus, error_message: Optional[str] = None):
        """Update agent status."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")
        
        agent = self._agents[agent_id]
        old_status = agent.status
        agent.status = status
        agent.error_message = error_message
        
        if old_status != status:
            logger.info(f"Agent {agent.name} status: {old_status.value} -> {status.value}")
            self._emit_event("status_changed", agent, old_status=old_status)
    
    def heartbeat(self, agent_id: str) -> bool:
        """
        Update agent heartbeat.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            True if heartbeat accepted
        """
        if agent_id not in self._agents:
            return False
        
        agent = self._agents[agent_id]
        agent.last_heartbeat = datetime.utcnow()
        
        # If agent was offline, bring it back
        if agent.status == AgentStatus.OFFLINE:
            agent.status = AgentStatus.IDLE
            self._emit_event("agent_online", agent)
        
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def get_agents(
        self,
        status: Optional[AgentStatus] = None,
        capability: Optional[AgentCapability] = None,
        agent_type: Optional[str] = None,
    ) -> List[AgentInfo]:
        """
        Get agents with optional filtering.
        
        Args:
            status: Filter by status
            capability: Filter by capability
            agent_type: Filter by agent type
            
        Returns:
            List of matching agents
        """
        agents = list(self._agents.values())
        
        if status:
            agents = [a for a in agents if a.status == status]
        
        if capability:
            agents = [a for a in agents if capability in a.capabilities]
        
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        return agents
    
    def get_available_agent(
        self,
        capability: Optional[AgentCapability] = None,
    ) -> Optional[AgentInfo]:
        """
        Get an available agent, optionally with a specific capability.
        
        Uses round-robin load balancing among available agents.
        
        Args:
            capability: Required capability
            
        Returns:
            Available agent or None
        """
        agents = self.get_agents(status=AgentStatus.IDLE, capability=capability)
        
        if not agents:
            return None
        
        # Simple load balancing: prefer agents with fewer completed tasks
        agents.sort(key=lambda a: a.tasks_completed)
        return agents[0]
    
    async def assign_task(
        self,
        agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
    ) -> TaskAssignment:
        """
        Assign a task to an agent.
        
        Args:
            agent_id: The agent to assign to
            task_type: Type of task
            parameters: Task parameters
            
        Returns:
            TaskAssignment
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")
        
        agent = self._agents[agent_id]
        
        if not agent.is_available():
            raise ValueError(f"Agent {agent.name} is not available (status: {agent.status})")
        
        task_id = str(uuid.uuid4())
        task = TaskAssignment(
            task_id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            parameters=parameters,
        )
        
        self._tasks[task_id] = task
        agent.status = AgentStatus.BUSY
        agent.current_task = task_id
        
        logger.info(f"Task {task_id} assigned to agent {agent.name}")
        self._emit_event("task_assigned", task, agent=agent)
        
        return task
    
    async def complete_task(
        self,
        task_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
    ):
        """
        Mark a task as complete.
        
        Args:
            task_id: The task ID
            success: Whether task succeeded
            result: Task result data
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self._tasks[task_id]
        task.completed_at = datetime.utcnow()
        task.status = "completed" if success else "failed"
        task.result = result
        
        # Update agent
        if task.agent_id in self._agents:
            agent = self._agents[task.agent_id]
            agent.current_task = None
            agent.status = AgentStatus.IDLE
            
            if success:
                agent.tasks_completed += 1
            else:
                agent.tasks_failed += 1
        
        logger.info(f"Task {task_id} completed: {'success' if success else 'failed'}")
        self._emit_event("task_completed", task, success=success)
    
    async def _health_check_loop(self):
        """Background loop for health checking."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_timeout // 2)
                
                for agent in list(self._agents.values()):
                    if not agent.is_healthy(self._heartbeat_timeout):
                        if agent.status != AgentStatus.OFFLINE:
                            agent.status = AgentStatus.OFFLINE
                            logger.warning(f"Agent {agent.name} is offline (no heartbeat)")
                            self._emit_event("agent_offline", agent)
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, *args, **kwargs):
        """Emit an event to registered handlers."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        agents = list(self._agents.values())
        
        return {
            "total_agents": len(agents),
            "by_status": {
                status.value: sum(1 for a in agents if a.status == status)
                for status in AgentStatus
            },
            "total_tasks_completed": sum(a.tasks_completed for a in agents),
            "total_tasks_failed": sum(a.tasks_failed for a in agents),
            "active_tasks": len([t for t in self._tasks.values() if t.status == "pending"]),
        }
