# backend/src/services/cost_tracker.py

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple

from utils.config import Settings, settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ModelPrice:
    """
    Pricing for a single LLM/model in *base currency* per 1M tokens.

    Prices are split by direction because some providers have different
    input vs output token rates.

    Example: DeepSeek (dummy numbers)
        input_price_per_million  = 0.20   (e.g. $0.20 / 1M tokens)
        output_price_per_million = 0.20
    """

    input_price_per_million: Decimal
    output_price_per_million: Decimal

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelPrice":
        return cls(
            input_price_per_million=Decimal(str(data.get("input", data.get("input_price_per_million", "0")))),
            output_price_per_million=Decimal(str(data.get("output", data.get("output_price_per_million", "0")))),
        )


@dataclass
class UsageCost:
    """
    Result of a cost calculation for a single usage event.
    """

    raw_cost: Decimal          # what the platform pays providers
    billable_cost: Decimal     # what the user/org should be charged
    margin_rate: Decimal       # e.g. 0.20 == 20%
    currency: str              # e.g. "USD"


# ---------------------------------------------------------------------------
# Cost tracker
# ---------------------------------------------------------------------------


class CostTracker:
    """
    Cost and pricing engine for the platform.

    Responsibilities:
      - Compute raw cost for a given usage (tokens, etc.)
      - Apply tiered margins (20%/25%/30%/35%) to compute billable price
      - Track aggregate cost per org in memory (for quick estimates)
      - Provide quotation helpers for UI ("this integration will cost ...")

    Persistence/invoicing/billing gateways (Stripe, Razorpay, etc.)
    are intentionally NOT handled here; they can be wired on top.
    """

    def __init__(self, cfg: Settings) -> None:
        self.cfg = cfg

        self.currency: str = (
            getattr(cfg, "COST_BASE_CURRENCY", None)
            or os.getenv("COST_BASE_CURRENCY")
            or "USD"
        )

        # Tiered margin structure
        # Values are tuples: (upper_bound_inclusive, margin_rate)
        # Example: (Decimal("10"), Decimal("0.20")) → cost <= 10 ⇒ +20%.
        self.margin_tiers: Tuple[Tuple[Decimal, Decimal], ...] = self._load_margin_tiers(cfg)

        # Model pricing configuration
        # key: "provider:model"  → ModelPrice(...)
        self.model_pricing: Dict[str, ModelPrice] = self._load_model_pricing(cfg)

        # In-memory aggregates per org (not persistent – OK for MVP / short-term)
        # org_id -> {"raw": Decimal, "billable": Decimal}
        self.org_totals: Dict[str, Dict[str, Decimal]] = {}

        logger.info(
            "CostTracker initialized (currency=%s, models=%d)",
            self.currency,
            len(self.model_pricing),
        )

    # ------------------------------------------------------------------ #
    # Configuration loaders
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_margin_tiers(cfg: Settings) -> Tuple[Tuple[Decimal, Decimal], ...]:
        """
        Load margin tier configuration.

        Priority:
          1. COST_MARGIN_TIERS_JSON env / settings (JSON list)
          2. default structure (20/25/30/35)
        """
        raw = (
            getattr(cfg, "COST_MARGIN_TIERS_JSON", None)
            or os.getenv("COST_MARGIN_TIERS_JSON")
        )
        if raw:
            try:
                tiers = json.loads(raw)
                result = []
                for t in tiers:
                    limit = Decimal(str(t["limit"]))
                    margin = Decimal(str(t["margin"]))
                    result.append((limit, margin))
                # Ensure sorted by limit
                result.sort(key=lambda x: x[0])
                return tuple(result)
            except Exception:
                logger.exception("CostTracker: failed to parse COST_MARGIN_TIERS_JSON, falling back to defaults")

        # Defaults based on your specification
        return (
            (Decimal("10"), Decimal("0.20")),        # <= $10  → +20%
            (Decimal("1000"), Decimal("0.25")),      # <= $1,000 → +25%
            (Decimal("10000"), Decimal("0.30")),     # <= $10,000 → +30%
            (Decimal("1000000000"), Decimal("0.35")),  # > $100k → effectively +35% cap
        )

    @staticmethod
    def _load_model_pricing(cfg: Settings) -> Dict[str, ModelPrice]:
        """
        Load model pricing from settings or environment.

        Expected JSON format (either in settings.MODEL_PRICING_JSON or env):

            {
              "deepseek:r1": {"input": 0.003, "output": 0.003},
              "deepseek:v3": {"input": 0.003, "output": 0.003},
              "openai:gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
            }

        Values are cost per 1M tokens in base currency.

        If not provided, we set a very conservative default for a single
        generic "default" model to keep things working.
        """
        raw = (
            getattr(cfg, "MODEL_PRICING_JSON", None)
            or os.getenv("MODEL_PRICING_JSON")
        )
        pricing: Dict[str, ModelPrice] = {}

        if raw:
            try:
                data = json.loads(raw)
                for key, val in data.items():
                    pricing[key] = ModelPrice.from_dict(val)
            except Exception:
                logger.exception("CostTracker: failed to parse MODEL_PRICING_JSON")

        if not pricing:
            # Safe fallback: cheap default model
            pricing["default:llm"] = ModelPrice(
                input_price_per_million=Decimal("0.003"),
                output_price_per_million=Decimal("0.003"),
            )
            logger.warning(
                "CostTracker: MODEL_PRICING_JSON not configured – using default model pricing"
            )

        return pricing

    # ------------------------------------------------------------------ #
    # Core margin / pricing logic
    # ------------------------------------------------------------------ #

    def _select_margin_rate(self, base_cost: Decimal) -> Decimal:
        """
        Select appropriate margin rate for given base cost using tier rules.
        """
        for limit, margin in self.margin_tiers:
            if base_cost <= limit:
                return margin
        # Fallback (should never hit if tiers set up correctly)
        return Decimal("0.35")

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        """
        Round monetary values to 4 decimal places by default.
        This is flexible enough for tokens; final invoicing can re-round.
        """
        return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def estimate_llm_cost(
        self,
        *,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageCost:
        """
        Estimate cost for a single LLM call and apply margin.

        This does NOT mutate org totals by itself – it's just a calculator.
        Use `record_llm_usage_for_org` when you want to track totals.

        Returns:
            UsageCost(raw_cost, billable_cost, margin_rate, currency)
        """
        key = f"{provider}:{model}"
        price = self.model_pricing.get(key) or self.model_pricing.get("default:llm")

        input_cost = (
            Decimal(input_tokens) / Decimal(1_000_000)
        ) * price.input_price_per_million
        output_cost = (
            Decimal(output_tokens) / Decimal(1_000_000)
        ) * price.output_price_per_million

        raw_cost = input_cost + output_cost
        raw_cost = self._round_money(raw_cost)

        margin_rate = self._select_margin_rate(raw_cost)
        billable_cost = self._round_money(raw_cost * (Decimal("1.0") + margin_rate))

        return UsageCost(
            raw_cost=raw_cost,
            billable_cost=billable_cost,
            margin_rate=margin_rate,
            currency=self.currency,
        )

    def record_llm_usage_for_org(
        self,
        *,
        org_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageCost:
        """
        Compute and accumulate cost for a given org's LLM call.

        Returns UsageCost (same as estimate_llm_cost) so the caller
        can attach it to logs, metrics, or audit trails.
        """
        usage_cost = self.estimate_llm_cost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        org_key = str(org_id)
        totals = self.org_totals.setdefault(
            org_key,
            {"raw": Decimal("0"), "billable": Decimal("0")},
        )
        totals["raw"] = self._round_money(totals["raw"] + usage_cost.raw_cost)
        totals["billable"] = self._round_money(
            totals["billable"] + usage_cost.billable_cost
        )

        return usage_cost

    def get_org_totals(self, org_id: str) -> Dict[str, Any]:
        """
        Get current aggregate totals for an org.

        Returns dict:
            {
              "raw_cost": Decimal,
              "billable_cost": Decimal,
              "currency": "USD"
            }

        If no usage yet, returns zeros.
        """
        org_key = str(org_id)
        totals = self.org_totals.get(org_key, {"raw": Decimal("0"), "billable": Decimal("0")})
        return {
            "raw_cost": self._round_money(totals["raw"]),
            "billable_cost": self._round_money(totals["billable"]),
            "currency": self.currency,
        }

    def quote_for_compute_cost(self, base_cost: Decimal) -> UsageCost:
        """
        Given a known base compute cost (e.g. aggregate infra estimate),
        compute what should be billed to the user with margins applied.

        Useful for:
          - "this Enterprise integration will cost X to run"
          - pre-purchase credit packs

        base_cost is in base currency (same as model prices).
        """
        base_cost = self._round_money(base_cost)
        margin_rate = self._select_margin_rate(base_cost)
        billable_cost = self._round_money(base_cost * (Decimal("1.0") + margin_rate))
        return UsageCost(
            raw_cost=base_cost,
            billable_cost=billable_cost,
            margin_rate=margin_rate,
            currency=self.currency,
        )

    # ------------------------------------------------------------------ #
    # Helpers for external serialization (e.g. API responses)
    # ------------------------------------------------------------------ #

    @staticmethod
    def usage_cost_to_dict(usage: UsageCost) -> Dict[str, Any]:
        """
        Convert UsageCost to a JSON-serializable dict.
        """
        return {
            "raw_cost": float(usage.raw_cost),
            "billable_cost": float(usage.billable_cost),
            "margin_rate": float(usage.margin_rate),
            "currency": usage.currency,
        }


# Global singleton used throughout backend
cost_tracker = CostTracker(settings)  # type: ignore[arg-type]
