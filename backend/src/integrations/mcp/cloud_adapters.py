# backend/src/integrations/mcp/cloud_adapters.py

"""Cloud platform adapters (AWS, GCP, Azure) with full implementations."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .mcp_adapter_base import MCPAdapter, MCPConnection, MCPCapability

logger = logging.getLogger(__name__)


class AWSAdapter(MCPAdapter):
    """AWS integration using boto3."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.region = config.get("aws_region", "us-east-1")
        self.capabilities = [MCPCapability.READ, MCPCapability.WRITE, MCPCapability.EXECUTE, MCPCapability.CONFIGURE]
        self.session = None
    
    async def connect(self) -> MCPConnection:
        try:
            import boto3
            self.session = boto3.Session(region_name=self.region)
            sts = self.session.client("sts")
            identity = sts.get_caller_identity()
            self.connected = True
            self.connection = MCPConnection(
                adapter_id=self.adapter_id,
                adapter_type="aws",
                endpoint=f"https://*.{self.region}.amazonaws.com",
                authenticated=True,
                capabilities=self.capabilities,
                metadata={"account_id": identity["Account"], "region": self.region},
                connected_at=datetime.utcnow()
            )
            logger.info(f"Connected to AWS account {identity['Account']}")
            return self.connection
        except ImportError:
            raise RuntimeError("boto3 not installed. Run: pip install boto3")
    
    async def disconnect(self) -> None:
        self.session = None
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            sts = self.session.client("sts")
            sts.get_caller_identity()
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """Read AWS resources."""
        params = params or {}
        service, resource_type = resource.split("/", 1)
        client = self.session.client(service)
        
        if service == "s3":
            if resource_type == "buckets":
                return client.list_buckets()
            elif resource_type.startswith("objects/"):
                bucket = resource_type.split("/", 1)[1]
                prefix = params.get("prefix", "")
                return client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        elif service == "ec2":
            if resource_type == "instances":
                filters = params.get("filters", [])
                return client.describe_instances(Filters=filters)
            elif resource_type == "security-groups":
                return client.describe_security_groups()
            elif resource_type == "vpcs":
                return client.describe_vpcs()
        
        elif service == "iam":
            if resource_type == "users":
                return client.list_users()
            elif resource_type == "roles":
                return client.list_roles()
            elif resource_type == "policies":
                return client.list_policies(Scope="Local")
        
        elif service == "lambda":
            if resource_type == "functions":
                return client.list_functions()
        
        elif service == "rds":
            if resource_type == "instances":
                return client.describe_db_instances()
        
        raise ValueError(f"Unsupported resource: {resource}")
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Write to AWS resources."""
        params = params or {}
        service, resource_type = resource.split("/", 1)
        client = self.session.client(service)
        
        if service == "s3":
            if resource_type.startswith("objects/"):
                parts = resource_type.split("/", 2)
                bucket = parts[1]
                key = parts[2] if len(parts) > 2 else params.get("key", "uploaded-object")
                client.put_object(Bucket=bucket, Key=key, Body=data)
                return {"status": "uploaded", "bucket": bucket, "key": key}
        
        elif service == "ec2":
            if resource_type == "tags":
                instance_id = params.get("instance_id")
                tags = data if isinstance(data, list) else [data]
                client.create_tags(Resources=[instance_id], Tags=tags)
                return {"status": "tags_created", "instance_id": instance_id}
        
        elif service == "ssm":
            if resource_type == "parameter":
                name = params.get("name")
                client.put_parameter(Name=name, Value=data, Type="SecureString", Overwrite=True)
                return {"status": "parameter_stored", "name": name}
        
        raise ValueError(f"Unsupported write resource: {resource}")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute AWS actions."""
        params = params or {}
        
        if action == "scan_security":
            # AWS Security Hub findings
            securityhub = self.session.client("securityhub")
            findings = securityhub.get_findings(MaxResults=100)
            return {
                "status": "scanned",
                "findings_count": len(findings.get("Findings", [])),
                "findings": findings.get("Findings", [])[:10]  # Return first 10
            }
        
        elif action == "run_ssm_command":
            ssm = self.session.client("ssm")
            instance_ids = params.get("instance_ids", [])
            document = params.get("document", "AWS-RunShellScript")
            commands = params.get("commands", ["echo 'Hello'"])
            
            response = ssm.send_command(
                InstanceIds=instance_ids,
                DocumentName=document,
                Parameters={"commands": commands}
            )
            return {
                "status": "command_sent",
                "command_id": response["Command"]["CommandId"]
            }
        
        elif action == "start_instances":
            ec2 = self.session.client("ec2")
            instance_ids = params.get("instance_ids", [])
            ec2.start_instances(InstanceIds=instance_ids)
            return {"status": "starting", "instance_ids": instance_ids}
        
        elif action == "stop_instances":
            ec2 = self.session.client("ec2")
            instance_ids = params.get("instance_ids", [])
            ec2.stop_instances(InstanceIds=instance_ids)
            return {"status": "stopping", "instance_ids": instance_ids}
        
        raise ValueError(f"Unknown action: {action}")


