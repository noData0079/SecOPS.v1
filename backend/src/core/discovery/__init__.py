"""
Discovery Module - Asset Management and Shadow IT

Components:
- ShadowITScanner: Network scanning and policy control
"""

from .shadow_it_scanner import (
    ShadowITScanner,
    NetworkAsset,
    shadow_it_scanner,
)

__all__ = [
    "ShadowITScanner",
    "NetworkAsset",
    "shadow_it_scanner",
]
