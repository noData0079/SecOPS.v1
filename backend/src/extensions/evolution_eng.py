# backend/src/extensions/evolution_engine.py

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .feature_store import FeatureEvent, FeatureStore
from .policy_engine import Policy, PolicyStore


@dataclass
class ArmStats:
    """
    Statistics for a single "arm" (variant) in a multi-armed bandit.

    We keep:
      - number of times chosen,
      - total reward,
      - simple running mean.
    """

    name: str
    pulls: int = 0
    total_reward: float = 0.0

    @property
    def mean_reward(self) -> float:
        if self.pulls == 0:
            return 0.0
        return self.total_reward / self.pulls


class ThompsonBandit:
    """
    Simple Bernoulli Thompson Sampling bandit.

    Used here as a generic optimizer:
      - arms are different policy variants or strategies,
      - reward is a scalar signal (e.g. +1 for "user liked it", 0 for ignore).

    This is a very standard, state-of-the-art pattern for online,
    lightweight adaptation without needing heavy ML frameworks.
    """

    def __init__(self) -> None:
        self._stats: Dict[str, ArmStats] = {}

    def register_arm(self, name: str) -> None:
        if name not in self._stats:
            self._stats[name] = ArmStats(name=name)

    def choose_arm(self) -> str:
        if not self._stats:
            raise RuntimeError("No arms registered for ThompsonBandit")

        samples: List[Tuple[str, float]] = []

        for name, s in self._stats.items():
            alpha = 1.0 + max(s.total_reward, 0.0)
            beta_param = 1.0 + max(s.pulls - s.total_reward, 0.0)
            sample = random.betavariate(alpha, beta_param)
            samples.append((name, sample))

        samples.sort(key=lambda x: x[1], reverse=True)
        return samples[0][0]

    def update(self, name: str, reward: float) -> None:
        if name not in self._stats:
            self._stats[name] = ArmStats(name=name)
        s = self._stats[name]
        s.pulls += 1
        s.total_reward += reward


class EvolutionEngine:
    """
    High-level "auto-evolution" engine for T79 AI.

    Responsibilities:
      - Track events (FeatureEvents) from the platform.
      - Maintain a simple bandit over different policy variants.
      - Propose which policy variant to use next for a given policy.
      - Optionally emit updated policies via PolicyStore.

    This is deliberately generic so you can plug it into different
    workflows: issue triage, check scheduling, severity thresholds, etc.

    IMPORTANT:
      This module is completely optional and not wired into the core
      runtime by default. You integrate it where appropriate.
    """

    def __init__(self, feature_store: FeatureStore, policy_store: PolicyStore) -> None:
        self._feature_store = feature_store
        self._policy_store = policy_store
        self._bandits: Dict[str, ThompsonBandit] = defaultdict(ThompsonBandit)

    def _bandit_for_policy(self, policy_name: str) -> ThompsonBandit:
        return self._bandits[policy_name]

    def register_policy_variants(self, policy_name: str, variant_names: List[str]) -> None:
        """
        Register the set of possible variants for a given policy.

        Example:
          policy_name = "check_frequency"
          variant_names = ["aggressive", "balanced", "conservative"]
        """
        bandit = self._bandit_for_policy(policy_name)
        for name in variant_names:
            bandit.register_arm(name)

    def choose_policy_variant(self, policy_name: str) -> str:
        """
        Choose the next variant for a given policy using Thompson Sampling.
        """
        bandit = self._bandit_for_policy(policy_name)
        return bandit.choose_arm()

    def record_feedback(
        self,
        policy_name: str,
        variant_name: str,
        reward: float,
        features: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record feedback about how well a policy variant performed.

        - `reward` could be:
            +1.0 → user found suggestion helpful
             0.0 → neutral
            -1.0 → user marked as noisy / wrong
        """
        bandit = self._bandit_for_policy(policy_name)
        bandit.update(variant_name, reward)

        event = FeatureEvent(
            id=f"{policy_name}:{variant_name}:{datetime.utcnow().isoformat()}",
            kind="policy_feedback",
            timestamp=datetime.utcnow(),
            features=features or {},
            label=reward,
        )
        self._feature_store.add_event(event)

    def materialize_policy(
        self,
        policy_name: str,
        base_parameters: Dict[str, Any],
        variant_strategy: Dict[str, Dict[str, Any]],
        description: Optional[str] = None,
    ) -> Policy:
        """
        Build a concrete Policy object from the best current variant.

        - `base_parameters`: default parameters for the policy.
        - `variant_strategy`: mapping variant_name → parameter overrides.

        Returns the chosen Policy and updates the PolicyStore.
        """
        variant_name = self.choose_policy_variant(policy_name)
        params = dict(base_parameters)
        overrides = variant_strategy.get(variant_name, {})
        params.update(overrides)

        existing = self._policy_store.get_policy(policy_name)
        version = 1 if existing is None else existing.version + 1

        policy = Policy(
            name=policy_name,
            version=version,
            parameters=params,
            description=description or f"Auto-evolved variant: {variant_name}",
        )
        self._policy_store.upsert_policy(policy)
        return policy
