"""
Process and Execution Mode Module

Defines the execution modes for crew operations: sequential and hierarchical.

Integrated from crewAI patterns.
"""

from enum import Enum


class Process(str, Enum):
    """
    Execution process modes for crews.
    
    Attributes:
        sequential: Tasks execute one after another in order
        hierarchical: A manager agent delegates and coordinates tasks
        parallel: Tasks execute concurrently where possible
        consensus: Multiple agents collaborate and reach consensus
    """
    
    sequential = "sequential"
    hierarchical = "hierarchical"
    parallel = "parallel"
    consensus = "consensus"
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "Process":
        """Create Process from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Unknown process type: {value}. Valid options: {[p.value for p in cls]}")
