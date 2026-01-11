"""
Tool Success Map - Learn which tools work in which contexts.

This is how autonomy becomes COMPETENT:
- Context -> Tool effectiveness mapping
- Continuous learning from outcomes
- Recommendations based on history
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SuccessRecord:
    """Record of a tool's success in a context."""
    tool: str
    context_key: str  # Normalized context identifier
    
    successes: int = 0
    failures: int = 0
    total_score: float = 0.0
    
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        total = self.successes + self.failures
        if total == 0:
            return 0.5
        return self.successes / total
    
    @property
    def avg_score(self) -> float:
        total = self.successes + self.failures
        if total == 0:
            return 50.0
        return self.total_score / total
    
    @property
    def confidence(self) -> float:
        """Confidence in this mapping (based on sample size)."""
        total = self.successes + self.failures
        return min(1.0, total / 20)  # Full confidence at 20 samples


class ToolSuccessMap:
    """
    Maps tools to contexts with effectiveness scores.
    
    Enables:
    - "This tool works well for timeout errors"
    - "That tool is bad for production"
    - Learning from every outcome
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./data/tool_success_map")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Map: (tool, context_key) -> SuccessRecord
        self.records: Dict[str, SuccessRecord] = {}
        
        self._load()
    
    def _make_key(self, tool: str, context: Dict[str, Any]) -> str:
        """Create a normalized context key."""
        # Extract key context factors
        factors = []
        
        if "error_type" in context:
            factors.append(f"error:{context['error_type']}")
        if "environment" in context:
            factors.append(f"env:{context['environment']}")
        if "service_type" in context:
            factors.append(f"svc:{context['service_type']}")
        if "severity" in context:
            factors.append(f"sev:{context['severity']}")
        
        context_key = "|".join(sorted(factors)) or "default"
        return f"{tool}@{context_key}"
    
    def record_outcome(
        self,
        tool: str,
        context: Dict[str, Any],
        success: bool,
        score: float = 0.0,
    ) -> SuccessRecord:
        """Record a tool outcome in a context."""
        key = self._make_key(tool, context)
        
        if key not in self.records:
            context_key = key.split("@")[1] if "@" in key else "default"
            self.records[key] = SuccessRecord(tool=tool, context_key=context_key)
        
        record = self.records[key]
        
        if success:
            record.successes += 1
        else:
            record.failures += 1
        
        record.total_score += score
        record.last_updated = datetime.now()
        
        self._persist()
        
        logger.debug(
            f"Recorded outcome for {tool} in {record.context_key}: "
            f"success_rate={record.success_rate:.2f}"
        )
        
        return record
    
    def get_success_rate(
        self,
        tool: str,
        context: Dict[str, Any],
    ) -> Tuple[float, float]:
        """
        Get success rate for a tool in a context.
        
        Returns:
            (success_rate, confidence)
        """
        key = self._make_key(tool, context)
        
        if key in self.records:
            record = self.records[key]
            return record.success_rate, record.confidence
        
        # Try to find similar contexts
        tool_records = [r for k, r in self.records.items() if r.tool == tool]
        if tool_records:
            # Average across all contexts for this tool
            avg_rate = sum(r.success_rate for r in tool_records) / len(tool_records)
            return avg_rate, 0.3  # Lower confidence for aggregated
        
        return 0.5, 0.0  # No data
    
    def get_recommendations(
        self,
        context: Dict[str, Any],
        available_tools: List[str],
        min_confidence: float = 0.3,
    ) -> List[Tuple[str, float, float]]:
        """
        Get tool recommendations for a context.
        
        Returns:
            List of (tool, success_rate, confidence) sorted by effectiveness
        """
        recommendations = []
        
        for tool in available_tools:
            success_rate, confidence = self.get_success_rate(tool, context)
            if confidence >= min_confidence:
                recommendations.append((tool, success_rate, confidence))
        
        # Sort by success rate (weighted by confidence)
        recommendations.sort(
            key=lambda x: x[1] * x[2],
            reverse=True
        )
        
        return recommendations
    
    def get_best_tool(
        self,
        context: Dict[str, Any],
        available_tools: List[str],
    ) -> Optional[str]:
        """Get the best tool for a context."""
        recs = self.get_recommendations(context, available_tools)
        if recs:
            return recs[0][0]
        return None
    
    def get_tool_report(self, tool: str) -> Dict[str, Any]:
        """Get detailed report for a tool."""
        tool_records = [r for r in self.records.values() if r.tool == tool]
        
        if not tool_records:
            return {"tool": tool, "data": "No records"}
        
        return {
            "tool": tool,
            "total_uses": sum(r.successes + r.failures for r in tool_records),
            "overall_success_rate": sum(r.successes for r in tool_records) / max(1, sum(r.successes + r.failures for r in tool_records)),
            "contexts": [
                {
                    "context": r.context_key,
                    "success_rate": r.success_rate,
                    "confidence": r.confidence,
                    "uses": r.successes + r.failures,
                }
                for r in tool_records
            ],
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of the success map."""
        tools = set(r.tool for r in self.records.values())
        
        return {
            "total_tools": len(tools),
            "total_records": len(self.records),
            "total_observations": sum(
                r.successes + r.failures for r in self.records.values()
            ),
            "tools": {
                tool: {
                    "contexts": len([r for r in self.records.values() if r.tool == tool]),
                    "avg_success_rate": sum(
                        r.success_rate for r in self.records.values() if r.tool == tool
                    ) / max(1, len([r for r in self.records.values() if r.tool == tool])),
                }
                for tool in tools
            },
        }
    
    def _persist(self):
        filepath = self.storage_path / "success_map.json"
        with open(filepath, "w") as f:
            json.dump({
                key: {
                    "tool": r.tool,
                    "context_key": r.context_key,
                    "successes": r.successes,
                    "failures": r.failures,
                    "total_score": r.total_score,
                    "last_updated": r.last_updated.isoformat(),
                }
                for key, r in self.records.items()
            }, f, indent=2)
    
    def _load(self):
        filepath = self.storage_path / "success_map.json"
        if not filepath.exists():
            return
        
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            for key, rd in data.items():
                self.records[key] = SuccessRecord(
                    tool=rd["tool"],
                    context_key=rd["context_key"],
                    successes=rd.get("successes", 0),
                    failures=rd.get("failures", 0),
                    total_score=rd.get("total_score", 0),
                    last_updated=datetime.fromisoformat(rd["last_updated"]),
                )
        except Exception as e:
            logger.warning(f"Failed to load success map: {e}")


# Global instance
tool_success_map = ToolSuccessMap()


__all__ = [
    "ToolSuccessMap",
    "SuccessRecord",
    "tool_success_map",
]
