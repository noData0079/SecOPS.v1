from __future__ import annotations

from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class IntegrationConfig(BaseModel):
    provider: str
    config: Dict[str, Any]


class IntegrationStatus(BaseModel):
    provider: str
    connected: bool
    last_sync: Optional[str]


class IntegrationTestResult(BaseModel):
    provider: str
    success: bool
    message: str


class ProviderListResponse(BaseModel):
    providers: List[Dict[str, Any]]


class IntegrationStatusResponse(BaseModel):
    provider: str
    connected: bool
    details: Optional[Dict[str, Any]] = None


class ConnectGitHubRequest(BaseModel):
    org_id: Optional[str] = None
    installation_id: str
    code: Optional[str] = None


class TriggerSyncRequest(BaseModel):
    org_id: Optional[str] = None
    providers: List[str]
    scope: str = "full"


class TriggerSyncResponse(BaseModel):
    job_ids: List[str]


class RegisterK8sClusterRequest(BaseModel):
    org_id: Optional[str] = None
    cluster_name: str
    kubeconfig: str


class TestIntegrationRequest(BaseModel):
    org_id: Optional[str] = None
    provider: str


class TestIntegrationResponse(BaseModel):
    success: bool
    message: str
