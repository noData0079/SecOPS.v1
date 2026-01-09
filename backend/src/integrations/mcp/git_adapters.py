# backend/src/integrations/mcp/git_adapters.py

"""Git repository adapters (GitHub, GitLab, Bitbucket)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .mcp_adapter_base import MCPAdapter, MCPConnection, MCPCapability

logger = logging.getLogger(__name__)


class GitHubAdapter(MCPAdapter):
    """GitHub integration via REST API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize GitHub adapter."""
        super().__init__(config)
        self.token = config.get("github_token")
        self.org = config.get("github_org")
        self.base_url = "https://api.github.com"
        self.capabilities = [
            MCPCapability.READ,
            MCPCapability.WRITE,
            MCPCapability.EXECUTE,
        ]
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> MCPConnection:
        """Connect to GitHub API."""
        if not self.token:
            raise ValueError("GitHub token not configured")
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30.0,
        )
        
        # Verify connection
        response = await self.client.get(f"{self.base_url}/user")
        response.raise_for_status()
        user_data = response.json()
        
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="github",
            endpoint=self.base_url,
            authenticated=True,
            capabilities=self.capabilities,
            metadata={"user": user_data.get("login"), "org": self.org},
            connected_at=datetime.utcnow(),
        )
        
        logger.info(f"Connected to GitHub as {user_data.get('login')}")
        return self.connection
    
    async def disconnect(self) -> None:
        """Disconnect from GitHub."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
        logger.info("Disconnected from GitHub")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check GitHub API health."""
        if not self.client:
            return {"healthy": False, "error": "Not connected"}
        
        try:
            response = await self.client.get(f"{self.base_url}/rate_limit")
            data = response.json()
            return {
                "healthy": True,
                "rate_limit": data.get("rate", {}),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """
        Read GitHub resource.
        
        Resources:
        - repos/{owner}/{repo}
        - repos/{owner}/{repo}/pulls
        - repos/{owner}/{repo}/issues
        - repos/{owner}/{repo}/contents/{path}
        """
        if not self.client:
            raise RuntimeError("Not connected to GitHub")
        
        response = await self.client.get(f"{self.base_url}/{resource}", params=params)
        response.raise_for_status()
        return response.json()
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Write to GitHub resource.
        
        Resources:
        - repos/{owner}/{repo}/pulls (create PR)
        - repos/{owner}/{repo}/issues (create issue)
        - repos/{owner}/{repo}/contents/{path} (create/update file)
        """
        if not self.client:
            raise RuntimeError("Not connected to GitHub")
        
        response = await self.client.post(f"{self.base_url}/{resource}", json=data, params=params)
        response.raise_for_status()
        return response.json()
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute GitHub action.
        
        Actions:
        - create_pr: Create pull request
        - merge_pr: Merge pull request
        - create_issue: Create issue
        - trigger_workflow: Trigger GitHub Actions workflow
        """
        if action == "create_pr":
            return await self._create_pull_request(params or {})
        elif action == "merge_pr":
            return await self._merge_pull_request(params or {})
        elif action == "create_issue":
            return await self._create_issue(params or {})
        elif action == "trigger_workflow":
            return await self._trigger_workflow(params or {})
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _create_pull_request(self, params: Dict) -> Dict[str, Any]:
        """Create a pull request."""
        owner = params.get("owner") or self.org
        repo = params["repo"]
        title = params["title"]
        body = params.get("body", "")
        head = params["head"]  # source branch
        base = params.get("base", "main")  # target branch
        
        pr_data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        
        result = await self.write(f"repos/{owner}/{repo}/pulls", pr_data)
        logger.info(f"Created PR #{result.get('number')}: {title}")
        return result
    
    async def _merge_pull_request(self, params: Dict) -> Dict[str, Any]:
        """Merge a pull request."""
        owner = params.get("owner") or self.org
        repo = params["repo"]
        pr_number = params["pr_number"]
        
        if not self.client:
            raise RuntimeError("Not connected")
        
        response = await self.client.put(
            f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
        )
        response.raise_for_status()
        logger.info(f"Merged PR #{pr_number}")
        return response.json()
    
    async def _create_issue(self, params: Dict) -> Dict[str, Any]:
        """Create an issue."""
        owner = params.get("owner") or self.org
        repo = params["repo"]
        title = params["title"]
        body = params.get("body", "")
        labels = params.get("labels", [])
        
        issue_data = {
            "title": title,
            "body": body,
            "labels": labels,
        }
        
        result = await self.write(f"repos/{owner}/{repo}/issues", issue_data)
        logger.info(f"Created issue #{result.get('number')}: {title}")
        return result
    
    async def _trigger_workflow(self, params: Dict) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow."""
        owner = params.get("owner") or self.org
        repo = params["repo"]
        workflow_id = params["workflow_id"]
        ref = params.get("ref", "main")
        inputs = params.get("inputs", {})
        
        if not self.client:
            raise RuntimeError("Not connected")
        
        response = await self.client.post(
            f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            json={"ref": ref, "inputs": inputs},
        )
        response.raise_for_status()
        logger.info(f"Triggered workflow {workflow_id} on {ref}")
        return {"status": "triggered", "workflow_id": workflow_id}


class GitLabAdapter(MCPAdapter):
    """GitLab integration via REST API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize GitLab adapter."""
        super().__init__(config)
        self.token = config.get("gitlab_token")
        self.base_url = config.get("gitlab_url", "https://gitlab.com/api/v4")
        self.capabilities = [MCPCapability.READ, MCPCapability.WRITE, MCPCapability.EXECUTE]
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> MCPConnection:
        """Connect to GitLab API."""
        if not self.token:
            raise ValueError("GitLab token not configured")
        
        self.client = httpx.AsyncClient(
            headers={"PRIVATE-TOKEN": self.token},
            timeout=30.0,
        )
        
        # Verify connection
        response = await self.client.get(f"{self.base_url}/user")
        response.raise_for_status()
        user_data = response.json()
        
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="gitlab",
            endpoint=self.base_url,
            authenticated=True,
            capabilities=self.capabilities,
            metadata={"user": user_data.get("username")},
            connected_at=datetime.utcnow(),
        )
        
        logger.info(f"Connected to GitLab as {user_data.get('username')}")
        return self.connection
    
    async def disconnect(self) -> None:
        """Disconnect from GitLab."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check GitLab API health."""
        if not self.client:
            return {"healthy": False, "error": "Not connected"}
        
        try:
            response = await self.client.get(f"{self.base_url}/version")
            return {"healthy": True, "version": response.json(), "timestamp": datetime.utcnow().isoformat()}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """Read GitLab resource."""
        if not self.client:
            raise RuntimeError("Not connected to GitLab")
        
        response = await self.client.get(f"{self.base_url}/{resource}", params=params)
        response.raise_for_status()
        return response.json()
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Write to GitLab resource."""
        if not self.client:
            raise RuntimeError("Not connected to GitLab")
        
        response = await self.client.post(f"{self.base_url}/{resource}", json=data, params=params)
        response.raise_for_status()
        return response.json()
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GitLab action."""
        if action == "create_mr":
            return await self._create_merge_request(params or {})
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _create_merge_request(self, params: Dict) -> Dict[str, Any]:
        """Create a merge request."""
        project_id = params["project_id"]
        title = params["title"]
        source_branch = params["source_branch"]
        target_branch = params.get("target_branch", "main")
        
        mr_data = {
            "id": project_id,
            "title": title,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "description": params.get("description", ""),
        }
        
        result = await self.write(f"projects/{project_id}/merge_requests", mr_data)
        logger.info(f"Created MR !{result.get('iid')}: {title}")
        return result
