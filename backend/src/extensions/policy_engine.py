# backend/src/extensions/policy_engine.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class Policy:
    """
    A simple representation of a tunable policy.

    Examples:
      - how frequently to run a specific check
      - what severity threshold to alert on
      - how aggressively to suggest fixes vs. just report issues

    `parameters` are arbitrary key/value pairs that you define.
    """

    name: str
    version: int
    parameters: Dict[str, Any]
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        return cls(
            name=str(data["name"]),
            version=int(data.get("version", 1)),
            parameters=dict(data.get("parameters", {})),
            description=data.get("description"),
        )


class PolicyStore:
    """
    In-memory policy registry.

    This is intentionally lightweight so that:
      - you can start with in-memory + static policies,
      - later you can back this with Supabase (or another DB) without
        changing the interface used by the evolution engine.
    """

    def __init__(self) -> None:
        self._policies: Dict[str, Policy] = {}

    def upsert_policy(self, policy: Policy) -> None:
        self._policies[policy.name] = policy

    def get_policy(self, name: str) -> Optional[Policy]:
        return self._policies.get(name)

    def all_policies(self) -> Dict[str, Policy]:
        return dict(self._policies)
