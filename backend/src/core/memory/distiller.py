"""
Knowledge Distiller - Sleeps and compresses episodic memories into semantic rules.

At "midnight" (or scheduled time), this component:
1. Reads resolved incidents from EpisodicStore
2. Identifies patterns (same tool used, similar outcome)
3. "Compresses" them into a SemanticFact (Rule of Thumb)
4. Updates SemanticStore
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter

from .episodic_store import EpisodicStore
from .semantic_store import SemanticStore

logger = logging.getLogger(__name__)


class KnowledgeDistiller:
    def __init__(self, episodic_store: EpisodicStore, semantic_store: SemanticStore):
        self.episodic_store = episodic_store
        self.semantic_store = semantic_store

    def distill_daily(self):
        """
        Run the daily distillation process.
        Iterate over recent resolved incidents and extract patterns.
        """
        logger.info("Starting daily knowledge distillation...")

        # 1. Gather recent data
        # In a real system, we'd filter by timestamp. For now, we take all from cache/storage.
        # Accessing private storage path for simulation purposes
        all_incidents = []
        for filepath in self.episodic_store.storage_path.glob("*.json"):
            memory = self.episodic_store._load_file(filepath)
            if memory and memory.final_outcome == "resolved":
                all_incidents.append(memory)

        logger.info(f"Found {len(all_incidents)} resolved incidents to analyze.")

        if not all_incidents:
            return

        # 2. Pattern Matching: Tool Effectiveness
        # Count tool usage and success in resolved incidents
        tool_stats = {}

        for incident in all_incidents:
            for episode in incident.episodes:
                if not episode.action_taken:
                    continue

                tool_name = episode.action_taken.get("tool")
                if not tool_name:
                    continue

                success = episode.outcome.get("success", False) if episode.outcome else False

                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {"success": 0, "total": 0}

                tool_stats[tool_name]["total"] += 1
                if success:
                    tool_stats[tool_name]["success"] += 1

        # 3. Create "Rules of Thumb" (Semantic Facts)
        for tool, stats in tool_stats.items():
            success_rate = stats["success"] / stats["total"]

            # If a tool is highly effective (> 80%), create a rule
            if success_rate > 0.8 and stats["total"] >= 3:
                fact_content = f"Tool '{tool}' is highly effective ({success_rate:.0%}) for resolving incidents."
                self.semantic_store.store_fact(
                    fact_id=f"rule_tool_{tool}_effectiveness",
                    category="tool_effectiveness",
                    content=fact_content,
                    confidence=0.85 + (min(stats["total"], 10) * 0.01) # Boost confidence with sample size
                )
                logger.info(f"Distilled rule: {fact_content}")

            # If a tool is ineffective (< 20%), create a warning
            elif success_rate < 0.2 and stats["total"] >= 3:
                fact_content = f"Tool '{tool}' rarely works ({success_rate:.0%}). Avoid unless necessary."
                self.semantic_store.store_fact(
                    fact_id=f"rule_tool_{tool}_ineffective",
                    category="tool_effectiveness",
                    content=fact_content,
                    confidence=0.8
                )
                logger.info(f"Distilled rule: {fact_content}")

        # 4. Pattern Matching: Sequence Analysis (Simple Bigrams)
        # Check if Action A is typically followed by Action B in resolved incidents
        sequences = []
        for incident in all_incidents:
            tools = [e.action_taken.get("tool") for e in incident.episodes if e.action_taken and e.action_taken.get("tool")]
            if len(tools) >= 2:
                for i in range(len(tools) - 1):
                    sequences.append((tools[i], tools[i+1]))

        seq_counts = Counter(sequences)
        for (t1, t2), count in seq_counts.items():
            if count >= 3:
                fact_content = f"After using '{t1}', consider using '{t2}'. This sequence appeared {count} times in resolved incidents."
                self.semantic_store.store_fact(
                    fact_id=f"rule_seq_{t1}_{t2}",
                    category="recommendation",
                    content=fact_content,
                    confidence=0.7
                )
                logger.info(f"Distilled rule: {fact_content}")

        logger.info("Daily distillation complete.")
