"""
The Swarm Orchestrator - Multi-Agent Specialization.

A single "TSM99" model is a generalist. To replace a team, you need a Swarm.
This Orchestrator delegates to "Sub-Agents" with specific system personas:
- Forensic Agent: Semantic store analysis & timeline reconstruction.
- Policy Auditor: "Red Team" for EconomicGovernor.
- Tool Architect: Generates new Python scripts for missing tools.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import asyncio

from core.llm.local_provider import LocalLLMProvider, local_llm
from core.memory.semantic_store import SemanticStore, semantic_store as global_semantic_store
from core.economics.governor import EconomicGovernor, economic_governor
from core.tools.tool_success_map import ToolSuccessMap, tool_success_map

logger = logging.getLogger(__name__)

@dataclass
class AgentPersona:
    """Definition of a sub-agent persona."""
    name: str
    description: str
    system_prompt_template: str
    tools: List[str] = field(default_factory=list)

class SwarmOrchestrator:
    """
    Orchestrates a swarm of specialized sub-agents.
    delegates tasks based on context or explicit request.
    """

    def __init__(
        self,
        provider: Optional[LocalLLMProvider] = None,
        semantic_store: Optional[SemanticStore] = None,
        governor: Optional[EconomicGovernor] = None,
        success_map: Optional[ToolSuccessMap] = None
    ):
        self.provider = provider or local_llm
        self.semantic_store = semantic_store or global_semantic_store
        self.governor = governor or economic_governor
        self.success_map = success_map or tool_success_map

        self.personas = self._initialize_personas()

    def _initialize_personas(self) -> Dict[str, AgentPersona]:
        return {
            "forensic": AgentPersona(
                name="Forensic Agent",
                description="Specialized in semantic_store.py analysis and timeline reconstruction.",
                system_prompt_template="""You are the Forensic Agent.
Your Goal: Analyze the Semantic Store and reconstruct timelines of incidents.
You have deep access to historical facts and patterns.

CONTEXT:
{context}

INSTRUCTIONS:
1. Analyze the provided logs or query.
2. Correlate with known Semantic Facts.
3. Reconstruct the sequence of events (Timeline).
4. Output a clear, factual report.
"""
            ),
            "auditor": AgentPersona(
                name="Policy Auditor",
                description="A 'Red Team' agent that finds bypasses in EconomicGovernor.",
                system_prompt_template="""You are the Policy Auditor (Red Team).
Your Goal: Critically analyze the Economic Governor and current plans to find security/cost bypasses.
You are skeptical and thorough.

GOVERNOR STATE:
{context}

INSTRUCTIONS:
1. Review the proposed action or state.
2. Attempt to find loopholes in the budget or safety logic.
3. Simulate how a malicious actor might exploit this.
4. Report vulnerabilities or confirm safety.
"""
            ),
            "architect": AgentPersona(
                name="Tool Architect",
                description="Generative agent that writes new Python scripts/wrappers.",
                system_prompt_template="""You are the Tool Architect.
Your Goal: Write new Python scripts/wrappers for tools not in the current ToolSuccessMap.
You generate production-ready, safe Python code.

EXISTING TOOLS:
{context}

INSTRUCTIONS:
1. Understand the missing capability.
2. Write a Python function/script to bridge the gap.
3. Ensure the code is safe, robust, and follows patterns.
4. Output the code block enclosed in ```python ... ```.
"""
            )
        }

    async def delegate(
        self,
        persona_name: str,
        task: str,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Delegate a task to a specific sub-agent.
        """
        if persona_name not in self.personas:
            raise ValueError(f"Unknown persona: {persona_name}")

        persona = self.personas[persona_name]
        context_str = self._build_context(persona_name, extra_context)

        system_prompt = persona.system_prompt_template.format(context=context_str)

        logger.info(f"Delegating task to {persona.name}")

        # Call the provider
        response = await self.provider.generate(
            prompt=task,
            system_prompt=system_prompt,
            temperature=0.3 if persona_name == "architect" else 0.1 # Architect needs a bit of creativity? Or 0.1 for precision?
        )

        return response

    def _build_context(self, persona_name: str, extra_context: Optional[Dict[str, Any]]) -> str:
        """Gather context for the specific persona."""
        extra = extra_context or {}

        if persona_name == "forensic":
            # Fetch relevant facts from semantic store if query is present?
            # For now, dump summary or recent facts.
            # In a real scenario, we'd do RAG here.
            # Let's just summarize the store.
            summary = self.semantic_store.summarize()
            # Maybe get recent facts?
            recent_facts = list(self.semantic_store.facts.values())[-5:]
            facts_str = "\n".join([f"- [{f.category}] {f.content}" for f in recent_facts])
            return f"Store Summary: {summary}\nRecent Facts:\n{facts_str}\nExtra: {extra}"

        elif persona_name == "auditor":
            # Get budget status for relevant tenant?
            tenant_id = extra.get("tenant_id", "default_tenant")
            budget_health = self.governor.check_budget_health(tenant_id)
            return f"Budget Health ({tenant_id}): {budget_health}\nExtra: {extra}"

        elif persona_name == "architect":
            # List existing tools from success map or registry
            # We need the registry really, but success map has keys.
            tools_summary = self.success_map.get_summary()
            return f"Tool Success Map Summary: {tools_summary}\nExtra: {extra}"

        return str(extra)

    async def route_request(self, prompt: str, tool_registry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent routing of the request.
        For use with AutonomyLoop model_fn.
        """
        # 1. Analyze intent (simple keyword heuristic for now, or lightweight LLM call)
        # To avoid infinite recursion or overhead, let's use keywords/heuristics.

        prompt_lower = prompt.lower()

        if any(k in prompt_lower for k in ["analyze semantic store", "reconstruct timeline", "semantic store"]):
            target = "forensic"
        elif any(k in prompt_lower for k in ["audit", "bypass", "budget check", "economic governor"]):
            target = "auditor"
        elif any(k in prompt_lower for k in ["write a tool", "new python script", "create tool", "tool architect"]):
            target = "architect"
        else:
            target = "generalist"

        if target == "generalist":
            # Fallback to standard provider behavior (simulated)
            # Actually, we need to return a JSON action for AutonomyLoop
            # So we ask the Generalist to produce JSON.
            system_prompt = "You are an autonomous infrastructure agent. Choose the next action. Output JSON only."
            response = await self.provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=True
            )
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from generalist: {response}")
                return {"tool": "error", "args": {"msg": "Invalid JSON"}}

        # If delegated:
        response_text = await self.delegate(target, prompt, extra_context={"tools": list(tool_registry.keys())})

        # We need to wrap the agent's text response into a Tool Action that AutonomyLoop understands.
        # e.g. using a "log_message" tool or similar to report the findings.
        # Or if the Architect wrote code, we might want to save it.

        if target == "architect":
            # Extract code?
            pass

        # For now, we wrap the text result in a 'consult_response' or just 'log' action
        # assuming 'log' tool exists. If not, we might need a meta-action.

        # Let's assume we return a specialized action that the loop handles?
        # Or just use a standard tool like 'echo' or 'log'.

        return {
            "tool": "report_agent_outcome",
            "args": {
                "agent": target,
                "content": response_text
            }
        }

# Global instance
swarm = SwarmOrchestrator()
