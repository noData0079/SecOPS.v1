
import logging
from typing import Optional, Dict, List, Any
from backend.src.core.llm.llm_router import LLMRouter, TaskType

logger = logging.getLogger(__name__)

# Constants adapted from EvoAgentX
OPTIMIZER_SYSTEM_PROMPT = (
    "You are part of an optimization system that improves text (i.e., variable). "
    "You will be asked to creatively and critically improve instruction prompts or system prompts. "
    "You will receive some feedback, and use the feedback to improve the variable. "
    "The feedback may be noisy, identify what is important and what is correct. "
    "Pay attention to the role description of the variable, and the context in which it is used. "
    "This is very important: You MUST give your response by sending the improved variable between <new_variable> {{improved variable}} </new_variable> tags. "
    "The text you send between the tags will directly replace the variable."
)

GENERAL_LOSS_PROMPT = (
    "Evaluate the following response to a task, comparing it to the expected outcome or criteria."
    "Your evaluation should cover the following points in a concise list of bullet points:\n"
    "- Correctness: Does the response correctly address the task? If not, what is missing or incorrect?\n"
    "- Completeness: Does the response cover all aspects of the task?\n"
    "- Clarity: Is the response clear and easy to understand?\n"
    "- Relevance: Is the response focused on the task?\n"
    "- Suggestions: How can the response be improved or clarified?"
)

class TextGradientOptimizer:
    """
    Implements a 'Lite' version of Textual Gradient Descent (TextGrad) from EvoAgentX.
    Instead of full backpropagation through a computation graph, it uses a simplified
    Critic -> Update loop powered by LLMs.
    """

    def __init__(self):
        self.router = LLMRouter()

    async def optimize(
        self,
        current_prompt: str,
        task_description: str,
        test_input: str,
        test_output: str,
        expected_output_description: str = "A correct and high-quality response"
    ) -> str:
        """
        Optimizes a prompt based on a single failure/feedback instance.

        Args:
            current_prompt: The system prompt or instruction being optimized.
            task_description: What the agent was supposed to do.
            test_input: The input that caused the issue.
            test_output: The actual output produced by the agent.
            expected_output_description: Description of what was expected.

        Returns:
            The optimized prompt.
        """

        # 1. Compute 'Gradient' (Critique)
        critique = await self._compute_gradient(
            task_description, test_input, test_output, expected_output_description
        )
        logger.info(f"Computed TextGrad Critique: {critique}")

        # 2. Update Step (Apply Gradient)
        new_prompt = await self._apply_gradient(current_prompt, critique)

        return new_prompt

    async def _compute_gradient(
        self,
        task_description: str,
        test_input: str,
        test_output: str,
        expected_output_description: str
    ) -> str:
        """
        Generates a critique of the output, acting as the 'loss function'.
        """
        prompt = (
            f"{GENERAL_LOSS_PROMPT}\n\n"
            f"Task Description: {task_description}\n"
            f"Input: {test_input}\n"
            f"Actual Output: {test_output}\n"
            f"Expected Criteria: {expected_output_description}\n"
        )

        response = await self.router.generate(
            prompt=prompt,
            task_type=TaskType.REASONING,
            temperature=0.1
        )
        return response

    async def _apply_gradient(self, current_prompt: str, critique: str) -> str:
        """
        Updates the prompt based on the critique.
        """
        prompt = (
            f"{OPTIMIZER_SYSTEM_PROMPT}\n\n"
            f"Current Variable (Prompt): {current_prompt}\n"
            f"Feedback (Gradient): {critique}\n"
        )

        response = await self.router.generate(
            prompt=prompt,
            task_type=TaskType.CODE, # Using Code Gen for strict formatting
            temperature=0.2
        )

        # Extract the new variable
        import re
        match = re.search(r"<new_variable>(.*?)</new_variable>", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            logger.warning("Could not extract new variable from optimizer response. Returning original.")
            return current_prompt
