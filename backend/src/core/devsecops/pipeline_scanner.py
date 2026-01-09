# backend/src/core/devsecops/pipeline_scanner.py

"""CI/CD pipeline security scanner for detecting vulnerabilities and misconfigurations."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CheckSeverity(str, Enum):
    """Security check severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CheckCategory(str, Enum):
    """Security check categories."""
    SECRETS = "secrets"
    PERMISSIONS = "permissions"
    DEPENDENCIES = "dependencies"
    CONFIGURATION = "configuration"
    INJECTION = "injection"
    SUPPLY_CHAIN = "supply_chain"


@dataclass
class SecurityCheck:
    """A single security check finding."""
    check_id: str
    name: str
    category: CheckCategory
    severity: CheckSeverity
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str = ""
    cwe_id: Optional[str] = None
    evidence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id,
            "evidence": self.evidence,
        }


@dataclass
class PipelineSecurityResult:
    """Results from a pipeline security scan."""
    pipeline_name: str
    scanned_at: datetime = field(default_factory=datetime.utcnow)
    findings: List[SecurityCheck] = field(default_factory=list)
    files_scanned: int = 0
    scan_duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_name": self.pipeline_name,
            "scanned_at": self.scanned_at.isoformat(),
            "findings": [f.to_dict() for f in self.findings],
            "findings_count": len(self.findings),
            "by_severity": self._count_by_severity(),
            "files_scanned": self.files_scanned,
            "scan_duration_ms": self.scan_duration_ms,
        }
    
    def _count_by_severity(self) -> Dict[str, int]:
        counts = {s.value: 0 for s in CheckSeverity}
        for f in self.findings:
            counts[f.severity.value] += 1
        return counts
    
    @property
    def passed(self) -> bool:
        """Check if scan passed (no critical/high findings)."""
        return not any(
            f.severity in [CheckSeverity.CRITICAL, CheckSeverity.HIGH]
            for f in self.findings
        )


