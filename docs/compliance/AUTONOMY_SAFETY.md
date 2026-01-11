# Autonomy Safety Justification

## Overview
The safety of TSM99's autonomous capabilities is guaranteed by a "Defense-in-Depth" architecture that wraps the probabilistic nature of LLMs with deterministic controls.

## 1. Architectural Safety (The Loop)
The Autonomy Loop is designed to isolate the model from the execution environment.

**Evidence Source:** `backend/src/core/autonomy/loop.py`

- **Isolation**: The model receives text (Observation) and outputs text (JSON). It has no direct access to the shell, network, or filesystem.
- **Sandboxing**: Tools are executed by a dedicated `tool_executor` which can enforce boundaries (e.g., containerization, timeouts).

```
OBSERVATION → MODEL → POLICY → TOOLS → OUTCOME → REPLAY
```

## 2. Deterministic Guardrails
Safety is enforced by the `PolicyEngine`, which is rule-based and deterministic.

**Evidence Source:** `backend/src/core/autonomy/policy_engine.py`

- **Schema Validation**: Inputs are validated against a strict schema before execution.
- **Risk Gating**: High-risk tools are blocked or require escalation based on context (e.g., Production vs. Development).
- **Rate Limiting**: `max_actions` limits the "blast radius" of a runaway agent.

## 3. Human Oversight
The system defaults to "Escalate" in ambiguous or high-risk situations.

- **Escalation Trigger**: Failure to meet confidence thresholds or policy rules results in `PolicyDecision.ESCALATE`.
- **Intervention**: Humans can intervene at the loop level via the `WAIT_APPROVAL` state (implied by escalation handling).

## 4. Verification & Testing
- **Replay Testing**: Historical incidents are replayed to verify policy effectiveness without risking live systems.
- **Auditability**: Every step is logged (`ReplayEntry`), allowing for post-hoc safety analysis and forensic reconstruction.

## 5. Production Constraints
- **Frozen Core**: The safety architecture itself is immutable without founder approval (`docs/AUTONOMY_ARCHITECTURE.md`).
- **Allowed List**: Only tools explicitly marked `prod_allowed=True` can run in production environments.
