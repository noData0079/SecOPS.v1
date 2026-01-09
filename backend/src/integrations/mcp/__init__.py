# backend/src/integrations/mcp/__init__.py

"""
Model Context Protocol (MCP) Integration Layer.
Connects the platform to external tools, SaaS platforms, and infrastructure.
"""

from .mcp_adapter_base import MCPAdapter, MCPConnection, MCPCapability
from .git_adapters import GitHubAdapter, GitLabAdapter
from .cicd_adapters import GitHubActionsAdapter, JenkinsAdapter
from .cloud_adapters import AWSAdapter, GCPAdapter, AzureAdapter
from .monitoring_adapters import PrometheusAdapter, DatadogAdapter
from .security_adapters import ProwlerAdapter, GarakAdapter

__all__ = [
    "MCPAdapter",
    "MCPConnection",
    "MCPCapability",
    "GitHubAdapter",
    "GitLabAdapter",
    "GitHubActionsAdapter",
    "JenkinsAdapter",
    "AWSAdapter",
    "GCPAdapter",
    "AzureAdapter",
    "PrometheusAdapter",
    "DatadogAdapter",
    "ProwlerAdapter",
    "GarakAdapter",
]
