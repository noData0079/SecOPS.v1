"""
Tree of Thought (ToT) Reasoning Module.

This module implements the Tree of Thought prompting strategy to simulate
multiple expert opinions before taking high-risk actions.
"""

from __future__ import annotations

import logging
import asyncio
from typing import List, Dict, Any, Optional

from .llm_router import get_llm_router, TaskType, LLMRouter

logger = logging.getLogger(__name__)

class TreeOfThought:
    """
    Implements Tree of Thought reasoning by simulating multiple expert opinions.
    """

    def __init__(self, llm_router: Optional[LLMRouter] = None):
        """
        Initialize the TreeOfThought engine.

        Args:
            llm_router: Optional injected router, defaults to global instance.
        """
        self.llm_router = llm_router or get_llm_router()
        self.num_experts = 5

    async def reason_with_experts(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate 5 expert opinions and synthesize a final decision.

        Args:
            prompt: The main problem or decision to analyze.
            context: Additional context for the experts.

        Returns:
            Dictionary containing the synthesis and individual expert opinions.
        """
        context_str = str(context) if context else "No additional context."

        # Define the system prompt for the experts
        # We ask the LLM to simulate 5 experts in one go or multiple calls.
        # For better isolation, we'll make parallel calls if possible, or one structured call.
        # Given the router structure, let's try to generate distinct personas.

        expert_personas = [
            "Security Expert",
            "Performance Engineer",
            "Data Privacy Officer",
            "Reliability Engineer",
            "Product Strategist"
        ]

        logger.info(f"Starting Tree of Thought reasoning for: {prompt[:50]}...")

        # We will generate opinions in parallel
        tasks = []
        for persona in expert_personas:
            tasks.append(self._get_expert_opinion(persona, prompt, context_str))

        expert_opinions = await asyncio.gather(*tasks)

        # Synthesize the results
        synthesis = await self._synthesize_opinions(prompt, expert_opinions)

        return {
            "final_decision": synthesis,
            "expert_opinions": {
                persona: opinion
                for persona, opinion in zip(expert_personas, expert_opinions)
            }
        }

    async def _get_expert_opinion(
        self,
        persona: str,
        problem: str,
        context: str
    ) -> str:
        """Get a single expert's opinion."""
        system_prompt = (
            f"You are a world-class {persona}. "
            "Analyze the following problem and provide your expert opinion, "
            "highlighting risks and recommendations specific to your domain."
        )

        full_prompt = (
            f"{system_prompt}\n\n"
            f"Problem: {problem}\n"
            f"Context: {context}\n\n"
            f"Your Opinion:"
        )

        try:
            response = await self.llm_router.generate(
                prompt=full_prompt,
                task_type=TaskType.REASONING,
                temperature=0.7
            )
            return response.content
        except Exception as e:
            logger.error(f"Failed to get opinion from {persona}: {e}")
            return f"Error obtaining opinion from {persona}: {e}"

    async def _synthesize_opinions(
        self,
        problem: str,
        opinions: List[str]
    ) -> str:
        """Synthesize multiple expert opinions into a final recommendation."""
        opinions_text = "\n\n".join(
            [f"Expert {i+1}: {op}" for i, op in enumerate(opinions)]
        )

        synthesis_prompt = (
            "You are a Chief Architect making a final decision. "
            "Review the following 5 expert opinions on the problem and provide "
            "a final, consolidated recommendation. Address any conflicts between experts.\n\n"
            f"Problem: {problem}\n\n"
            f"Expert Opinions:\n{opinions_text}\n\n"
            "Final Recommendation:"
        )

        try:
            response = await self.llm_router.generate(
                prompt=synthesis_prompt,
                task_type=TaskType.REASONING,
                temperature=0.5 # Lower temp for synthesis
            )
            return response.content
        except Exception as e:
            logger.error(f"Failed to synthesize opinions: {e}")
            return "Error synthesizing final decision."
