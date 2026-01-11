"""
Shadow IT Scanner - Asset Discovery

Crawls the network to find unauthorized assets.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


@dataclass
class NetworkAsset:
    ip: str
    port: int
    service_banner: str
    detected_at: datetime = field(default_factory=datetime.now)
    status: str = "unauthorized"  # unauthorized, authorized, ignored


class ShadowITScanner:
    """
    Scans for Shadow IT and brings it under control.
    """

    def __init__(self):
        self.known_assets: Dict[str, NetworkAsset] = {}
        self.authorized_policies: Set[str] = set() # Set of "ip:port" that are allowed

    def authorize_asset(self, ip: str, port: int):
        """Mark an asset as authorized."""
        self.authorized_policies.add(f"{ip}:{port}")
        key = f"{ip}:{port}"
        if key in self.known_assets:
            self.known_assets[key].status = "authorized"
            logger.info(f"Asset {key} authorized.")

    def scan_network(self, subnet: str = "192.168.1.0/24") -> List[NetworkAsset]:
        """
        Simulate a network scan.
        In a real scenario, this would use nmap or similar.
        """
        logger.info(f"Scanning subnet {subnet}...")

        # Mock finding assets.
        # In a real impl, this would loop through IPs/Ports.
        found_assets = []

        # This function is mainly a placeholder for the logic.
        # We rely on `report_asset` being called by the simulation/mock or actual scanner integration.
        return found_assets

    def report_asset(self, ip: str, port: int, banner: str):
        """
        Report a found asset.
        """
        key = f"{ip}:{port}"
        status = "authorized" if key in self.authorized_policies else "unauthorized"

        asset = NetworkAsset(
            ip=ip,
            port=port,
            service_banner=banner,
            status=status
        )

        if key not in self.known_assets:
            self.known_assets[key] = asset
            if status == "unauthorized":
                logger.warning(f"SHADOW IT DETECTED: {ip}:{port} ({banner})")
                self._trigger_policy_control(asset)
        else:
            # Update existing
            self.known_assets[key] = asset

    def _trigger_policy_control(self, asset: NetworkAsset):
        """
        Attempt to bring the asset under control.
        """
        logger.info(f"Initiating policy control for {asset.ip}:{asset.port}")
        # Logic to:
        # 1. Notify admin
        # 2. Block port (if firewall integration exists)
        # 3. Attempt to identify owner

        # For this simplified version, we just log.
        pass

    def get_unauthorized_assets(self) -> List[NetworkAsset]:
        return [a for a in self.known_assets.values() if a.status == "unauthorized"]


# Global instance
shadow_it_scanner = ShadowITScanner()
