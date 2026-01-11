# Audit Logging Description

## Overview
TSM99 maintains comprehensive, immutable audit logs for all system activities, ensuring full traceability of autonomous decisions and human actions.

## 1. Replay Buffer (Operational Logs)
The Autonomy Loop records every step of execution into a structured JSON "Replay Entry". These logs serve as the primary source of truth for agent behavior.

**Evidence Source:** `backend/src/core/autonomy/loop.py`

### Log Structure (`ReplayEntry`)
- **Incident ID**: Unique identifier for the session.
- **Timestamp**: ISO-8601 timestamp of the event.
- **Observation**: The input data triggered the action.
- **Action**: The tool and arguments selected by the model.
- **Outcome**: The result of the execution (Success/Failure, Side Effects).
- **Resolution Time**: Time taken to resolve the step.

```python
# backend/src/core/autonomy/loop.py

@dataclass
class ReplayEntry:
    incident_id: str
    observation: str
    action: Dict[str, Any]
    outcome: Dict[str, Any]
    resolution_time_seconds: int
    timestamp: datetime = field(default_factory=datetime.now)
```

### Persistence
Logs are written to disk as immutable JSON files:
`{incident_id}_{timestamp}.json`

## 2. Policy Decision Log
The Policy Engine maintains an internal log of all evaluations, capturing the "why" behind every allowed or blocked action.

**Evidence Source:** `backend/src/core/autonomy/policy_engine.py`

- **Content**: Tool name, Confidence score, Decision (ALLOW/BLOCK/ESCALATE), System State.

## 3. Database Audit Trails
Persistent state changes and replay events are logged to the database with mandatory timestamps.

**Evidence Source:** `backend/src/db/schemas/replay.py`

### Replay Event Schema
- **Table**: `replay_events`
- **Fields**:
    - `replay_run_id`: Session UUID.
    - `event_type`: Type of event (e.g., POLICY_DECAY).
    - `before_state` / `after_state`: JSON snapshots.
    - `created_at` / `updated_at`: Automatically managed via `TimestampMixin`.

```python
# backend/src/db/schemas/replay.py

class ReplayEvent(Base, TimestampMixin):
    # ...
    replay_run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    before_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})
    # ...
```

## Retention & Integrity
- **Format**: JSON (human-readable and machine-parseable).
- **Integrity**: Append-only design for log files and database records.
- **Retention**: Logs are persisted to disk and database for historical analysis.
