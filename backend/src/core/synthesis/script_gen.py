"""
Script Generator - Writes new tools on the fly.
"""
from typing import Optional
from core.audit.immutable_trace import immutable_trace
from core.security.kill_switch import kill_switch

class ScriptGenerator:
    """
    Generates Python scripts for new tools based on specifications.
    """
    def generate_tool(self, spec: str) -> str:
        """
        Generates code for a new tool.

        Args:
            spec: The specification for the tool.

        Returns:
            The generated Python code as a string.
        """
        if kill_switch.is_active():
            raise RuntimeError("KILL SWITCH ACTIVE: Evolution frozen.")

        # Simulating generation for now
        # In a real scenario, this would call an LLM
        code = f"# Generated tool from spec: {spec}\n\ndef run():\n    print('Running generated tool')"

        # Log to immutable ledger
        immutable_trace.log_trace(
            action="generate_tool",
            before_content=None,
            after_content=code,
            metadata={"spec": spec}
        )

        return code

    def modify_tool(self, original_code: str, spec: str) -> str:
        """
        Modifies an existing tool code.

        Args:
            original_code: The existing code.
            spec: Modification instructions.

        Returns:
            The modified code.
        """
        if kill_switch.is_active():
            raise RuntimeError("KILL SWITCH ACTIVE: Evolution frozen.")

        # Simulating modification
        new_code = original_code + f"\n# Modified per spec: {spec}"

        # Log to immutable ledger
        immutable_trace.log_trace(
            action="modify_tool",
            before_content=original_code,
            after_content=new_code,
            metadata={"spec": spec}
        )

        return new_code
