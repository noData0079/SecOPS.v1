# backend/src/integrations/security/scanners.py

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

import anyio

from utils.config import Settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------


@dataclass
class SecurityFinding:
    """
    Unified representation of a security scanner finding.

    Fields:
      - scanner: "trivy" | "snyk" | ...
      - target: image / path / project being scanned
      - type: "container" | "filesystem" | "dependency" | ...
      - severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | None
      - id: vulnerability identifier (e.g. CVE, GHSA)
      - title: short title or description
      - description: more detailed description if available
      - package: affected package or component (if applicable)
      - version: affected version
      - fixed_version: version where the issue is fixed (if known)
      - references: list of URLs with more info
      - metadata: provider-specific extras (full JSON, raw fields, etc.)
    """

    scanner: str
    target: str
    type: str

    severity: Optional[str] = None
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    package: Optional[str] = None
    version: Optional[str] = None
    fixed_version: Optional[str] = None

    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Trivy scanner (CLI-based)
# ---------------------------------------------------------------------------


class TrivyScanner:
    """
    Lightweight wrapper around the Trivy CLI for container/filesystem scanning.

    This scanner is **optional**:
      - If TRIVY_ENABLED = false (or not set), it will NOT run.
      - If the 'trivy' binary is missing, it logs and returns [].

    It is designed so that checks can safely call it without worrying about
    environment details.

    Settings used (via Settings or env vars):
      - TRIVY_ENABLED: bool (default: False)
      - TRIVY_PATH: path to the trivy executable (default: "trivy")
      - TRIVY_ADDITIONAL_ARGS: extra CLI args string (optional)
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled: bool = bool(
            getattr(settings, "TRIVY_ENABLED", None)
            or os.getenv("TRIVY_ENABLED", "false").lower() == "true"
        )
        self.trivy_path: str = (
            getattr(settings, "TRIVY_PATH", None)
            or os.getenv("TRIVY_PATH")
            or "trivy"
        )
        self.additional_args: str = (
            getattr(settings, "TRIVY_ADDITIONAL_ARGS", None)
            or os.getenv("TRIVY_ADDITIONAL_ARGS")
            or ""
        )

        if not self.enabled:
            logger.info("TrivyScanner initialized but disabled (TRIVY_ENABLED=false)")

    # ---------------------------- public API ----------------------------

    async def scan_image(self, image: str) -> List[SecurityFinding]:
        """
        Scan a container image using Trivy.

        Returns:
          List[SecurityFinding]
        """
        if not self.enabled:
            logger.debug("TrivyScanner.scan_image called but scanner is disabled")
            return []

        cmd = f"{shlex.quote(self.trivy_path)} image --format json {self.additional_args} {shlex.quote(image)}"
        return await self._run_trivy(cmd=cmd, target=image, target_type="container")

    async def scan_filesystem(self, path: str) -> List[SecurityFinding]:
        """
        Scan a filesystem path (e.g. repo directory) using Trivy.

        Returns:
          List[SecurityFinding]
        """
        if not self.enabled:
            logger.debug("TrivyScanner.scan_filesystem called but scanner is disabled")
            return []

        cmd = f"{shlex.quote(self.trivy_path)} fs --format json {self.additional_args} {shlex.quote(path)}"
        return await self._run_trivy(cmd=cmd, target=path, target_type="filesystem")

    # ---------------------------- internals -----------------------------

    async def _run_trivy(
        self,
        *,
        cmd: str,
        target: str,
        target_type: str,
    ) -> List[SecurityFinding]:
        """
        Run Trivy via subprocess and parse its JSON output into findings.

        On any failure (missing binary, non-zero exit, invalid JSON),
        this method logs the error and returns an empty list.
        """
        logger.info("TrivyScanner: running '%s' for target=%s", cmd, target)

        async def _exec() -> subprocess.CompletedProcess:
            # Use subprocess.run in a background thread to avoid blocking the loop.
            return subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        try:
            result = await anyio.to_thread.run_sync(_exec)
        except FileNotFoundError:
            logger.warning("TrivyScanner: 'trivy' binary not found (cmd=%s)", cmd)
            return []
        except Exception as exc:
            logger.exception("TrivyScanner: failed to execute Trivy command")
            return []

        if result.returncode not in (0, 5):  # 0 = no vulns, 5 = vulns found
            # Other codes usually mean errors
            logger.warning(
                "TrivyScanner: non-zero exit code=%s for cmd=%s stderr=%s",
                result.returncode,
                cmd,
                (result.stderr or "").strip()[:500],
            )
            return []

        stdout = (result.stdout or "").strip()
        if not stdout:
            logger.debug("TrivyScanner: no output for target=%s", target)
            return []

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            logger.exception("TrivyScanner: failed to parse JSON output")
            return []

        return self._parse_trivy_json(
            data=data,
            target=target,
            target_type=target_type,
        )

    def _parse_trivy_json(
        self,
        *,
        data: Any,
        target: str,
        target_type: str,
    ) -> List[SecurityFinding]:
        """
        Parse Trivy JSON output into SecurityFinding objects.

        We handle both:
          - normal 'Results' structure,
          - or multiple targets in a list.
        """
        findings: List[SecurityFinding] = []

        if isinstance(data, list):
            # Some Trivy modes produce a list of results
            for item in data:
                findings.extend(
                    self._parse_trivy_target(
                        item,
                        target=target,
                        target_type=target_type,
                    )
                )
        elif isinstance(data, dict):
            findings.extend(
                self._parse_trivy_target(
                    data,
                    target=target,
                    target_type=target_type,
                )
            )
        else:
            logger.warning("TrivyScanner: unexpected JSON type: %s", type(data))

        return findings

    def _parse_trivy_target(
        self,
        item: Dict[str, Any],
        *,
        target: str,
        target_type: str,
    ) -> List[SecurityFinding]:
        """
        Parse a single Trivy result item (one target) into findings.
        """
        scanner_name = "trivy"
        resolved_target = item.get("Target") or target
        results = item.get("Results") or []

        findings: List[SecurityFinding] = []
        for r in results:
            vulns = r.get("Vulnerabilities") or []
            if not isinstance(vulns, list):
                continue

            for v in vulns:
                severity = v.get("Severity")
                vuln_id = v.get("VulnerabilityID")
                title = v.get("Title") or v.get("Description") or vuln_id
                description = v.get("Description")
                pkg_name = v.get("PkgName")
                installed = v.get("InstalledVersion")
                fixed = v.get("FixedVersion")

                references_raw = v.get("References") or []
                if isinstance(references_raw, list):
                    refs = [str(x) for x in references_raw]
                else:
                    refs = []

                meta = {
                    "target": resolved_target,
                    "pkg_path": r.get("Target"),
                    "class": r.get("Class"),
                    "type": r.get("Type"),
                    "data_source": v.get("DataSource"),
                    "published_date": v.get("PublishedDate"),
                    "last_modified_date": v.get("LastModifiedDate"),
                }

                findings.append(
                    SecurityFinding(
                        scanner=scanner_name,
                        target=resolved_target,
                        type=target_type,
                        severity=severity,
                        id=vuln_id,
                        title=title,
                        description=description,
                        package=pkg_name,
                        version=installed,
                        fixed_version=fixed,
                        references=refs,
                        metadata=meta,
                    )
                )

        return findings


# ---------------------------------------------------------------------------
# Orchestrator / factory
# ---------------------------------------------------------------------------


class SecurityScanners:
    """
    Convenience orchestrator for all available scanners.

    For now it only wraps Trivy, but is designed to be extended with
    more scanners (e.g. Snyk) without breaking callers.

    Typical usage in a check:

        scanners = SecurityScanners(settings)
        image_findings = await scanners.scan_container_image("nginx:latest")
        fs_findings = await scanners.scan_filesystem("/app")
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.trivy = TrivyScanner(settings)

    async def scan_container_image(self, image: str) -> List[SecurityFinding]:
        """
        Run all configured container scanners on an image.
        Currently: Trivy only.
        """
        findings: List[SecurityFinding] = []

        # Trivy
        try:
            findings.extend(await self.trivy.scan_image(image))
        except Exception:
            logger.exception("SecurityScanners: Trivy image scan failed")

        # Future: Snyk, etc.

        return findings

    async def scan_filesystem(self, path: str) -> List[SecurityFinding]:
        """
        Run all configured filesystem scanners on a directory.
        Currently: Trivy only.
        """
        findings: List[SecurityFinding] = []

        # Trivy
        try:
            findings.extend(await self.trivy.scan_filesystem(path))
        except Exception:
            logger.exception("SecurityScanners: Trivy filesystem scan failed")

        # Future: Snyk, etc.

        return findings


def get_security_scanners(settings: Settings) -> SecurityScanners:
    """
    Factory helper for dependency injection.

    Example use in a check:

        from integrations.security.scanners import get_security_scanners
        from utils.config import settings

        scanners = get_security_scanners(settings)
        findings = await scanners.scan_container_image("nginx:latest")
    """
    return SecurityScanners(settings=settings)
