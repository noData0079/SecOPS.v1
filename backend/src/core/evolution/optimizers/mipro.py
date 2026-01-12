
import logging
import asyncio
from typing import List, Optional, Callable
from backend.src.core.llm.llm_router import LLMRouter, TaskType

logger = logging.getLogger(__name__)

class MiproOptimizer:
    """
    Implements a 'Lite' version of MIPRO (Multi-prompt Instruction Proposal) from EvoAgentX.
    It proposes multiple candidate instructions and selects the best one based on evaluation.
    """

    def __init__(self):
        self.router = LLMRouter()

    async def optimize(
        self,
        base_prompt: str,
        task_description: str,
        dataset: List[dict],
        evaluator_func: Callable[[str, dict], float],
        num_candidates: int = 3
    ) -> str:
        """
        Optimizes a prompt by generating candidates and evaluating them against a dataset.

        Args:
            base_prompt: The starting prompt.
            task_description: Description of the task.
            dataset: A list of examples (input/output pairs) to evaluate on.
                     Each item should be dict like {'input': ..., 'expected': ...}
            evaluator_func: A function that takes (generated_output, example) and returns a score (0.0-1.0).
            num_candidates: How many variations to generate.

        Returns:
            The best performing prompt.
        """

        # 1. Propose Candidates
        candidates = await self._propose_candidates(base_prompt, task_description, num_candidates)
        candidates.append(base_prompt) # Include the original as a baseline

        logger.info(f"MIPRO generated {len(candidates)} candidates.")

        # 2. Evaluate Candidates
        best_score = -1.0
        best_prompt = base_prompt

        for i, candidate in enumerate(candidates):
            score = await self._evaluate_candidate(candidate, dataset, evaluator_func)
            logger.info(f"Candidate {i} Score: {score:.2f}")

            if score > best_score:
                best_score = score
                best_prompt = candidate

        logger.info(f"MIPRO selected best prompt with score {best_score:.2f}")
        return best_prompt

    async def _propose_candidates(self, base_prompt: str, task_description: str, n: int) -> List[str]:
        """
        Generates N variations of the prompt using the LLM.
        """
        prompt = (
            f"You are an expert Prompt Engineer. I need you to generate {n} distinct and improved variations "
            f"of the following system prompt for a specific task.\n\n"
            f"Task: {task_description}\n"
            f"Original Prompt: {base_prompt}\n\n"
            f"The variations should try different strategies (e.g., more detailed, more concise, chain-of-thought, role-playing).\n"
            f"Output the variations in a numbered list, separated by '---'."
        )

        response = await self.router.generate(
            prompt=prompt,
            task_type=TaskType.REASONING,
            temperature=0.7
        )

        # Simple parsing of the numbered list
        candidates = []
        import re
        parts = re.split(r'\d+\.\s+', response)
        for part in parts:
            clean = part.strip().strip('---').strip()
            if clean and len(clean) > 10:
                candidates.append(clean)

        return candidates[:n]

    async def _evaluate_candidate(
        self,
        candidate_prompt: str,
        dataset: List[dict],
        evaluator_func: Callable[[str, dict], float]
    ) -> float:
        """
        Runs the candidate prompt on the dataset and returns the average score.
        """
        total_score = 0.0

        # We process sequentially here for simplicity, but could be parallelized
        for example in dataset:
            # We need to simulate the agent execution with this candidate prompt
            # For this 'Lite' version, we assume the prompt is used directly to generate output

            # Construct a prompt for the LLM using the candidate as system prompt
            system_prompt = candidate_prompt
            user_input = example.get('input', '')

            output = await self.router.generate(
                prompt=user_input,
                system_prompt=system_prompt,
                task_type=TaskType.GENERAL,
                temperature=0.0
            )

            score = evaluator_func(output, example)
            total_score += score

        return total_score / len(dataset) if dataset else 0.0
