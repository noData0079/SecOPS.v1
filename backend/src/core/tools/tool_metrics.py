"""
Tool Metrics - Track tool usage and performance.

Enables:
- Dynamic risk scoring
- Tool blacklisting after failures
- Cooldown enforcement
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolMetric:
    """Metrics for a single tool."""
    tool: str
    
    # Usage counts
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    
    # Timing
    total_execution_time_ms: int = 0
    last_used: Optional[datetime] = None
    
    # Failure tracking
    consecutive_failures: int = 0
    is_blacklisted: bool = False
    blacklisted_until: Optional[datetime] = None
    
    # Cooldown
    current_cooldown_seconds: int = 0
    cooldown_until: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_uses == 0:
            return 0.5
        return self.successful_uses / self.total_uses
    
    @property
    def avg_execution_time_ms(self) -> float:
        if self.total_uses == 0:
            return 0
        return self.total_execution_time_ms / self.total_uses
    
    @property
    def is_available(self) -> bool:
        """Check if tool is currently available."""
        now = datetime.now()
        
        if self.is_blacklisted:
            if self.blacklisted_until and now > self.blacklisted_until:
                self.is_blacklisted = False
            else:
                return False
        
        if self.cooldown_until and now < self.cooldown_until:
            return False
        
        return True


class ToolMetrics:
    """
    Track and manage tool metrics.
    
    Features:
    - Usage tracking
    - Automatic blacklisting after failures
    - Cooldown management
    - Performance analysis
    """
    
    def __init__(self):
        self.metrics: Dict[str, ToolMetric] = {}
        
        # Configuration
        self.config = {
            "blacklist_threshold": 3,  # Consecutive failures to blacklist
            "blacklist_duration_hours": 1,
            "cooldown_base_seconds": 5,
            "cooldown_multiplier": 2,  # Exponential backoff
            "cooldown_max_seconds": 300,
        }
    
    def get_metric(self, tool: str) -> ToolMetric:
        """Get or create metric for a tool."""
        if tool not in self.metrics:
            self.metrics[tool] = ToolMetric(tool=tool)
        return self.metrics[tool]
    
    def record_use(
        self,
        tool: str,
        success: bool,
        execution_time_ms: int = 0,
    ) -> ToolMetric:
        """Record a tool use."""
        metric = self.get_metric(tool)
        
        metric.total_uses += 1
        metric.total_execution_time_ms += execution_time_ms
        metric.last_used = datetime.now()
        
        if success:
            metric.successful_uses += 1
            metric.consecutive_failures = 0
            metric.current_cooldown_seconds = 0
        else:
            metric.failed_uses += 1
            metric.consecutive_failures += 1
            
            # Apply cooldown
            self._apply_cooldown(metric)
            
            # Check for blacklist
            if metric.consecutive_failures >= self.config["blacklist_threshold"]:
                self._blacklist(metric)
        
        return metric
    
    def _apply_cooldown(self, metric: ToolMetric):
        """Apply exponential backoff cooldown."""
        if metric.consecutive_failures == 0:
            metric.current_cooldown_seconds = 0
            metric.cooldown_until = None
            return
        
        cooldown = min(
            self.config["cooldown_base_seconds"] * (
                self.config["cooldown_multiplier"] ** (metric.consecutive_failures - 1)
            ),
            self.config["cooldown_max_seconds"]
        )
        
        metric.current_cooldown_seconds = int(cooldown)
        metric.cooldown_until = datetime.now() + timedelta(seconds=cooldown)
        
        logger.info(f"Tool {metric.tool} cooldown: {cooldown}s")
    
    def _blacklist(self, metric: ToolMetric):
        """Blacklist a tool."""
        metric.is_blacklisted = True
        metric.blacklisted_until = datetime.now() + timedelta(
            hours=self.config["blacklist_duration_hours"]
        )
        logger.warning(
            f"Tool {metric.tool} blacklisted until {metric.blacklisted_until}"
        )
    
    def unblacklist(self, tool: str):
        """Manually unblacklist a tool."""
        if tool in self.metrics:
            metric = self.metrics[tool]
            metric.is_blacklisted = False
            metric.blacklisted_until = None
            metric.consecutive_failures = 0
            logger.info(f"Tool {tool} unblacklisted")
    
    def is_available(self, tool: str) -> tuple[bool, str]:
        """Check if a tool is available."""
        metric = self.get_metric(tool)
        
        if metric.is_blacklisted:
            return False, f"Blacklisted until {metric.blacklisted_until}"
        
        if metric.cooldown_until and datetime.now() < metric.cooldown_until:
            remaining = (metric.cooldown_until - datetime.now()).seconds
            return False, f"Cooldown: {remaining}s remaining"
        
        return True, "Available"
    
    def get_available_tools(self, tools: List[str]) -> List[str]:
        """Filter to only available tools."""
        return [t for t in tools if self.is_available(t)[0]]
    
    def get_rankings(self) -> List[tuple]:
        """Get tools ranked by success rate."""
        rankings = [
            (m.tool, m.success_rate, m.total_uses)
            for m in self.metrics.values()
        ]
        return sorted(rankings, key=lambda x: (x[1], x[2]), reverse=True)
    
    def get_report(self) -> Dict[str, Any]:
        """Get full metrics report."""
        return {
            "tools": [
                {
                    "tool": m.tool,
                    "total_uses": m.total_uses,
                    "success_rate": m.success_rate,
                    "avg_execution_time_ms": m.avg_execution_time_ms,
                    "is_available": m.is_available,
                    "is_blacklisted": m.is_blacklisted,
                    "consecutive_failures": m.consecutive_failures,
                }
                for m in self.metrics.values()
            ],
            "blacklisted_count": len([m for m in self.metrics.values() if m.is_blacklisted]),
            "total_uses": sum(m.total_uses for m in self.metrics.values()),
        }


# Global instance
tool_metrics = ToolMetrics()


__all__ = [
    "ToolMetrics",
    "ToolMetric",
    "tool_metrics",
]
