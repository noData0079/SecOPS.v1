# Incident Response Flow

## Overview
TSM99 defines a clear workflow for handling system incidents, autonomous failures, and emergency situations. The response strategy prioritizes safety and human oversight.

## 1. Automated Escalation
The system automatically escalates control to humans when pre-defined risk or failure thresholds are met.

**Evidence Source:** `backend/src/core/autonomy/policy_engine.py`

### Triggers
- **Action Limit Reached**: Exceeding the maximum allowed steps (`max_actions`).
- **Low Confidence**: High-risk actions with insufficient model confidence (< 0.85).
- **Repeated Failures**: Consecutive action failures (Rule 4).

### Mechanism
The `PolicyEngine` returns `PolicyDecision.ESCALATE`, causing the `AutonomyLoop` to pause and request human intervention.

```python
# backend/src/core/autonomy/policy_engine.py

if state.last_action_failed and state.escalation_count >= 2:
    logger.warning("Multiple failures detected. Escalating.")
    return PolicyDecision.ESCALATE
```

## 2. Emergency Protocol ("Break Glass")
For critical system failures or rogue behavior, a manual override is available.

**Evidence Source:** `GOVERNANCE_BINDER.md`

- **Command**: `/emergency-access`
- **Actions Available**:
    - **Global Kill Switch**: Instantly halts all autonomous execution.
    - **API Key Revocation**: Cuts off external access.
    - **Log Access**: Immediate view of audit trails.

## 3. Human-in-the-Loop Resolution
When an incident is escalated:
1.  **Notification**: The system flags the incident for review.
2.  **Review**: Operators examine the `ReplayEntry` logs and `PolicyDecision` history.
3.  **Action**: Operators can manually intervene, approve the blocked action, or terminate the session.

## 4. Post-Incident Review
All escalated incidents and emergency actions trigger a mandatory review process.
- **Data**: Replay logs and database events (`replay_events`) are analyzed.
- **Outcome**: Policy rules are updated (e.g., decaying confidence for failed tools) to prevent recurrence.
