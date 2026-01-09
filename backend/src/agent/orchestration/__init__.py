"""
SecOps-AI Agent Orchestration Module

Integrated from crewAI patterns for multi-agent orchestration.
This module provides the core infrastructure for creating and managing
crews of AI agents that can work together on complex security operations.

Key Components:
- Crew: Multi-agent team orchestration
- Agent: Individual agent definition with roles and goals
- Task: Task definition and execution
- Process: Sequential and hierarchical execution modes
- Flow: Workflow orchestration

Source: crewAI (https://github.com/crewAIInc/crewAI)
"""

from .crew import Crew, CrewOutput
from .agent import Agent, AgentConfig
from .task import Task, TaskOutput, ConditionalTask
from .process import Process
from .flow import Flow, FlowState

__all__ = [
    "Crew",
    "CrewOutput", 
    "Agent",
    "AgentConfig",
    "Task",
    "TaskOutput",
    "ConditionalTask",
    "Process",
    "Flow",
    "FlowState",
]

__version__ = "1.0.0"
