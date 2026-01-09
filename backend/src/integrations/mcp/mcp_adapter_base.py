# backend/src/integrations/mcp/mcp_adapter_base.py

"""Base MCP adapter for all external integrations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPCapability(str, Enum):
    """Capabilities that an MCP adapter can provide."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    MONITOR = "monitor"
    CONFIGURE = "configure"


@dataclass
class MCPConnection:
    """Connection details for an MCP adapter."""
    adapter_id: str
    adapter_type: str
    endpoint: str
    authenticated: bool
    capabilities: List[MCPCapability]
    metadata: Dict[str, Any]
    connected_at: datetime
    last_activity: Optional[datetime] = None


class MCPAdapter(ABC):
    """
    Base adapter for Model Context Protocol integrations.
    
    All external tool integrations inherit from this to provide
    a unified interface for the platform.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize adapter with configuration."""
        self.config = config
        self.adapter_id = config.get("adapter_id", self.__class__.__name__)
        self.connected = False
        self.connection: Optional[MCPConnection] = None
        self.capabilities: List[MCPCapability] = []
        
    @abstractmethod
    async def connect(self) -> MCPConnection:
        """
        Establish connection to the external system.
        
        Returns:
            MCPConnection with connection details
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the external system."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the connection.
        
        Returns:
            Dict with health status
        """
        pass
    
    @abstractmethod
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """
        Read data from the external system.
        
        Args:
            resource: Resource identifier
            params: Optional parameters
            
        Returns:
            Data from the resource
        """
        pass
    
    @abstractmethod
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Write data to the external system.
        
        Args:
            resource: Resource identifier
            data: Data to write
            params: Optional parameters
            
        Returns:
            Result of the write operation
        """
        pass
    
    @abstractmethod
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute an action on the external system.
        
        Args:
            action: Action to execute
            params: Action parameters
            
        Returns:
            Result of the execution
        """
        pass
    
    def get_capabilities(self) -> List[MCPCapability]:
        """Get supported capabilities of this adapter."""
        return self.capabilities
    
    def supports_capability(self, capability: MCPCapability) -> bool:
        """Check if adapter supports a capability."""
        return capability in self.capabilities
    
    def get_connection_info(self) -> Optional[MCPConnection]:
        """Get current connection information."""
        return self.connection
