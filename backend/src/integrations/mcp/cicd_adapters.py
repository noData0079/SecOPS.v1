# backend/src/integrations/mcp/cicd_adapters.py

"""CI/CD platform adapters."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from .mcp_adapter_base import MCPAdapter, MCPConnection, MCPCapability

logger = logging.getLogger(__name__)


class GitHubActionsAdapter(MCPAdapter):
    """GitHub Actions integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.token = config.get("github_token")
        self.org = config.get("github_org")
        self.base_url = "https://api.github.com"
        self.capabilities = [MCPCapability.READ, MCPCapability.EXECUTE, MCPCapability.MONITOR]
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> MCPConnection:
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"},
            timeout=30.0
        )
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="github_actions",
            endpoint=self.base_url,
            authenticated=True,
            capabilities=self.capabilities,
            metadata={"org": self.org},
            connected_at=datetime.utcnow()
        )
        return self.connection
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{self.base_url}/rate_limit")
            return {"healthy": True, "rate_limit": response.json()}
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
        if action == "trigger_workflow":
            owner, repo = params["owner"], params["repo"]
            workflow_id, ref = params["workflow_id"], params.get("ref", "main")
            response = await self.client.post(
                f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
                json={"ref": ref, "inputs": params.get("inputs", {})}
            )
            response.raise_for_status()
            return {"status": "triggered"}
        raise ValueError(f"Unknown action: {action}")


class JenkinsAdapter(MCPAdapter):
    """Jenkins CI/CD integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("jenkins_url")
        self.username = config.get("jenkins_username")
        self.token = config.get("jenkins_token")
        self.capabilities = [MCPCapability.READ, MCPCapability.EXECUTE, MCPCapability.MONITOR]
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> MCPConnection:
        self.client = httpx.AsyncClient(auth=(self.username, self.token), timeout=30.0)
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="jenkins",
            endpoint=self.base_url,
            authenticated=True,
            capabilities=self.capabilities,
            metadata={"username": self.username},
            connected_at=datetime.utcnow()
        )
        return self.connection
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{self.base_url}/api/json")
            return {"healthy": response.status_code == 200}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        response = await self.client.get(f"{self.base_url}/{resource}/api/json")
        response.raise_for_status()
        return response.json()
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        raise NotImplementedError("Jenkins write not supported via REST")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        if action == "trigger_build":
            job_name = params["job_name"]
            response = await self.client.post(f"{self.base_url}/job/{job_name}/build")
            response.raise_for_status()
            return {"status": "triggered", "job": job_name}
        raise ValueError(f"Unknown action: {action}")
