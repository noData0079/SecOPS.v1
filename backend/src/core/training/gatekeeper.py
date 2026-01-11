import logging
import asyncio
from typing import List, Dict, Any
from src.core.llm.llm_router import get_llm_router, TaskType

logger = logging.getLogger(__name__)

class DataCleaner:
    """
    The Quality Gatekeeper.

    Filters IT data using a small, fast model (like Phi-3) to ensure
    Garbage In = Blocked.
    """

    def __init__(self, model_name: str = "phi3"):
        self.router = get_llm_router()
        self.model_name = model_name

    async def filter_garbage(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out low-quality data.

        Args:
            data: List of raw scenarios.

        Returns:
            List of clean scenarios.
        """
        clean_data = []
        for item in data:
            score = await self._score_item(item)
            if score >= 7.0: # Threshold
                clean_data.append(item)
            else:
                logger.info(f"Rejected item with score {score}: {item.get('scenario')[:50]}...")

        return clean_data

    async def _score_item(self, item: Dict[str, Any]) -> float:
        """Score a single item using the gatekeeper model."""
        prompt = f"""
        Rate the following IT scenario for technical accuracy, clarity, and relevance to IT operations on a scale of 0 to 10.

        Scenario: {item.get('scenario')}
        Root Cause: {item.get('root_cause')}
        Remediation: {item.get('remediation')}
        Code: {item.get('code_snippet')}

        Return ONLY the numeric score (e.g., 8.5).
        """

        try:
            response = await self.router.generate(
                prompt=prompt,
                task_type=TaskType.GENERAL,
                preferred_provider="local",
                model=self.model_name,
                temperature=0.1,
                max_tokens=10
            )

            score_str = response.content.strip()
            # extract number
            import re
            match = re.search(r"(\d+(\.\d+)?)", score_str)
            if match:
                return float(match.group(1))
            return 0.0

        except Exception as e:
            logger.error(f"Gatekeeper scoring failed: {e}")
            return 0.0
