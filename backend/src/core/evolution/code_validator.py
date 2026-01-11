"""
Code Validator - Formal Verification

Ensures self-written code is safe and valid before execution.
"""

import ast
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class CodeValidator:
    """
    Performs static analysis and security checks on generated code.
    """

    def __init__(self):
        # Blacklist of dangerous functions/modules
        self.blacklist = {
            "os.system", "subprocess.Popen", "subprocess.call", "subprocess.run",
            "eval", "exec", "shutil.rmtree", "socket", "requests"
        }
        # Exceptions for authorized modules can be handled via strict allowlists elsewhere

    def check_safety(self, source_code: str) -> bool:
        """
        Validates source code against safety rules.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Syntax Error in generated code: {e}")
            return False

        # 1. Check imports and calls against blacklist
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if self._is_blacklisted(alias.name):
                        logger.warning(f"Validation Failed: Blacklisted import '{alias.name}'")
                        return False
            elif isinstance(node, ast.ImportFrom):
                if self._is_blacklisted(node.module):
                    logger.warning(f"Validation Failed: Blacklisted import from '{node.module}'")
                    return False
            elif isinstance(node, ast.Call):
                # Simple check for function calls
                func_name = self._get_func_name(node.func)
                if func_name and self._is_blacklisted(func_name):
                    logger.warning(f"Validation Failed: Blacklisted function call '{func_name}'")
                    return False

        logger.info("Code safety check passed.")
        return True

    def _is_blacklisted(self, name: str) -> bool:
        """Checks if a name matches the blacklist."""
        if not name:
            return False
        if name in self.blacklist:
            return True
        # Check sub-modules (e.g. os.path is okay, but os.system is not?)
        # For strictness, if 'os' is blacklisted, everything is.
        # But we might want 'os.path'.
        # For this MVP, we match exact strings in blacklist or if it starts with one + dot
        for b in self.blacklist:
             if name == b or name.startswith(b + "."):
                 return True
        return False

    def _get_func_name(self, node) -> str:
        """Helper to get function name from AST Call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}"
        return ""
