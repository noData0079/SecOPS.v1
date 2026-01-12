"""
Autonomy Loop - The Core Agent Execution Cycle

OBSERVATION → MODEL → POLICY → TOOLS → OUTCOME → REPLAY

The model is NEVER asked questions.
It is ORDERED to act.
This is real autonomy.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Any, Callable, Dict, Optional, List

from .policy_engine import (
    PolicyEngine,
    PolicyDecision,
    AgentState,
)
from core.autonomy.gatekeeper import Gatekeeper, ApprovalQueueDB
from core.safety.risk_matrix import RiskMatrix
from core.security.kill_switch import kill_switch

logger = logging.getLogger(__name__)


@dataclass
class Observation:
    """Input observation for the agent."""
    content: str
    source: str  # "logs", "metrics", "events", "alert"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Outcome:
    """Result of executing a tool."""
    success: bool
    error: Optional[str] = None
    side_effects: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0


@dataclass
class ReplayEntry:
    """Entry for the replay buffer."""
    incident_id: str
    observation: str
    action: Dict[str, Any]
    outcome: Dict[str, Any]
    resolution_time_seconds: int
    timestamp: datetime = field(default_factory=datetime.now)


class AutonomyLoop:
    """
    Main Autonomy Loop implementation.
    
    The loop:
    1. Observes (logs/metrics/events)
    2. Model decides (DeepSeek-Coder 6.7B)
    3. Policy checks (deterministic rules)
    4. Tool executes (sandboxed)
    5. Outcome recorded
    6. Replay stored (learning without GPUs)
    """
    
    def __init__(
        self,
        policy_engine: PolicyEngine,
        model_fn: Callable[[str, Dict[str, Any]], Dict[str, Any]],
        tool_executor: Callable[[str, Dict[str, Any]], Outcome],
        replay_store_path: Optional[Path] = None,
        approvals_path: Optional[Path] = None,
    ):
        self.policy_engine = policy_engine
        self.model_fn = model_fn  # Function that calls the model
        self.tool_executor = tool_executor  # Function that executes tools
        self.replay_store_path = replay_store_path or Path("./replay_buffer")
        self.replay_store_path.mkdir(exist_ok=True)
        self.approvals_path = approvals_path or Path("backend/approvals")
        self.approvals_path.mkdir(exist_ok=True, parents=True)
        
        self.state = AgentState()
        self.replay_buffer: List[ReplayEntry] = []
        self.incident_id: Optional[str] = None
        self.start_time: Optional[datetime] = None

        # Initialize Gatekeeper
        # Use default path (backend/data/approvals_queue) to match API
        self.approval_db = ApprovalQueueDB()
        self.gatekeeper = Gatekeeper(RiskMatrix(), self.approval_db)
    
    def reset(self, incident_id: str):
        """Reset the loop for a new incident."""
        self.state = AgentState()
        self.incident_id = incident_id
        self.start_time = datetime.now()
        logger.info(f"Autonomy loop reset for incident: {incident_id}")
    
    def observe(self, observation: Observation) -> str:
        """Process an observation into a prompt for the model."""
        prompt = f"""SYSTEM:
You are an autonomous infrastructure agent.
Your job: Choose the next action. Nothing else.

INPUT:
{observation.content}

SOURCE: {observation.source}

TOOLS AVAILABLE:
{json.dumps(list(self.policy_engine.tool_registry.keys()), indent=2)}

Previous actions taken: {self.state.actions_taken}
Last action failed: {self.state.last_action_failed}