class PipelineScanner:
    """
    Security scanner for CI/CD pipelines.
    
    Detects:
    - Hardcoded secrets and credentials
    - Insecure permissions (write-all, etc.)
    - Vulnerable dependencies
    - Injection vulnerabilities
    - Supply chain risks
    - Misconfigurations
    """
    
    # Secret patterns
    SECRET_PATTERNS = [
        (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[\w-]{20,}', "API Key exposed"),
        (r'(?i)(secret|password|passwd|pwd)\s*[:=]\s*["\'][^"\']+', "Hardcoded secret"),
        (r'(?i)aws[_-]?(access|secret)[_-]?key\s*[:=]', "AWS credential"),
        (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
        (r'gho_[a-zA-Z0-9]{36}', "GitHub OAuth Token"),
        (r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}', "GitHub PAT (fine-grained)"),
        (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key"),
        (r'AIza[0-9A-Za-z-_]{35}', "Google API Key"),
        (r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----', "Private key embedded"),
    ]
    
    # Dangerous GitHub Actions patterns
    DANGEROUS_PATTERNS = [
        (r'permissions:\s*write-all', "Overly permissive workflow permissions"),
        (r'pull_request_target:', "Potentially dangerous trigger for PRs from forks"),
        (r'\$\{\{\s*github\.event\.issue\.body', "Potential injection from issue body"),
        (r'\$\{\{\s*github\.event\.pull_request\.title', "Potential injection from PR title"),
        (r'\$\{\{\s*github\.event\.comment\.body', "Potential injection from comment"),
        (r'curl.*\|\s*bash', "Piping curl to bash is dangerous"),
        (r'wget.*\|\s*sh', "Piping wget to shell is dangerous"),
    ]
    
    def __init__(self):
        """Initialize pipeline scanner."""
        self._compiled_secret_patterns = [
            (re.compile(pattern), desc)
            for pattern, desc in self.SECRET_PATTERNS
        ]
        self._compiled_danger_patterns = [
            (re.compile(pattern), desc)
            for pattern, desc in self.DANGEROUS_PATTERNS
        ]
        logger.info("PipelineScanner initialized")
    
    async def scan_directory(self, directory: str) -> PipelineSecurityResult:
        """
        Scan a directory for pipeline security issues.
        
        Args:
            directory: Path to scan
            
        Returns:
            PipelineSecurityResult with findings
        """
        import time
        start_time = time.time()
        
        findings: List[SecurityCheck] = []
        files_scanned = 0
        
        path = Path(directory)
        
        # Scan workflow files
        workflow_patterns = [
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".circleci/config.yml",
            "azure-pipelines.yml",
            ".travis.yml",
        ]
        
        for pattern in workflow_patterns:
            for file_path in path.glob(pattern):
                file_findings = await self._scan_file(file_path)
                findings.extend(file_findings)
                files_scanned += 1
        
        # Scan Dockerfiles
        for dockerfile in path.rglob("Dockerfile*"):
            file_findings = await self._scan_dockerfile(dockerfile)
            findings.extend(file_findings)
            files_scanned += 1
        
        # Scan for secrets in common config files
        config_files = ["*.env", "*.env.*", "config*.yml", "config*.yaml", "*.conf"]
        for pattern in config_files:
            for file_path in path.rglob(pattern):
                # Skip .env.example files
                if ".example" in str(file_path) or ".sample" in str(file_path):
                    continue
                file_findings = await self._scan_for_secrets(file_path)
                findings.extend(file_findings)
                files_scanned += 1
        
        scan_duration = (time.time() - start_time) * 1000
        
        result = PipelineSecurityResult(
            pipeline_name=str(directory),
            findings=findings,
            files_scanned=files_scanned,
            scan_duration_ms=scan_duration,
        )
        
        logger.info(f"Scanned {files_scanned} files, found {len(findings)} issues")
        return result
    
    async def _scan_file(self, file_path: Path) -> List[SecurityCheck]:
        """Scan a workflow file for security issues."""
        findings = []
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            for line_num, line in enumerate(lines, 1):
                # Check for secrets
                for pattern, description in self._compiled_secret_patterns:
                    if pattern.search(line):
                        findings.append(SecurityCheck(
                            check_id=f"SEC-{len(findings)+1:03d}",
                            name="Hardcoded Secret",
                            category=CheckCategory.SECRETS,
                            severity=CheckSeverity.CRITICAL,
                            description=description,
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Use secrets management (e.g., GitHub Secrets, Vault)",
                            cwe_id="CWE-798",
                            evidence=line[:100],
                        ))
                
                # Check for dangerous patterns
                for pattern, description in self._compiled_danger_patterns:
                    if pattern.search(line):
                        findings.append(SecurityCheck(
                            check_id=f"CFG-{len(findings)+1:03d}",
                            name="Insecure Configuration",
                            category=CheckCategory.CONFIGURATION,
                            severity=CheckSeverity.HIGH,
                            description=description,
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Review and restrict permissions/inputs",
                            evidence=line[:100],
                        ))
            
            # Check for missing security features
            if "permissions:" not in content and file_path.suffix in [".yml", ".yaml"]:
                findings.append(SecurityCheck(
                    check_id=f"CFG-{len(findings)+1:03d}",
                    name="Missing Permissions Block",
                    category=CheckCategory.PERMISSIONS,
                    severity=CheckSeverity.MEDIUM,
                    description="Workflow lacks explicit permissions declaration",
                    file_path=str(file_path),
                    recommendation="Add explicit permissions block with least privilege",
                ))
                
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
        
        return findings
    
    async def _scan_dockerfile(self, file_path: Path) -> List[SecurityCheck]:
        """Scan Dockerfile for security issues."""
        findings = []
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            has_user_directive = False
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for running as root
                if line_stripped.startswith("USER "):
                    user = line_stripped[5:].strip()
                    if user.lower() not in ["root", "0"]:
                        has_user_directive = True
                
                # Check for secrets in ENV
                if line_stripped.startswith("ENV "):
                    for pattern, description in self._compiled_secret_patterns:
                        if pattern.search(line_stripped):
                            findings.append(SecurityCheck(
                                check_id=f"SEC-{len(findings)+1:03d}",
                                name="Secret in Dockerfile ENV",
                                category=CheckCategory.SECRETS,
                                severity=CheckSeverity.CRITICAL,
                                description=description,
                                file_path=str(file_path),
                                line_number=line_num,
                                recommendation="Use build args or runtime secrets",
                                cwe_id="CWE-798",
                            ))
                
                # Check for latest tag
                if line_stripped.startswith("FROM ") and ":latest" in line_stripped:
                    findings.append(SecurityCheck(
                        check_id=f"CFG-{len(findings)+1:03d}",
                        name="Using latest Tag",
                        category=CheckCategory.SUPPLY_CHAIN,
                        severity=CheckSeverity.MEDIUM,
                        description="Using 'latest' tag can lead to unpredictable builds",
                        file_path=str(file_path),
                        line_number=line_num,
                        recommendation="Pin to a specific version/digest",
                    ))
                
                # Check for curl/wget piped to shell
                if "curl" in line_stripped and "|" in line_stripped and ("bash" in line_stripped or "sh" in line_stripped):
                    findings.append(SecurityCheck(
                        check_id=f"INJ-{len(findings)+1:03d}",
                        name="Unsafe Remote Script Execution",
                        category=CheckCategory.INJECTION,
                        severity=CheckSeverity.HIGH,
                        description="Piping remote content to shell is dangerous",
                        file_path=str(file_path),
                        line_number=line_num,
                        recommendation="Download and verify scripts before execution",
                    ))
            
            # Check if running as root
            if not has_user_directive:
                findings.append(SecurityCheck(
                    check_id=f"CFG-{len(findings)+1:03d}",
                    name="Running as Root",
                    category=CheckCategory.PERMISSIONS,
                    severity=CheckSeverity.MEDIUM,
                    description="Container runs as root user",
                    file_path=str(file_path),
                    recommendation="Add USER directive to run as non-root",
                ))
                
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
        
        return findings
    
    async def _scan_for_secrets(self, file_path: Path) -> List[SecurityCheck]:
        """Scan file for hardcoded secrets."""
        findings = []
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in self._compiled_secret_patterns:
                    if pattern.search(line):
                        findings.append(SecurityCheck(
                            check_id=f"SEC-{len(findings)+1:03d}",
                            name="Hardcoded Secret",
                            category=CheckCategory.SECRETS,
                            severity=CheckSeverity.CRITICAL,
                            description=description,
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Use environment variables or secrets manager",
                            cwe_id="CWE-798",
                        ))
                        
        except Exception as e:
            logger.debug(f"Error scanning {file_path}: {e}")
        
        return findings
    
    async def scan_github_actions(self, workflow_content: str, workflow_name: str = "workflow") -> PipelineSecurityResult:
        """
        Scan GitHub Actions workflow content directly.
        
        Args:
            workflow_content: YAML content of the workflow
            workflow_name: Name for the result
            
        Returns:
            PipelineSecurityResult
        """
        import time
        import tempfile
        
        start_time = time.time()
        
        # Write to temp file and scan
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(workflow_content)
            temp_path = Path(f.name)
        
        try:
            findings = await self._scan_file(temp_path)
        finally:
            temp_path.unlink()
        
        scan_duration = (time.time() - start_time) * 1000
        
        return PipelineSecurityResult(
            pipeline_name=workflow_name,
            findings=findings,
            files_scanned=1,
            scan_duration_ms=scan_duration,
        )
