"""
Dynamic Tool Synthesis Engine ("MacGyver" Layer)

Purpose: Generates new tool scripts on-the-fly when existing tools are insufficient.
Constraint: All generated tools must pass strict sandbox validation and receive Human Approval
before being added to the active library.
"""

import ast
import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Constants
APPROVALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "approvals")
SANDBOX_BLACKLIST = ["os.system", "subprocess.call", "subprocess.Popen", "eval", "exec"]

@dataclass
class ToolProposal:
    tool_name: str
    purpose: str
    code: str
    risk_score: float
    timestamp: str
    status: str = "WAIT_APPROVAL"
    signature: Optional[str] = None

class SandboxValidator:
    """
    Static analysis sandbox to verify generated code safety.
    """
    @staticmethod
    def validate(code: str) -> bool:
        """
        Parses code into AST and checks for blacklisted nodes/calls.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            logger.error("Generated code has syntax errors.")
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec"]:
                        logger.warning(f"Sandbox Violation: {node.func.id} usage detected.")
                        return False
                elif isinstance(node.func, ast.Attribute):
                    # Check for os.system, etc.
                    # This is a simplified check.
                    if hasattr(node.func.value, "id"):
                         module = node.func.value.id
                         method = node.func.attr
                         call_sig = f"{module}.{method}"
                         # Simple string match for blacklist
                         for banned in SANDBOX_BLACKLIST:
                             if banned in call_sig:
                                 logger.warning(f"Sandbox Violation: {call_sig} usage detected.")
                                 return False
        return True

class ToolSynthesizer:
    """
    The MacGyver Engine. Synthesizes tools and queues them for approval.
    """
    def __init__(self):
        self.approvals_path = APPROVALS_DIR
        os.makedirs(self.approvals_path, exist_ok=True)

    def generate_tool_candidate(self, tool_name: str, purpose: str, simulated_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate the LLM generation of a tool.
        In a real system, this would call the DeepSeek model with a prompt.
        For this implementation, we accept `simulated_code` or generate a stub.
        """
        if not simulated_code:
            # Stub for "MacGyver" generation
            simulated_code = f"""
def {tool_name}_handler(args):
    # Auto-generated tool for: {purpose}
    print(f"Executing {tool_name} with {{args}}")
    return {{ "status": "success", "data": "processed" }}
"""

        logger.info(f"Synthesized code for {tool_name}. Validating...")

        # 1. Sandbox Verification
        if not SandboxValidator.validate(simulated_code):
            return {"status": "rejected", "reason": "Sandbox validation failed"}

        # 2. Package Proposal
        proposal = ToolProposal(
            tool_name=tool_name,
            purpose=purpose,
            code=simulated_code,
            risk_score=0.8, # Synthesized tools are inherently high risk
            timestamp=datetime.utcnow().isoformat()
        )

        # 3. Submit for Approval (Write to file)
        self._submit_for_approval(proposal)

        return {"status": "wait_approval", "proposal_id": f"proposal_{tool_name}"}

    def _submit_for_approval(self, proposal: ToolProposal):
        """Writes the proposal to the approvals directory."""
        filename = f"tool_request_{proposal.tool_name}_{int(time.time())}.json"
        filepath = os.path.join(self.approvals_path, filename)

        with open(filepath, "w") as f:
            json.dump(asdict(proposal), f, indent=2)

        logger.info(f"Tool proposal written to {filepath}")
