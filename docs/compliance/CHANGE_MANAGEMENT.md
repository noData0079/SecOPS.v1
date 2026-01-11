# Change Management Policy

## Overview
TSM99 strictly controls changes to the system, particularly the autonomy core, ensuring stability, safety, and compliance. The system operates under a "Frozen Core" policy for critical components.

## Policy-Gated Execution
All autonomous actions are subject to strict policy gates. No action is executed without passing deterministic checks.

**Evidence Source:** `backend/src/core/autonomy/policy_engine.py`

### Mechanism
1.  **Proposed Action**: The model proposes a tool and arguments.
2.  **Policy Evaluation**: The `PolicyEngine` evaluates the proposal against immutable rules.
3.  **Decision**: The engine returns `ALLOW`, `BLOCK`, or `ESCALATE`.

```python
# backend/src/core/autonomy/policy_engine.py

def policy_check(action: ProposedAction, state: AgentState) -> PolicyDecision:
    # Rule 3: Block prod-disallowed actions in prod
    if not action.prod_allowed and state.environment == "production":
        return PolicyDecision.BLOCK
    # ...
```

## Immutable Core Components
Certain architectural components are designated as **FROZEN** and require explicit founder approval for modification.

**Evidence Source:** `docs/AUTONOMY_ARCHITECTURE.md`

- **Status**: FROZEN
- **Restricted Components**:
    - Core Autonomy Loop
    - Policy Engine Rules
    - Replay Logic

## Change Request & Approval
- **Code Changes**: Managed via Git version control.
- **Human Oversight**: High-risk actions require human approval (via `WAIT_APPROVAL` state and `ESCALATE` decision).
- **Audit Trail**: All policy decisions (Blocks/Escalations) are logged to the decision log.

## Environment Separation
- **Development**: Allows broader tool usage for testing.
- **Production**: Enforces strict "prod-allowed" flags on all tools.

## Emergency Changes
Emergency changes follow the "Break Glass" protocol defined in `GOVERNANCE_BINDER.md`. All such changes are post-incident reviewed.
