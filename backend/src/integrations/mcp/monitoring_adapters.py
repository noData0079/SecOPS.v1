# backend/src/integrations/mcp/monitoring_adapters.py

"""Monitoring and observability platform adapters."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from .mcp_adapter_base import MCPAdapter, MCPConnection, MCPCapability

logger = logging.getLogger(__name__)


class PrometheusAdapter(MCPAdapter):
    """Prometheus metrics integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("prometheus_url", "http://localhost:9090")
        self.capabilities = [MCPCapability.READ, MCPCapability.MONITOR]
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> MCPConnection:
        self.client = httpx.AsyncClient(timeout=30.0)
        response = await self.client.get(f"{self.base_url}/api/v1/status/config")
        response.raise_for_status()
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="prometheus",
            endpoint=self.base_url,
            authenticated=False,
            capabilities=self.capabilities,
            metadata={},
            connected_at=datetime.utcnow()
        )
        return self.connection
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{self.base_url}/-/healthy")
            return {"healthy": response.status_code == 200}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """Query Prometheus metrics."""
        response = await self.client.get(f"{self.base_url}/api/v1/{resource}", params=params)
        response.raise_for_status()
        return response.json()
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        raise NotImplementedError("Prometheus is read-only via API")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        if action == "query":
            query = params["query"]
            result = await self.read("query", {"query": query})
            return result
        raise ValueError(f"Unknown action: {action}")


class DatadogAdapter(MCPAdapter):
    """Datadog monitoring integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("datadog_api_key")
        self.app_key = config.get("datadog_app_key")
        self.base_url = "https://api.datadoghq.com/api/v1"
        self.capabilities = [MCPCapability.READ, MCPCapability.MONITOR]
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> MCPConnection:
        self.client = httpx.AsyncClient(
            headers={"DD-API-KEY": self.api_key, "DD-APPLICATION-KEY": self.app_key},
            timeout=30.0
        )
        response = await self.client.get(f"{self.base_url}/validate")
        response.raise_for_status()
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="datadog",
            endpoint=self.base_url,
            authenticated=True,
            capabilities=self.capabilities,
            metadata={},
            connected_at=datetime.utcnow()
        )
        return self.connection
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{self.base_url}/validate")
            return {"healthy": response.status_code == 200}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        response = await self.client.get(f"{self.base_url}/{resource}", params=params)
        response.raise_for_status()
        return response.json()
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        response = await self.client.post(f"{self.base_url}/{resource}", json=data)
        response.raise_for_status()
        return response.json()
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        if action == "query_metrics":
            return await self.read("query", params)
        raise ValueError(f"Unknown action: {action}")
