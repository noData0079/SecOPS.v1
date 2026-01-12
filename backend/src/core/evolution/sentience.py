
import logging
from typing import Optional, List, Callable
from backend.src.core.evolution.optimizers.text_gradient import TextGradientOptimizer
from backend.src.core.evolution.optimizers.mipro import MiproOptimizer

logger = logging.getLogger(__name__)

class SentienceEngine:
    """
    Orchestrates the self-evolution process by selecting the appropriate optimization strategy
    (TextGrad or MIPRO) based on the context and available data.
    """

    def __init__(self):
        self.text_grad = TextGradientOptimizer()
        self.mipro = MiproOptimizer()

    async def evolve_prompt(
        self,
        current_prompt: str,
        task_description: str,
        recent_failures: Optional[List[dict]] = None,
        dataset: Optional[List[dict]] = None,
        evaluator_func: Optional[Callable[[str, dict], float]] = None
    ) -> str:
        """
        Evolves the prompt to improve performance.

        Strategy:
        1. If we have a dataset and evaluator, use MIPRO for broad exploration and robust optimization.
        2. If we only have recent failures (feedback), use TextGrad for targeted repair.
        3. If neither, return original prompt (or use TextGrad with self-reflection if implemented).
        """

        if dataset and evaluator_func and len(dataset) > 0:
            logger.info("SentienceEngine: Selecting MIPRO for optimization (Dataset available).")
            return await self.mipro.optimize(
                base_prompt=current_prompt,
                task_description=task_description,
                dataset=dataset,
                evaluator_func=evaluator_func
            )

        elif recent_failures and len(recent_failures) > 0:
            logger.info("SentienceEngine: Selecting TextGrad for optimization (Feedback available).")
            # Use the most recent failure for gradient calculation
            last_failure = recent_failures[-1]
            return await self.text_grad.optimize(
                current_prompt=current_prompt,
                task_description=task_description,
                test_input=last_failure.get('input', ''),
                test_output=last_failure.get('output', ''),
                expected_output_description=last_failure.get('expected', 'Correct behavior')
            )

        else:
            logger.warning("SentienceEngine: No data or feedback provided. Skipping optimization.")
            return current_prompt
