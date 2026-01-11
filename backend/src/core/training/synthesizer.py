import logging
import asyncio
from typing import List, Dict, Any
from src.core.llm.llm_router import get_llm_router, TaskType

logger = logging.getLogger(__name__)

class DeepSeekSynthesizer:
    """
    Vertical Data Synthesizer.

    Uses DeepSeek-V3 to generate synthetic high-quality training examples
    based on IT/Tech scenarios.
    """

    def __init__(self, model_name: str = "deepseek-v3"):
        self.router = get_llm_router()
        self.model_name = model_name
        self.prompt_template = """
        You are an expert IT Systems Architect and Reliability Engineer.
        Generate {count} unique, complex IT failure scenarios with their corresponding root causes and remediation steps.

        Focus on these areas:
        - Kubernetes orchestration failures
        - Database deadlocks and inconsistencies
        - BGP routing anomalies
        - Memory leaks in microservices
        - Security breaches (SQLi, XSS, RCE)

        Format the output as a JSON list of objects, each containing:
        - "scenario": Description of the failure
        - "logs": Synthetic log snippets (relevant to the failure)
        - "root_cause": Technical explanation
        - "remediation": Concrete steps to fix it
        - "code_snippet": A Python or Bash script related to the fix or the issue

        Ensure the technical details are accurate and the scenarios are diverse.
        """

    async def generate_it_scenarios(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate synthetic IT scenarios.

        Args:
            count: Number of scenarios to generate (default 10 per batch to avoid context limits)

        Returns:
            List of scenario dictionaries.
        """
        prompt = self.prompt_template.format(count=count)

        try:
            response = await self.router.generate(
                prompt=prompt,
                task_type=TaskType.REASONING,
                preferred_provider="local", # Assuming DeepSeek is served locally via Ollama
                model=self.model_name,
                temperature=0.8,
                max_tokens=4096
            )

            # Simple parsing - in production we'd use a robust JSON parser or structured output
            import json
            content = response.content

            # extract json block if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            if isinstance(data, list):
                return data
            else:
                logger.warning("Synthesizer output is not a list")
                return []

        except Exception as e:
            logger.error(f"Failed to generate scenarios: {e}")
            return []
