# backend/src/integrations/storage/supabase_client.py

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import httpx

from utils.config import Settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


class SupabaseConfigError(RuntimeError):
    """Raised when Supabase is not properly configured."""


class SupabaseClient:
    """
    Lightweight async wrapper around Supabase REST + Storage.

    It does NOT try to be a full ORM – just the pieces we need:
      - table operations via /rest/v1
      - file upload/download via /storage/v1

    Configuration (via Settings or env):

      SUPABASE_URL:          e.g. https://xyz.supabase.co
      SUPABASE_ANON_KEY:     anon or service role key
      SUPABASE_SERVICE_ROLE: (optional) service role key (overrides anon)

    If URL or key is missing, the client is considered "disabled" and all
    operations will log a warning and return safe defaults instead of raising.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        url = (
            getattr(settings, "SUPABASE_URL", None)
            or os.getenv("SUPABASE_URL")
        )
        # Prefer service role if provided
        key = (
            getattr(settings, "SUPABASE_SERVICE_ROLE", None)
            or os.getenv("SUPABASE_SERVICE_ROLE")
            or getattr(settings, "SUPABASE_ANON_KEY", None)
            or os.getenv("SUPABASE_ANON_KEY")
        )

        self._base_url: Optional[str] = url.rstrip("/") if url else None
        self._api_key: Optional[str] = key

        if not self._base_url or not self._api_key:
            logger.warning(
                "SupabaseClient initialized without full configuration "
                "(SUPABASE_URL or key missing). Supabase operations are disabled."
            )
            self._enabled = False
        else:
            self._enabled = True

        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Internal client
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._enabled:
            raise SupabaseConfigError("Supabase is not configured (URL or key missing)")

        if self._client is None:
            headers = {
                "apikey": self._api_key or "",
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # REST helpers (PostgREST /rest/v1)
    # ------------------------------------------------------------------

    async def insert(
        self,
        table: str,
        rows: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: str = "representation",
    ) -> List[Dict[str, Any]]:
        """
        Insert one or more rows into a table.

        `rows` may be a single dict or list of dicts.
        Returns a list of inserted rows (if returning != 'minimal'),
        or an empty list when disabled or in minimal mode.
        """
        if not self._enabled:
            logger.debug("SupabaseClient.insert called but Supabase is disabled")
            return []

        client = await self._get_client()

        if not isinstance(rows, list):
            payload = [rows]
        else:
            payload = rows

        headers = {
            "Prefer": f"return={returning}",
        }

        resp = await client.post(f"/rest/v1/{table}", headers=headers, content=json.dumps(payload))

        if resp.status_code >= 400:
            logger.warning(
                "Supabase insert failed for table=%s status=%s body=%s",
                table,
                resp.status_code,
                resp.text[:500],
            )
            return []

        if returning == "minimal" or resp.status_code == 204:
            return []

        try:
            data = resp.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            return []
        except ValueError:
            logger.error("SupabaseClient.insert: response is not valid JSON")
            return []

    async def upsert(
        self,
        table: str,
        rows: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        on_conflict: Optional[str] = None,
        returning: str = "representation",
    ) -> List[Dict[str, Any]]:
        """
        Upsert (insert or update) rows into a table based on a conflict key.

        Equivalent to:
          POST /rest/v1/{table}?on_conflict=...
          Prefer: resolution=merge-duplicates
        """
        if not self._enabled:
            logger.debug("SupabaseClient.upsert called but Supabase is disabled")
            return []

        client = await self._get_client()

        if not isinstance(rows, list):
            payload = [rows]
        else:
            payload = rows

        params: Dict[str, Any] = {}
        if on_conflict:
            params["on_conflict"] = on_conflict

        headers = {
            "Prefer": f"return={returning},resolution=merge-duplicates",
        }

        resp = await client.post(
            f"/rest/v1/{table}",
            params=params or None,
            headers=headers,
            content=json.dumps(payload),
        )

        if resp.status_code >= 400:
            logger.warning(
                "Supabase upsert failed for table=%s status=%s body=%s",
                table,
                resp.status_code,
                resp.text[:500],
            )
            return []

        if returning == "minimal" or resp.status_code == 204:
            return []

        try:
            data = resp.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            return []
        except ValueError:
            logger.error("SupabaseClient.upsert: response is not valid JSON")
            return []

    async def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Simple SELECT wrapper.

        `filters` is a dict of column -> value, which we map to
        PostgREST `eq` filters: e.g. `column=eq.value`.

        For more complex queries, call Supabase directly or add a specialized
        method instead of overloading this.
        """
        if not self._enabled:
            logger.debug("SupabaseClient.select called but Supabase is disabled")
            return []

        client = await self._get_client()

        params: Dict[str, Any] = {
            "select": columns,
        }

        if filters:
            for col, value in filters.items():
                params[col] = f"eq.{value}"

        if limit is not None:
            params["limit"] = str(limit)

        resp = await client.get(f"/rest/v1/{table}", params=params)

        if resp.status_code >= 400:
            logger.warning(
                "Supabase select failed for table=%s status=%s body=%s",
                table,
                resp.status_code,
                resp.text[:500],
            )
            return []

        try:
            data = resp.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            return []
        except ValueError:
            logger.error("SupabaseClient.select: response is not valid JSON")
            return []

    async def delete(
        self,
        table: str,
        *,
        filters: Dict[str, Any],
    ) -> int:
        """
        Delete rows matching filters.

        Returns number of rows deleted if available, or 0.

        `filters` is mapped to eq filters like select().
        """
        if not self._enabled:
            logger.debug("SupabaseClient.delete called but Supabase is disabled")
            return 0

        client = await self._get_client()

        params: Dict[str, Any] = {}
        for col, value in filters.items():
            params[col] = f"eq.{value}"

        headers = {
            "Prefer": "return=representation",
        }

        resp = await client.delete(f"/rest/v1/{table}", params=params, headers=headers)

        if resp.status_code >= 400:
            logger.warning(
                "Supabase delete failed for table=%s status=%s body=%s",
                table,
                resp.status_code,
                resp.text[:500],
            )
            return 0

        try:
            data = resp.json()
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                return 1
            return 0
        except ValueError:
            # No body
            return 0

    # ------------------------------------------------------------------
    # Storage helpers (/storage/v1)
    # ------------------------------------------------------------------

    async def upload_file(
        self,
        *,
        bucket: str,
        path: str,
        content: bytes,
        content_type: Optional[str] = None,
        upsert: bool = True,
    ) -> bool:
        """
        Upload a file to Supabase Storage.

        Path is relative to the bucket root.

        Returns True on success, False on failure or when disabled.
        """
        if not self._enabled:
            logger.debug("SupabaseClient.upload_file called but Supabase is disabled")
            return False

        client = await self._get_client()

        # We need raw request for storage; override headers appropriately.
        headers = {
            "apikey": self._api_key or "",
            "Authorization": f"Bearer {self._api_key}",
        }
        if content_type:
            headers["Content-Type"] = content_type

        params = {
            "bucket": bucket,
            "path": path,
            "upsert": "true" if upsert else "false",
        }

        resp = await client.post(
            "/storage/v1/object",
            params=params,
            content=content,
            headers=headers,
        )

        if resp.status_code >= 400:
            logger.warning(
                "Supabase upload_file failed for bucket=%s path=%s status=%s body=%s",
                bucket,
                path,
                resp.status_code,
                resp.text[:500],
            )
            return False

        return True

    async def download_file(
        self,
        *,
        bucket: str,
        path: str,
    ) -> Optional[bytes]:
        """
        Download a file from Supabase Storage.

        Returns file bytes or None on failure / missing / disabled.
        """
        if not self._enabled:
            logger.debug("SupabaseClient.download_file called but Supabase is disabled")
            return None

        client = await self._get_client()

        headers = {
            "apikey": self._api_key or "",
            "Authorization": f"Bearer {self._api_key}",
        }

        url = f"/storage/v1/object/{bucket}/{path.lstrip('/')}"
        resp = await client.get(url, headers=headers)

        if resp.status_code >= 400:
            logger.warning(
                "Supabase download_file failed for bucket=%s path=%s status=%s",
                bucket,
                path,
                resp.status_code,
            )
            return None

        return resp.content


# ----------------------------------------------------------------------
# Factory helper
# ----------------------------------------------------------------------


def get_supabase_client(settings: Settings) -> SupabaseClient:
    """
    Factory helper for dependency injection.

    Typical usage:

        from integrations.storage.supabase_client import get_supabase_client
        from utils.config import settings

        sb = get_supabase_client(settings)
        rows = await sb.select("issues", filters={"org_id": "org-123"})
    """
    return SupabaseClient(settings=settings)
