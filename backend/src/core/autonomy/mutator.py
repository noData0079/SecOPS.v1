"""
Mutation Engine - Adaptive tool retry mechanism.

If a tool fails, the AI "mutates" the tool's parameters or prompt and retries.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, List

from backend.src.core.outcomes.failure_classifier import (
    FailureClassifier,
    ClassifiedFailure,
    FailureType,
    failure_classifier
)

logger = logging.getLogger(__name__)


@dataclass
class MutationResult:
    """Result of a mutation attempt."""
    should_retry: bool
    new_args: Dict[str, Any] = field(default_factory=dict)
    strategy: str = "none"  # "parameter_fix", "timeout_increase", "prompt_refine"
    reason: str = ""


class MutationEngine:
    """
    Engine for mutating tool parameters upon failure.

    Strategies:
    1. Heuristic fixes (JSON repair, type casting)
    2. Retry configuration (timeout increase, backoff)
    3. Model-based mutation (ask LLM to fix parameters)
    """

    def __init__(self, classifier: FailureClassifier = failure_classifier):
        self.classifier = classifier

    def mutate(
        self,
        tool_name: str,
        original_args: Dict[str, Any],
        error: str,
        attempt: int = 1,
        model_fn: Optional[Callable[[str], str]] = None
    ) -> MutationResult:
        """
        Suggest a mutation for a failed tool execution.
        """
        # 1. Classify failure
        classification = self.classifier.classify(error)

        if not classification.is_recoverable and attempt > 1:
             return MutationResult(should_retry=False, reason="Failure classified as non-recoverable")

        # 2. Check retry limits (skipped for VALIDATION if we have a fix strategy)
        should_retry_basic = self.classifier.should_retry(classification, attempt)

        # 3. Apply mutation strategies

        # Strategy A: Timeout/Transient - Just retry with same args (maybe delay handled by caller)
        if classification.failure_type in (FailureType.TIMEOUT, FailureType.TRANSIENT):
            if not should_retry_basic:
                return MutationResult(
                    should_retry=False,
                    reason=f"Max retries reached for {classification.failure_type}"
                )
            # For timeouts, maybe we can look for a 'timeout' arg in the tool?
            # Assuming generic structure for now.
            new_args = original_args.copy()
            if classification.failure_type == FailureType.TIMEOUT and "timeout" in new_args:
                try:
                    current_timeout = int(new_args["timeout"])
                    new_args["timeout"] = current_timeout * 2
                    return MutationResult(
                        should_retry=True,
                        new_args=new_args,
                        strategy="timeout_increase",
                        reason="Increased timeout due to timeout failure"
                    )
                except (ValueError, TypeError):
                    pass

            return MutationResult(
                should_retry=True,
                new_args=original_args,
                strategy="simple_retry",
                reason="Transient failure, retrying"
            )

        # Strategy B: Validation - Try to fix parameters
        if classification.failure_type == FailureType.VALIDATION:
            # We bypass should_retry_basic because validation errors are technically "permanent"
            # unless we mutate arguments.

            # Simple heuristic: JSON loading error?
            if "json" in error.lower() or "expecting value" in error.lower():
                # Maybe args was passed as a string instead of dict?
                # This is a bit abstract without knowing specific tool schemas.
                pass

            # Use Model if available to fix parameters
            if model_fn:
                try:
                    prompt = f"""
The tool '{tool_name}' failed with the following error:
{error}

The arguments used were:
{json.dumps(original_args, indent=2)}

Please correct the arguments to fix the error. Return ONLY the JSON of the new arguments.
"""
                    response = model_fn(prompt)
                    # Extract JSON from response
                    new_args = self._extract_json(response)
                    if new_args:
                        return MutationResult(
                            should_retry=True,
                            new_args=new_args,
                            strategy="model_correction",
                            reason="Model suggested parameter fix"
                        )
                except Exception as e:
                    logger.warning(f"Model mutation failed: {e}")

        # Default fallback
        return MutationResult(should_retry=False, reason="No mutation strategy found")

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text."""
        try:
            # Try parsing raw text first
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try finding code block
        import re
        match = re.search(r"```json(.*?)```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass

        return None

# Global instance
mutation_engine = MutationEngine()
