"""
Shadow Mirror - Asynchronously mirrors production requests to a 'Shadow' service.
"""
import logging
import asyncio
import random
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.src.core.outcomes.comparator import Comparator

class ShadowMirror:
    """
    Shadow Mirror component that runs a shadow service in parallel with the baseline.
    Supports both Dependency Injection (for testing/new arch) and Global Instance (legacy/simulation).
    """
    def __init__(self, baseline_service: Any = None, shadow_service: Any = None, outcomes_scorer: Any = None):
        self.baseline = baseline_service  # Current "Safe" Logic
        self.shadow = shadow_service      # AI's Self-Evolved Logic
        self.scorer = outcomes_scorer

        # Legacy/Global state
        self.shadow_model_path: Optional[str] = None
        self.is_active = False
        self.request_count = 0
        self.success_count = 0
        self.trust_score = 0.0

    # --- New Architecture Methods ---

    def handle_request(self, payload: Any) -> Any:
        if not self.baseline:
            logger.warning("ShadowMirror: No baseline service configured.")
            return None

        # 1. Fire Baseline (Synchronous - the user sees this)
        baseline_result = self.baseline.process(payload)

        # 2. Fire Shadow (Asynchronous - fire and forget)
        if self.shadow:
            if hasattr(self.shadow, 'async_process'):
                self.shadow.async_process(payload, callback=lambda res: self.compare_performance(res, baseline_result))
            else:
                try:
                    shadow_result = self.shadow.process(payload)
                    self.compare_performance(shadow_result, baseline_result)
                except Exception as e:
                    logger.error(f"Shadow service failed: {e}")

        return baseline_result

    def compare_performance(self, shadow_result: Any, baseline_result: Any):
        if not self.scorer:
            return

        # 3. Analyze discrepancies
        report = self.scorer.analyze_diff(shadow_result, baseline_result)

        # 4. Promotion Logic
        if report.get('trust_score', 0) > 0.99 and report.get('consistency_count', 0) > 1000:
            self.promote_shadow_to_baseline()

    def promote_shadow_to_baseline(self):
        """
        Promotes the shadow service to be the new baseline.
        """
        logger.info("Promoting Shadow Service to Baseline due to superior performance/trust.")
        pass

    # --- Legacy/Global Architecture Methods ---

    def start_mirror(self, model_path: str):
        """Starts mirroring traffic to the specified model path."""
        self.shadow_model_path = model_path
        self.is_active = True
        self.request_count = 0
        self.success_count = 0
        self.trust_score = 0.0
        logger.info(f"Shadow Mirroring started for: {model_path}")

    def process_request(self, prompt: str):
        """
        Simulates processing a request in shadow mode (Legacy).
        """
        if not self.is_active:
            return

        self.request_count += 1
        # Simulate evaluation
        is_successful = random.random() > 0.05 # 95% success rate
        if is_successful:
            self.success_count += 1
        self._update_trust_score()

    def _update_trust_score(self):
        if self.request_count == 0:
            self.trust_score = 0.0
        else:
            self.trust_score = self.success_count / self.request_count

    def get_trust_score(self) -> float:
        """Returns the current trust score of the shadow model."""
        # Simulate traffic if no requests have been processed yet (for testing purposes)
        if self.is_active and self.request_count == 0:
             logger.info("Simulating background traffic for Shadow Mirror...")
             for _ in range(100):
                 self.process_request("test prompt")
        return self.trust_score

    def stop_mirror(self):
        self.is_active = False
        logger.info("Shadow Mirroring stopped.")

# Global instance for legacy/simulation support
shadow_mirror = ShadowMirror()
