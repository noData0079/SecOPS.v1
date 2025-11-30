# backend/src/api/routes/integrations.py

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.schemas.integrations import (
    ProviderListResponse,
    IntegrationStatusResponse,
    ConnectGitHubRequest,
    TriggerSyncRequest,
    TriggerSyncResponse,
    RegisterK8sClusterRequest,
    TestIntegrationRequest,
    TestIntegrationResponse,
)
from api.deps import get_current_user, get_integrations_service
from integrations.service import IntegrationsService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/integrations",
    tags=["Integrations"],
)


# --- Helper ------------------------------------------------------------------


def _resolve_org_id(
    current_user: dict[str, Any],
    explicit_org_id: Optional[str] = None,
) -> str:
    """
    Decide which org_id to use for integration operations.

    - If explicit_org_id is provided (admin use-cases), prefer that.
    - Otherwise, fall back to current_user["org_id"].
    """
    if explicit_org_id:
        return explicit_org_id

    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required.",
        )
    return str(org_id)


# --- Providers listing -------------------------------------------------------


@router.get(
    "/providers",
    response_model=ProviderListResponse,
    summary="List supported integration providers",
    response_description="All providers that this platform can integrate with.",
)
async def list_providers(
    integrations_service: IntegrationsService = Depends(get_integrations_service),
) -> ProviderListResponse:
    """
    Return the list of supported providers and their capabilities.

    This is mostly static, but comes from the IntegrationsService so that we
    can evolve supported providers without changing the router.
    """
    try:
        providers = integrations_service.list_providers()
        return ProviderListResponse(providers=providers)
    except Exception:
        logger.exception("Failed to list integration providers")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list integration providers.",
        )


# --- Status ------------------------------------------------------------------


@router.get(
    "/status/{provider}",
    response_model=IntegrationStatusResponse,
    summary="Get integration status for a provider",
    response_description="Connection / sync status for a given provider.",
)
async def get_integration_status(
    provider: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    integrations_service: IntegrationsService = Depends(get_integrations_service),
) -> IntegrationStatusResponse:
    """
    Return connection and last-sync status for the given provider
    for the current org.
    """
    org_id = _resolve_org_id(current_user)

    try:
        status_info = await integrations_service.get_status(
            org_id=org_id,
            provider=provider,
        )
        return IntegrationStatusResponse(**status_info)
    except ValueError as exc:
        logger.info("Unknown provider '%s': %s", provider, exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("Failed to get integration status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get integration status.",
        )


# --- GitHub connect ----------------------------------------------------------


@router.post(
    "/github/connect",
    response_model=IntegrationStatusResponse,
    summary="Connect GitHub for current org",
    response_description="Stores credentials / installation and returns status.",
)
async def connect_github(
    payload: ConnectGitHubRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    integrations_service: IntegrationsService = Depends(get_integrations_service),
) -> IntegrationStatusResponse:
    """
    Connect GitHub for the current org.

    The IntegrationsService is responsible for:
    - validating tokens / installation ids
    - storing them securely (e.g., in a secrets manager or encrypted storage)
    - initiating initial sync if configured
    """
    org_id = _resolve_org_id(current_user, explicit_org_id=payload.org_id)

    try:
        status_info = await integrations_service.connect_github(
            org_id=org_id,
            data=payload,
        )
        return IntegrationStatusResponse(**status_info)
    except ValueError as exc:
        logger.info("GitHub connect failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("Unexpected error during GitHub connect")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect GitHub integration.",
        )


# --- K8s register cluster ----------------------------------------------------


@router.post(
    "/k8s/register",
    response_model=IntegrationStatusResponse,
    summary="Register a Kubernetes cluster",
    response_description="Registers a cluster and returns integration status.",
)
async def register_k8s_cluster(
    payload: RegisterK8sClusterRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    integrations_service: IntegrationsService = Depends(get_integrations_service),
) -> IntegrationStatusResponse:
    """
    Register a Kubernetes cluster for the current org.

    The IntegrationsService handles:
    - validating kubeconfig or connection params
    - securely storing credentials / config
    - scheduling initial discovery job
    """
    org_id = _resolve_org_id(current_user, explicit_org_id=payload.org_id)

    try:
        status_info = await integrations_service.register_k8s_cluster(
            org_id=org_id,
            data=payload,
        )
        return IntegrationStatusResponse(**status_info)
    except ValueError as exc:
        logger.info("K8s registration failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("Unexpected error during K8s registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register Kubernetes cluster.",
        )


# --- Manual sync trigger -----------------------------------------------------


@router.post(
    "/sync",
    response_model=TriggerSyncResponse,
    summary="Trigger a manual sync for one or more providers",
    response_description="Schedules sync jobs and returns job identifiers.",
)
async def trigger_sync(
    payload: TriggerSyncRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    integrations_service: IntegrationsService = Depends(get_integrations_service),
) -> TriggerSyncResponse:
    """
    Trigger synchronization for the given providers.

    Example use-cases:
    - Pull latest GitHub security alerts
    - Refresh repos metadata
    - Re-scan K8s resources
    """
    org_id = _resolve_org_id(current_user, explicit_org_id=payload.org_id)

    try:
        result = await integrations_service.trigger_sync(
            org_id=org_id,
            providers=payload.providers,
            scope=payload.scope,
            triggered_by=current_user.get("id"),
        )
        return TriggerSyncResponse(**result)
    except ValueError as exc:
        logger.info("Trigger sync failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("Unexpected error during sync trigger")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger sync.",
        )


# --- Test integration --------------------------------------------------------


@router.post(
    "/test",
    response_model=TestIntegrationResponse,
    summary="Test a specific integration connection",
    response_description="Performs a lightweight connectivity check.",
)
async def test_integration(
    payload: TestIntegrationRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    integrations_service: IntegrationsService = Depends(get_integrations_service),
) -> TestIntegrationResponse:
    """
    Perform a lightweight connectivity/configuration check
    for a given provider (e.g. GitHub, K8s, CI).

    The IntegrationsService implements provider-specific tests.
    """
    org_id = _resolve_org_id(current_user, explicit_org_id=payload.org_id)

    try:
        result = await integrations_service.test_integration(
            org_id=org_id,
            provider=payload.provider,
        )
        return TestIntegrationResponse(**result)
    except ValueError as exc:
        logger.info("Test integration failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("Unexpected error during integration test")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test integration.",
        )
