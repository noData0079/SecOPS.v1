"""
Auth Module - Identity Security

Components:
- IdentitySentinel: Impossible Travel and Anomalous Usage detection
"""

from .identity_sentinel import (
    IdentitySentinel,
    LoginEvent,
    identity_sentinel,
)

__all__ = [
    "IdentitySentinel",
    "LoginEvent",
    "identity_sentinel",
]
