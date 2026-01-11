# SOC 2 Control Mapping

## Overview
This document maps TSM99's internal controls to the AICPA SOC 2 Trust Services Criteria (TSC).

| SOC 2 Criteria | TSM99 Control | Description | Evidence Source |
| :--- | :--- | :--- | :--- |
| **CC1.1** (Control Environment) | **Separation of Duties** | Control Plane (Policy) is strictly separated from Execution Plane (Tools). | `docs/AUTONOMY_ARCHITECTURE.md` |
| **CC2.1** (Communication) | **Governance Documentation** | Policies and procedures are documented in the Governance Binder. | `GOVERNANCE_BINDER.md` |
| **CC3.1** (Risk Assessment) | **Risk Scoring** | Automated risk assessment for every autonomous action via Policy Engine. | `backend/src/core/autonomy/policy_engine.py` (Class `RiskLevel`) |
| **CC6.1** (Logical Access) | **RBAC** | Role-based access control via Supabase Auth and admin guards. | `backend/src/api/deps.py` (`require_admin`) |
| **CC6.6** (External Threats) | **Sandboxing** | Model execution is isolated; no direct shell access. | `backend/src/core/autonomy/loop.py` |
| **CC7.1** (System Ops) | **Audit Logging** | Immutable logging of all actions and outcomes (Replay Buffer). | `backend/src/core/autonomy/loop.py` (`ReplayEntry`) |
| **CC7.2** (Incident Management) | **Auto-Escalation** | System detects failures/risks and escalates to humans. | `backend/src/core/autonomy/policy_engine.py` (Rule 4) |
| **CC8.1** (Change Management) | **Frozen Core** | Critical autonomy code is locked; changes require approval. | `docs/AUTONOMY_ARCHITECTURE.md` |
| **CC8.1** (Change Management) | **Policy-Gated Exec** | No autonomous action occurs without policy approval. | `backend/src/core/autonomy/policy_engine.py` |

## Detailed Mapping

### CC6.1 - Logical Access Security
**Control**: The system restricts access to critical functions based on user roles.
- **Implementation**: The `require_admin` dependency in `backend/src/api/deps.py` enforces that only users with `service_role`, `admin`, or `superadmin` claims can access protected endpoints.

### CC7.1 - System Operations (Auditing)
**Control**: The system creates an immutable record of processing activities.
- **Implementation**: The `AutonomyLoop` writes every step to a JSON file on disk (`backend/src/core/autonomy/loop.py`), capturing the input, model decision, policy check, and tool output.

### CC3.1 - Risk Mitigation
**Control**: The system assesses risk before executing autonomous actions.
- **Implementation**: The `PolicyEngine` (`backend/src/core/autonomy/policy_engine.py`) assigns a `RiskLevel` (NONE, LOW, MEDIUM, HIGH) to every tool and blocks or escalates based on confidence and environment.
