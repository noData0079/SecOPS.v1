from enum import Enum
from typing import Dict, Any

class RiskLevel(Enum):
    SAFE = 0       # Read-only actions (Get Logs, Scan IP)
    MODERATE = 1   # Reversible changes (Block IP temp, Isolate Host)
    CRITICAL = 2   # Destructive/Business Impact (Delete DB, Ban User, Shutdown Server)

class RiskMatrix:
    def evaluate(self, tool_name: str, params: Dict[str, Any]) -> RiskLevel:
        # 1. HARD RULES
        tool_lower = tool_name.lower()
        if "delete" in tool_lower or "shutdown" in tool_lower or "destroy" in tool_lower:
            return RiskLevel.CRITICAL

        if tool_lower == "firewall_block_ip":
            # Context matters: Blocking internal IP is critical, external is moderate
            ip = params.get('ip', '')
            if ip.startswith("192.168") or ip.startswith("10.") or ip.startswith("172."):
                return RiskLevel.CRITICAL
            return RiskLevel.MODERATE

        # Default SAFE for read-only or unknown tools,
        # but in a real system we might default to MODERATE for unknown tools.
        # For this MVP we'll stick to the prompt's logic or safe defaults.
        # Let's add a few more SAFE examples or logic.
        if tool_lower.startswith("get") or tool_lower.startswith("read") or tool_lower.startswith("scan"):
            return RiskLevel.SAFE

        # Default to MODERATE if we are unsure (safer than SAFE)
        return RiskLevel.MODERATE
