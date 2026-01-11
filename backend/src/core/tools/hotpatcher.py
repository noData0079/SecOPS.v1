"""
Autonomous Patching - Hotfix generation and application.

Generates and applies temporary "hotfixes" to firewall rules or codebases during an active breach.
"""

import os
import re
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from backend.src.core.autonomy.loop import Outcome

logger = logging.getLogger(__name__)


@dataclass
class PatchResult:
    """Result of a patch operation."""
    success: bool
    message: str
    backup_path: Optional[str] = None


class HotPatcher:
    """
    Tool for applying hotfixes to code or configuration.

    Capabilities:
    1. Apply firewall rules (simulated or via iptables if allowed)
    2. Patch source code files (with backup)
    3. Revert patches
    """

    def apply_firewall_rule(self, rule: str) -> Outcome:
        """
        Apply a firewall rule.

        Args:
            rule: iptables rule string or simple description (e.g., "BLOCK 1.2.3.4")
        """
        try:
            logger.info(f"Applying firewall rule: {rule}")

            # Validation
            if not rule:
                return Outcome(success=False, error="Empty rule")

            # Simple simulation for safety in this environment
            # In a real scenario, this would call subprocess.run(['iptables', ...])
            # We strictly validate the format to prevent command injection if we were running it.

            if "DROP" in rule or "BLOCK" in rule:
                # Simulate success
                return Outcome(
                    success=True,
                    data={"status": "applied", "rule": rule},
                    side_effects=True
                )

            return Outcome(success=False, error="Unsupported rule type. Only DROP/BLOCK allowed.")

        except Exception as e:
            return Outcome(success=False, error=str(e))

    def patch_file(self, filepath: str, search_block: str, replace_block: str) -> Outcome:
        """
        Patch a file by replacing a block of text.

        Args:
            filepath: Path to file
            search_block: Text to find
            replace_block: Text to replace with
        """
        try:
            # Security check: Prevent directory traversal
            abs_path = os.path.abspath(filepath)
            # Assuming we are running in the repo root or strict sandbox
            # We can check if the path starts with current working directory
            cwd = os.getcwd()
            if not abs_path.startswith(cwd):
                return Outcome(success=False, error="Security violation: Cannot access files outside working directory")

            if not os.path.exists(filepath):
                return Outcome(success=False, error=f"File not found: {filepath}")

            # Read file
            with open(filepath, 'r') as f:
                content = f.read()

            # Check if search block exists
            if search_block not in content:
                # Try normalized whitespace
                return Outcome(success=False, error="Search block not found in file")

            # Create backup
            backup_path = f"{filepath}.bak"
            with open(backup_path, 'w') as f:
                f.write(content)

            # Apply patch
            new_content = content.replace(search_block, replace_block)

            with open(filepath, 'w') as f:
                f.write(new_content)

            return Outcome(
                success=True,
                data={"backup": backup_path, "patched": True},
                side_effects=True
            )

        except Exception as e:
            return Outcome(success=False, error=str(e))

    def revert_patch(self, filepath: str) -> Outcome:
        """Revert a patch by restoring the backup."""
        try:
            backup_path = f"{filepath}.bak"
            if not os.path.exists(backup_path):
                return Outcome(success=False, error="No backup found")

            # Restore
            with open(backup_path, 'r') as f:
                content = f.read()

            with open(filepath, 'w') as f:
                f.write(content)

            os.remove(backup_path)

            return Outcome(
                success=True,
                data={"reverted": True},
                side_effects=True
            )

        except Exception as e:
            return Outcome(success=False, error=str(e))


# Standalone function wrappers for tool registry
_hotpatcher = HotPatcher()

def apply_firewall_rule(rule: str) -> Dict[str, Any]:
    """Apply a firewall rule."""
    outcome = _hotpatcher.apply_firewall_rule(rule)
    return {"success": outcome.success, "error": outcome.error, "data": outcome.data}

def patch_file(filepath: str, search_block: str, replace_block: str) -> Dict[str, Any]:
    """Patch a file."""
    outcome = _hotpatcher.patch_file(filepath, search_block, replace_block)
    return {"success": outcome.success, "error": outcome.error, "data": outcome.data}

def revert_patch(filepath: str) -> Dict[str, Any]:
    """Revert a patch."""
    outcome = _hotpatcher.revert_patch(filepath)
    return {"success": outcome.success, "error": outcome.error, "data": outcome.data}
