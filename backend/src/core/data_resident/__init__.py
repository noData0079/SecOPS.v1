"""
Data-Resident Architecture Module

All customer data stays in customer infrastructure.
Only sanitized metadata goes to external LLMs.
"""

from .orchestrator import (
    DataResidentOrchestrator,
    Finding,
    FixProposal,
    WorkflowStage,
    run_data_resident_workflow,
)

__all__ = [
    "DataResidentOrchestrator",
    "Finding",
    "FixProposal",
    "WorkflowStage",
    "run_data_resident_workflow",
]

__version__ = "1.0.0"