class GCPAdapter(MCPAdapter):
    """Google Cloud Platform integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_id = config.get("gcp_project_id")
        self.capabilities = [MCPCapability.READ, MCPCapability.WRITE, MCPCapability.EXECUTE, MCPCapability.CONFIGURE]
        self.storage_client = None
        self.compute_client = None
    
    async def connect(self) -> MCPConnection:
        try:
            from google.cloud import storage
            from google.cloud import compute_v1
            
            self.storage_client = storage.Client(project=self.project_id)
            self.compute_client = compute_v1.InstancesClient()
            self.connected = True
            self.connection = MCPConnection(
                adapter_id=self.adapter_id,
                adapter_type="gcp",
                endpoint="https://cloud.google.com",
                authenticated=True,
                capabilities=self.capabilities,
                metadata={"project_id": self.project_id},
                connected_at=datetime.utcnow()
            )
            logger.info(f"Connected to GCP project {self.project_id}")
            return self.connection
        except ImportError as e:
            raise RuntimeError(f"GCP libraries not installed: {e}")
    
    async def disconnect(self) -> None:
        self.storage_client = None
        self.compute_client = None
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            list(self.storage_client.list_buckets(max_results=1))
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """Read GCP resources."""
        params = params or {}
        
        if resource == "storage/buckets":
            buckets = list(self.storage_client.list_buckets())
            return {"buckets": [b.name for b in buckets]}
        
        elif resource.startswith("storage/objects/"):
            bucket_name = resource.split("/", 2)[2]
            bucket = self.storage_client.bucket(bucket_name)
            prefix = params.get("prefix", "")
            blobs = list(bucket.list_blobs(prefix=prefix, max_results=100))
            return {"objects": [b.name for b in blobs]}
        
        elif resource == "compute/instances":
            from google.cloud import compute_v1
            zone = params.get("zone", "us-central1-a")
            request = compute_v1.ListInstancesRequest(project=self.project_id, zone=zone)
            instances = list(self.compute_client.list(request=request))
            return {"instances": [{"name": i.name, "status": i.status} for i in instances]}
        
        elif resource == "compute/zones":
            from google.cloud import compute_v1
            zones_client = compute_v1.ZonesClient()
            zones = list(zones_client.list(project=self.project_id))
            return {"zones": [z.name for z in zones]}
        
        raise ValueError(f"Unsupported resource: {resource}")
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Write to GCP resources."""
        params = params or {}
        
        if resource.startswith("storage/objects/"):
            parts = resource.split("/")
            bucket_name = parts[2]
            object_name = "/".join(parts[3:]) if len(parts) > 3 else params.get("name", "uploaded-object")
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            blob.upload_from_string(data)
            return {"status": "uploaded", "bucket": bucket_name, "object": object_name}
        
        raise ValueError(f"Unsupported write resource: {resource}")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GCP actions."""
        params = params or {}
        
        if action == "scan_security":
            # Security Command Center scan
            try:
                from google.cloud import securitycenter_v1
                client = securitycenter_v1.SecurityCenterClient()
                org_name = params.get("organization", self.project_id)
                
                findings = client.list_findings(
                    request={"parent": f"organizations/{org_name}/sources/-"}
                )
                findings_list = list(findings)[:10]
                return {
                    "status": "scanned",
                    "findings_count": len(findings_list),
                    "findings": [f.finding.name for f in findings_list]
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif action == "start_instance":
            from google.cloud import compute_v1
            zone = params.get("zone", "us-central1-a")
            instance = params.get("instance")
            self.compute_client.start(project=self.project_id, zone=zone, instance=instance)
            return {"status": "starting", "instance": instance}
        
        elif action == "stop_instance":
            from google.cloud import compute_v1
            zone = params.get("zone", "us-central1-a")
            instance = params.get("instance")
            self.compute_client.stop(project=self.project_id, zone=zone, instance=instance)
            return {"status": "stopping", "instance": instance}
        
        raise ValueError(f"Unknown action: {action}")


class AzureAdapter(MCPAdapter):
    """Microsoft Azure integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.subscription_id = config.get("azure_subscription_id")
        self.resource_group = config.get("azure_resource_group")
        self.capabilities = [MCPCapability.READ, MCPCapability.WRITE, MCPCapability.EXECUTE, MCPCapability.CONFIGURE]
        self.credential = None
        self.resource_client = None
        self.compute_client = None
        self.storage_client = None
    
    async def connect(self) -> MCPConnection:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.storage import StorageManagementClient
            
            self.credential = DefaultAzureCredential()
            self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            self.storage_client = StorageManagementClient(self.credential, self.subscription_id)
            
            self.connected = True
            self.connection = MCPConnection(
                adapter_id=self.adapter_id,
                adapter_type="azure",
                endpoint="https://management.azure.com",
                authenticated=True,
                capabilities=self.capabilities,
                metadata={"subscription_id": self.subscription_id},
                connected_at=datetime.utcnow()
            )
            logger.info(f"Connected to Azure subscription {self.subscription_id}")
            return self.connection
        except ImportError as e:
            raise RuntimeError(f"Azure libraries not installed: {e}")
    
    async def disconnect(self) -> None:
        self.credential = None
        self.resource_client = None
        self.compute_client = None
        self.storage_client = None
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            list(self.resource_client.resource_groups.list())
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def read(self, resource: str, params: Optional[Dict] = None) -> Any:
        """Read Azure resources."""
        params = params or {}
        
        if resource == "resource-groups":
            groups = list(self.resource_client.resource_groups.list())
            return {"resource_groups": [g.name for g in groups]}
        
        elif resource == "compute/vms":
            rg = params.get("resource_group", self.resource_group)
            if rg:
                vms = list(self.compute_client.virtual_machines.list(rg))
            else:
                vms = list(self.compute_client.virtual_machines.list_all())
            return {"vms": [{"name": vm.name, "location": vm.location} for vm in vms]}
        
        elif resource == "storage/accounts":
            accounts = list(self.storage_client.storage_accounts.list())
            return {"accounts": [a.name for a in accounts]}
        
        elif resource == "resources":
            rg = params.get("resource_group", self.resource_group)
            if rg:
                resources = list(self.resource_client.resources.list_by_resource_group(rg))
            else:
                resources = list(self.resource_client.resources.list())
            return {"resources": [{"name": r.name, "type": r.type} for r in resources[:50]]}
        
        raise ValueError(f"Unsupported resource: {resource}")
    
    async def write(self, resource: str, data: Any, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Write to Azure resources."""
        params = params or {}
        
        if resource == "resource-groups":
            name = params.get("name")
            location = params.get("location", "eastus")
            self.resource_client.resource_groups.create_or_update(
                name, {"location": location}
            )
            return {"status": "created", "name": name, "location": location}
        
        elif resource == "tags":
            resource_id = params.get("resource_id")
            tags = data if isinstance(data, dict) else {}
            self.resource_client.tags.create_or_update_at_scope(
                resource_id, {"properties": {"tags": tags}}
            )
            return {"status": "tags_updated", "resource_id": resource_id}
        
        raise ValueError(f"Unsupported write resource: {resource}")
    
    async def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Azure actions."""
        params = params or {}
        
        if action == "scan_security":
            try:
                from azure.mgmt.security import SecurityCenter
                security_client = SecurityCenter(self.credential, self.subscription_id)
                
                # Get security alerts
                alerts = list(security_client.alerts.list())[:10]
                return {
                    "status": "scanned",
                    "alerts_count": len(alerts),
                    "alerts": [a.name for a in alerts]
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif action == "start_vm":
            rg = params.get("resource_group", self.resource_group)
            vm_name = params.get("vm_name")
            self.compute_client.virtual_machines.begin_start(rg, vm_name)
            return {"status": "starting", "vm_name": vm_name}
        
        elif action == "stop_vm":
            rg = params.get("resource_group", self.resource_group)
            vm_name = params.get("vm_name")
            self.compute_client.virtual_machines.begin_deallocate(rg, vm_name)
            return {"status": "stopping", "vm_name": vm_name}
        
        elif action == "restart_vm":
            rg = params.get("resource_group", self.resource_group)
            vm_name = params.get("vm_name")
            self.compute_client.virtual_machines.begin_restart(rg, vm_name)
            return {"status": "restarting", "vm_name": vm_name}
        
        raise ValueError(f"Unknown action: {action}")