OUTPUT (JSON ONLY):
{{
  "reasoning": "Chain of thought explaining why this action is chosen...",
  "confidence": 0-100,
  "tool": "tool_name",
  "args": {{ ... }}
}}
"""
        return prompt

    def _wait_for_approval(self, incident_id: str, action_id: str = None) -> bool:
        """
        Poll for approval token/status for the given incident or specific action.
        Blocks until approved or denied.
        Returns True if approved, False if denied.
        """
        logger.warning(f"WAITING FOR APPROVAL. Incident: {incident_id}, Action: {action_id}")

        if action_id:
            # Poll ApprovalQueueDB
            while True:
                if kill_switch.is_active():
                    logger.error("Kill switch activated while waiting for approval. Aborting.")
                    return False

                request = self.approval_db.get_request(action_id)
                if request:
                    status = request.get('status')
                    if status == "APPROVED":
                        logger.info(f"Action {action_id} APPROVED.")
                        return True
                    elif status == "DENIED":
                        logger.warning(f"Action {action_id} DENIED.")
                        return False

                # Also check legacy file mechanism as fallback or concurrent method
                approval_file = self.approvals_path / f"{incident_id}.approve"
                if approval_file.exists():
                    logger.info(f"Legacy approval file found for incident {incident_id}. Resuming.")
                    return True

                time.sleep(1)
        else:
            # Legacy file polling
            approval_file = self.approvals_path / f"{incident_id}.approve"
            logger.warning(f"WAITING FOR APPROVAL. Create file to proceed: {approval_file}")

            while not approval_file.exists():
                if kill_switch.is_active():
                    logger.error("Kill switch activated. Aborting.")
                    return False
                time.sleep(1)

            logger.info(f"Approval received for incident {incident_id}. Resuming.")
            return True
    
    def run_step(self, observation: Observation) -> tuple[PolicyDecision, Optional[Outcome]]:
        """
        Execute one step of the autonomy loop.
        
        Returns:
            (decision, outcome) - decision is the policy result, outcome is None if blocked/escalated
        """
        assert self.incident_id is not None, "Incident ID must be set before running step"

        # 1. Build prompt from observation
        prompt = self.observe(observation)
        
        # 2. Get model decision
        try:
            model_response = self.model_fn(prompt, self.policy_engine.tool_registry)
        except Exception as e:
            logger.error(f"Model failed: {e}")
            return PolicyDecision.ESCALATE, None
        
        logger.info(f"Model decision: {model_response}")

        # Cognitive Health & Observability
        reasoning = model_response.get("reasoning", "No reasoning provided")
        confidence = float(model_response.get("confidence", 100))

        # Traceability: Calculate Reasoning Hash
        # Hash = SHA256(observation + reasoning + action)
        action_str = json.dumps({k: v for k, v in model_response.items() if k not in ["reasoning", "confidence"]}, sort_keys=True)
        trace_content = f"{observation.content}{reasoning}{action_str}"
        reasoning_hash = hashlib.sha256(trace_content.encode()).hexdigest()
        
        # Store Cognitive Trace
        self._store_cognitive_trace(reasoning_hash, reasoning, confidence, model_response)

        # Confidence Check
        if confidence < 70:
            logger.warning(f"Low confidence ({confidence}%). Pausing for Consultation.")
            # Force WAIT_APPROVAL regardless of policy engine, unless it's already blocking/escalating
            # We will evaluate policy first, then override if ALLOW but low confidence
            pass

        # 3. Policy check
        decision, reason = self.policy_engine.evaluate(model_response, self.state)
        
        # Override decision if confidence is low and decision was ALLOW
        if decision == PolicyDecision.ALLOW and confidence < 70:
            decision = PolicyDecision.WAIT_APPROVAL
            reason = f"Low confidence ({confidence}%) requires consultation"

        # Handle WAIT_APPROVAL
        if decision == PolicyDecision.WAIT_APPROVAL:
            approved = self._wait_for_approval(self.incident_id)
            if not approved:
                 # Denied (via kill switch or explicit denial if we passed action_id, but here generic)
                 return PolicyDecision.BLOCK, None

            # After approval, we PROCEED (switch to ALLOW) or re-evaluate?
            # Usually approval implies "Allow despite risk".
            # We will treat it as ALLOW after approval.
            decision = PolicyDecision.ALLOW
            logger.info("Action allowed after approval.")

        if decision == PolicyDecision.BLOCK:
            logger.warning(f"Action BLOCKED: {reason}")
            # Even if blocked, we might want to update stats? Unused decay still happens.
            # But specific tool usage logic requires execution attempt or at least intent?
            # We'll treat blocked as "tool not used" but we should still tick the decay for others.
            # However, `update_tool_stats` expects a used tool name.
            # We'll skip stats update for blocked actions for now, or maybe decay everything as "unused"?
            # Let's keep it simple.
            return decision, None
        
        if decision == PolicyDecision.ESCALATE:
            logger.warning(f"Action ESCALATED: {reason}")
            self.state.escalation_count += 1
            return decision, None
        
        # 4. Gatekeeper Check before Execution
        assert decision == PolicyDecision.ALLOW, f"Expected ALLOW, got {decision}"

        tool_name = model_response.get("tool")
        tool_args = model_response.get("args", {})
        
        # GATEKEEPER CHECK
        gate_decision = self.gatekeeper.execute_or_wait(self.incident_id, tool_name, tool_args)

        if gate_decision["status"] == "PAUSED":
             logger.info(f"Gatekeeper PAUSED execution. {gate_decision['message']}")
             approved = self._wait_for_approval(self.incident_id, gate_decision.get("action_id"))
             if not approved:
                 return PolicyDecision.BLOCK, None
             # If approved, proceed to execution
             logger.info("Gatekeeper released action.")

        outcome: Outcome
        try:
            # Runtime assertion before execution
            assert tool_name in self.policy_engine.tool_registry, "Tool not in registry"

            outcome = self.tool_executor(tool_name, tool_args)
            assert isinstance(outcome, Outcome), "Tool executor must return Outcome object"

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            outcome = Outcome(success=False, error=str(e))
        
        # 5. Update state and confidence
        self.state.actions_taken += 1
        self.state.last_action_failed = not outcome.success
        
        # Update confidence/decay
        self.policy_engine.update_tool_stats(self.state, tool_name, outcome.success)

        # 6. Store replay entry
        if self.incident_id and self.start_time:
            resolution_time = int((datetime.now() - self.start_time).total_seconds())
            entry = ReplayEntry(
                incident_id=self.incident_id,
                observation=observation.content,
                action=model_response,
                outcome={
                    "success": outcome.success,
                    "error": outcome.error,
                    "side_effects": outcome.side_effects,
                },
                resolution_time_seconds=resolution_time,
            )
            self.replay_buffer.append(entry)
            self._persist_replay_entry(entry)
        
        return decision, outcome
    
    def run_until_resolved(
        self, 
        observe_fn: Callable[[], Optional[Observation]],
        is_resolved_fn: Callable[[], bool],
    ) -> bool:
        """
        Run the full autonomy loop until resolved or escalated.
        
        Args:
            observe_fn: Function that returns the next observation, or None if done
            is_resolved_fn: Function that checks if the incident is resolved
        
        Returns:
            True if resolved, False if escalated or blocked
        """
        while not is_resolved_fn():
            # 1. CHECK FOR KILL SWITCH
            if kill_switch.is_active():
                logger.error("🚨 KILL SWITCH ACTIVATED. TERMINATING LOOP.")
                break

            observation = observe_fn()
            if observation is None:
                logger.info("No more observations. Exiting loop.")
                break
            
            decision, outcome = self.run_step(observation)
            
            if decision in (PolicyDecision.BLOCK, PolicyDecision.ESCALATE):
                logger.warning(f"Loop terminated with decision: {decision}")
                return False
            
            if outcome and outcome.success:
                logger.info("Action succeeded. Checking if resolved...")
        
        return is_resolved_fn()
    
    def _store_cognitive_trace(self, r_hash: str, reasoning: str, confidence: float, action: Dict[str, Any]):
        """Store cognitive trace to disk."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{timestamp}_{r_hash}.json"
        filepath = Path("data/cognitive_trace") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, "w") as f:
                json.dump({
                    "reasoning_hash": r_hash,
                    "reasoning": reasoning,
                    "confidence": confidence,
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to store cognitive trace: {e}")

    def _persist_replay_entry(self, entry: ReplayEntry):
        """Persist a replay entry to disk."""
        filename = f"{entry.incident_id}_{entry.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.replay_store_path / filename
        
        with open(filepath, "w") as f:
            json.dump({
                "incident_id": entry.incident_id,
                "observation": entry.observation,
                "action": entry.action,
                "outcome": entry.outcome,
                "resolution_time_seconds": entry.resolution_time_seconds,
                "timestamp": entry.timestamp.isoformat(),
            }, f, indent=2)
        
        logger.debug(f"Replay entry saved: {filepath}")


__all__ = [
    "AutonomyLoop",
    "Observation",
    "Outcome",
    "ReplayEntry",
]
