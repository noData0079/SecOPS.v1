# backend/src/integrations/mcp/security_adapters.py

"""Security scanning tool adapters (Prowler, Garak, Trivy, etc.)."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .mcp_adapter_base import MCPAdapter, MCPConnection, MCPCapability

logger = logging.getLogger(__name__)


class ProwlerAdapter(MCPAdapter):
    """Prowler AWS security scanner integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prowler_path = config.get("prowler_path", "prowler")
        self.output_dir = config.get("output_dir", "/tmp/prowler")
        self.capabilities = [MCPCapability.READ, MCPCapability.EXECUTE]
    
    async def connect(self) -> MCPConnection:
        # Verify prowler is installed
        try:
            result = subprocess.run([self.prowler_path, "--version"], capture_output=True, text=True, timeout=5)
            version = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception as e:
            logger.warning(f"Prowler not found: {e}")
            version = "not_installed"
        
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="prowler",
            endpoint="local",
            authenticated=True,
            capabilities=self.capabilities,
            metadata={"version": version},
            connected_at=datetime.utcnow()
        )
        return self.connection
    
    async def disconnect(self) -> None:
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            result = subprocess.run([self.prowler_path, "--version"], capture_output=True, timeout=5)
            return {"healthy": result.returncode == 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """Read Prowler scan results."""
        params = params or {}
        
        if resource == "findings":
            # Read latest scan results
            output_path = Path(self.output_dir)
            json_files = sorted(output_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            if not json_files:
                return {"findings": [], "message": "No scan results found"}
            
            with open(json_files[0], "r") as f:
                findings = json.load(f)
            
            severity_filter = params.get("severity")
            if severity_filter:
                findings = [f for f in findings if f.get("severity", "").lower() == severity_filter.lower()]
            
            return {"findings": findings, "count": len(findings)}
        
        elif resource == "summary":
            output_path = Path(self.output_dir)
            json_files = sorted(output_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            if not json_files:
                return {"summary": {}, "message": "No scan results found"}
            
            with open(json_files[0], "r") as f:
                findings = json.load(f)
            
            summary = {"total": len(findings), "by_severity": {}, "by_service": {}}
            for f in findings:
                sev = f.get("severity", "unknown")
                svc = f.get("service", "unknown")
                summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
                summary["by_service"][svc] = summary["by_service"].get(svc, 0) + 1
            
            return {"summary": summary}
        
        raise ValueError(f"Unsupported resource: {resource}")
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        raise NotImplementedError("Prowler does not support write operations")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Prowler security scan."""
        params = params or {}
        
        if action == "scan_aws":
            services = params.get("services", [])
            regions = params.get("regions", [])
            compliance = params.get("compliance")
            
            cmd = [self.prowler_path, "aws"]
            if services:
                cmd.extend(["--services", ",".join(services)])
            if regions:
                cmd.extend(["--regions", ",".join(regions)])
            if compliance:
                cmd.extend(["--compliance", compliance])
            
            cmd.extend(["--output-formats", "json", "--output-directory", self.output_dir])
            
            logger.info(f"Running Prowler scan: {' '.join(cmd)}")
            
            # Run asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            return {
                "status": "scan_started",
                "pid": process.pid,
                "command": " ".join(cmd),
                "output_dir": self.output_dir
            }
        
        elif action == "scan_status":
            pid = params.get("pid")
            if pid:
                try:
                    import psutil
                    process = psutil.Process(pid)
                    return {"status": "running" if process.is_running() else "completed"}
                except Exception:
                    return {"status": "completed"}
            return {"status": "unknown"}
        
        raise ValueError(f"Unknown action: {action}")


class GarakAdapter(MCPAdapter):
    """Garak LLM vulnerability scanner integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.garak_path = config.get("garak_path", "garak")
        self.output_dir = config.get("output_dir", "/tmp/garak")
        self.capabilities = [MCPCapability.READ, MCPCapability.EXECUTE]
    
    async def connect(self) -> MCPConnection:
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="garak",
            endpoint="local",
            authenticated=True,
            capabilities=self.capabilities,
            metadata={},
            connected_at=datetime.utcnow()
        )
        return self.connection
    
    async def disconnect(self) -> None:
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            result = subprocess.run([self.garak_path, "--version"], capture_output=True, timeout=5)
            return {"healthy": result.returncode == 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """Read Garak scan results."""
        params = params or {}
        
        if resource == "results":
            output_path = Path(self.output_dir)
            json_files = sorted(output_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            if not json_files:
                return {"results": [], "message": "No scan results found"}
            
            with open(json_files[0], "r") as f:
                results = json.load(f)
            
            return {"results": results}
        
        elif resource == "probes":
            # List available probes
            result = subprocess.run([self.garak_path, "--list_probes"], capture_output=True, text=True, timeout=30)
            probes = [line.strip() for line in result.stdout.split("\n") if line.strip()]
            return {"probes": probes}
        
        raise ValueError(f"Unsupported resource: {resource}")
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        raise NotImplementedError("Garak does not support write operations")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Garak LLM vulnerability scan."""
        params = params or {}
        
        if action == "scan_llm":
            model = params.get("model")
            probes = params.get("probes", [])
            
            if not model:
                raise ValueError("model parameter is required")
            
            cmd = [self.garak_path, "--model_name", model]
            if probes:
                cmd.extend(["--probes", ",".join(probes)])
            
            cmd.extend(["--report_prefix", self.output_dir])
            
            logger.info(f"Running Garak scan: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            return {
                "status": "scan_started",
                "pid": process.pid,
                "model": model,
                "probes": probes
            }
        
        raise ValueError(f"Unknown action: {action}")


class TrivyAdapter(MCPAdapter):
    """Trivy container and IaC vulnerability scanner."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.trivy_path = config.get("trivy_path", "trivy")
        self.capabilities = [MCPCapability.READ, MCPCapability.EXECUTE]
    
    async def connect(self) -> MCPConnection:
        try:
            result = subprocess.run([self.trivy_path, "--version"], capture_output=True, text=True, timeout=5)
            version = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            version = "not_installed"
        
        self.connected = True
        self.connection = MCPConnection(
            adapter_id=self.adapter_id,
            adapter_type="trivy",
            endpoint="local",
            authenticated=True,
            capabilities=self.capabilities,
            metadata={"version": version},
            connected_at=datetime.utcnow()
        )
        return self.connection
    
    async def disconnect(self) -> None:
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            result = subprocess.run([self.trivy_path, "--version"], capture_output=True, timeout=5)
            return {"healthy": result.returncode == 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        raise ValueError(f"Unsupported resource: {resource}")
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        raise NotImplementedError("Trivy does not support write operations")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Trivy vulnerability scan."""
        params = params or {}
        
        if action == "scan_image":
            image = params.get("image")
            severity = params.get("severity", "HIGH,CRITICAL")
            
            if not image:
                raise ValueError("image parameter is required")
            
            cmd = [self.trivy_path, "image", "--format", "json", "--severity", severity, image]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    findings = json.loads(result.stdout)
                    return {"status": "completed", "findings": findings}
                except json.JSONDecodeError:
                    return {"status": "completed", "raw_output": result.stdout}
            
            return {"status": "error", "error": result.stderr}
        
        elif action == "scan_filesystem":
            path = params.get("path", ".")
            severity = params.get("severity", "HIGH,CRITICAL")
            
            cmd = [self.trivy_path, "fs", "--format", "json", "--severity", severity, path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                try:
                    findings = json.loads(result.stdout)
                    return {"status": "completed", "findings": findings}
                except json.JSONDecodeError:
                    return {"status": "completed", "raw_output": result.stdout}
            
            return {"status": "error", "error": result.stderr}
        
        elif action == "scan_config":
            path = params.get("path", ".")
            
            cmd = [self.trivy_path, "config", "--format", "json", path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                try:
                    findings = json.loads(result.stdout)
                    return {"status": "completed", "findings": findings}
                except json.JSONDecodeError:
                    return {"status": "completed", "raw_output": result.stdout}
            
            return {"status": "error", "error": result.stderr}
        
        raise ValueError(f"Unknown action: {action}")
