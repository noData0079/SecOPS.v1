"""
Semantic Memory - Abstracted lessons from experience.

This is "what usually works" - distilled knowledge:
- Tool effectiveness patterns
- Situational recommendations
- Abstracted playbooks
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SemanticFact:
    """A learned semantic fact."""
    fact_id: str
    category: str  # "tool_effectiveness", "pattern", "recommendation"
    content: str
    confidence: float = 0.5
    evidence_count: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def reinforce(self, amount: float = 0.1):
        """Reinforce this fact with more evidence."""
        self.confidence = min(0.99, self.confidence + amount)
        self.evidence_count += 1
        self.updated_at = datetime.now()
    
    def decay(self, amount: float = 0.05):
        """Decay confidence due to non-use or contradiction."""
        self.confidence = max(0.1, self.confidence - amount)
        self.updated_at = datetime.now()


@dataclass
class ToolPattern:
    """Pattern about tool effectiveness."""
    tool: str
    context: str  # "high_memory", "timeout", "permission_error", etc.
    effectiveness: float  # 0-1
    sample_size: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


class SemanticStore:
    """
    Semantic memory store - abstracted knowledge.
    
    Unlike episodic memory (raw incidents), semantic memory is:
    - Abstracted patterns
    - General knowledge
    - Compressed wisdom
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./data/semantic_memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory stores
        self.facts: Dict[str, SemanticFact] = {}
        self.tool_patterns: Dict[str, ToolPattern] = {}
        
        # Load existing
        self._load()
    
    def store_fact(
        self,
        fact_id: str,
        category: str,
        content: str,
        confidence: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticFact:
        """Store or update a semantic fact."""
        if fact_id in self.facts:
            fact = self.facts[fact_id]
            fact.reinforce()
        else:
            fact = SemanticFact(
                fact_id=fact_id,
                category=category,
                content=content,
                confidence=confidence,
                metadata=metadata or {},
            )
            self.facts[fact_id] = fact
        
        self._persist()
        return fact
    
    def learn_tool_pattern(
        self,
        tool: str,
        context: str,
        was_effective: bool,
    ) -> ToolPattern:
        """Learn a tool effectiveness pattern from experience."""
        key = f"{tool}|{context}"
        
        if key in self.tool_patterns:
            pattern = self.tool_patterns[key]
            # Update moving average
            old_weight = pattern.sample_size / (pattern.sample_size + 1)
            new_weight = 1 / (pattern.sample_size + 1)
            pattern.effectiveness = (
                pattern.effectiveness * old_weight +
                (1.0 if was_effective else 0.0) * new_weight
            )
            pattern.sample_size += 1
        else:
            pattern = ToolPattern(
                tool=tool,
                context=context,
                effectiveness=1.0 if was_effective else 0.0,
                sample_size=1,
            )
            self.tool_patterns[key] = pattern
        
        pattern.last_updated = datetime.now()
        self._persist()
        
        logger.info(
            f"Learned pattern: {tool} in {context} -> "
            f"effectiveness={pattern.effectiveness:.2f} (n={pattern.sample_size})"
        )
        
        return pattern
    
    def get_tool_recommendation(
        self,
        context: str,
        available_tools: List[str],
    ) -> List[tuple]:
        """Get tool recommendations for a context."""
        recommendations: List[tuple] = []
        
        for tool in available_tools:
            key = f"{tool}|{context}"
            if key in self.tool_patterns:
                pattern = self.tool_patterns[key]
                recommendations.append((tool, pattern.effectiveness, pattern.sample_size))
            else:
                # No data - use default
                recommendations.append((tool, 0.5, 0))
        
        # Sort by effectiveness (weighted by sample size)
        recommendations.sort(
            key=lambda x: x[1] * min(1, x[2] / 10),  # Weight by samples up to 10
            reverse=True
        )
        
        return recommendations
    
    def get_facts_by_category(self, category: str) -> List[SemanticFact]:
        """Get all facts in a category."""
        return [
            f for f in self.facts.values()
            if f.category == category
        ]
    
    def search_facts(self, query: str) -> List[SemanticFact]:
        """Search facts by content."""
        query_lower = query.lower()
        results = [
            f for f in self.facts.values()
            if query_lower in f.content.lower()
        ]
        return sorted(results, key=lambda f: f.confidence, reverse=True)
    
    def summarize(self) -> Dict[str, Any]:
        """Get summary of semantic memory."""
        return {
            "total_facts": len(self.facts),
            "total_patterns": len(self.tool_patterns),
            "categories": list(set(f.category for f in self.facts.values())),
            "high_confidence_facts": len([
                f for f in self.facts.values() if f.confidence > 0.8
            ]),
        }
    
    def _persist(self):
        """Persist to disk."""
        # Facts
        facts_file = self.storage_path / "facts.json"
        with open(facts_file, "w") as f:
            json.dump({
                fid: {
                    "fact_id": fact.fact_id,
                    "category": fact.category,
                    "content": fact.content,
                    "confidence": fact.confidence,
                    "evidence_count": fact.evidence_count,
                    "created_at": fact.created_at.isoformat(),
                    "updated_at": fact.updated_at.isoformat(),
                    "metadata": fact.metadata,
                }
                for fid, fact in self.facts.items()
            }, f, indent=2)
        
        # Patterns
        patterns_file = self.storage_path / "tool_patterns.json"
        with open(patterns_file, "w") as f:
            json.dump({
                key: {
                    "tool": p.tool,
                    "context": p.context,
                    "effectiveness": p.effectiveness,
                    "sample_size": p.sample_size,
                    "last_updated": p.last_updated.isoformat(),
                }
                for key, p in self.tool_patterns.items()
            }, f, indent=2)
    
    def _load(self):
        """Load from disk."""
        facts_file = self.storage_path / "facts.json"
        if facts_file.exists():
            try:
                with open(facts_file) as f:
                    data = json.load(f)
                for fid, fd in data.items():
                    self.facts[fid] = SemanticFact(
                        fact_id=fd["fact_id"],
                        category=fd["category"],
                        content=fd["content"],
                        confidence=fd["confidence"],
                        evidence_count=fd.get("evidence_count", 1),
                        created_at=datetime.fromisoformat(fd["created_at"]),
                        updated_at=datetime.fromisoformat(fd["updated_at"]),
                        metadata=fd.get("metadata", {}),
                    )
            except Exception as e:
                logger.warning(f"Failed to load facts: {e}")
        
        patterns_file = self.storage_path / "tool_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    data = json.load(f)
                for key, pd in data.items():
                    self.tool_patterns[key] = ToolPattern(
                        tool=pd["tool"],
                        context=pd["context"],
                        effectiveness=pd["effectiveness"],
                        sample_size=pd.get("sample_size", 1),
                        last_updated=datetime.fromisoformat(pd["last_updated"]),
                    )
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")


__all__ = [
    "SemanticStore",
    "SemanticFact",
    "ToolPattern",
]
