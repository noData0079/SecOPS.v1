# Features and Services Architecture

## System Overview
TSM99 (The Sovereign Mechanica) is an autonomous security and operations platform. It allows organizations to detect, reason about, and remediate risks across their entire technical stack (Code, Infrastructure, Cloud) with verifiable trust.

## Core Microservices (Logical)

### 1. **Ingest Service** (`backend/src/api/routes/ingest.py`*)
- **Purpose**: Normalizes signals from disparate sources (GitHub Webhooks, K8s Events, CloudWatch Logs).
- **Features**:
  - `POST /upload`: Secure file upload for config analysis.
  - Signal De-duplication.
  - Metadata enrichment.

### 2. **Reasoning Engine** (`backend/src/agent/reasoning/`)
- **Purpose**: The "Brain" of the platform. Uses Poly-LLM architecture to understand context.
- **Features**:
  - **Context Stitcher**: Graphs relationships between a CVE, a K8s Pod, and a Code Commit.
  - **Planner**: Decomposes high-level goals ("Fix vulnerability") into atomic steps.
  - **Critic**: Self-reflects on proposed plans to ensure safety.

### 3. **Action Executor** (`backend/src/agent/executor/`)
- **Purpose**: Performs side-effects (modifications) on external systems.
- **Features**:
  - **Sandboxed Execution**: Actions run in isolated scopes.
  - **Provider Adapters**: GitHub API, Kubernetes API, AWS SDK.
  - **Approval Gate**: Checks with Trust Ledger and Policy Engine before commit.

### 4. **Trust Ledger** (`backend/src/core/trust_ledger/`)
- **Purpose**: Immutable audit trail.
- **Features**:
  - **Cryptographic Chaining**: Each entry contains a hash of the previous one.
  - **Verification**: Record of *who* approved *what* and *why*.
  - **Telemetry**: Timestamp, Latency, Model ID, Confidence Score.

### 5. **Security Kernel** (`backend/src/core/security/`)
- **Purpose**: Global safety enforcement.
- **Features**:
  - **Kill Switch**: Immediate halt of all outbound actions.
  - **Rate Limiter**: Token-bucket protection against abuse.
  - **Demo Guard**: Enforces strict resource quotas for evaluation users.

---

## Infrastructure Services

| Service | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14 | User Interface (Console, Admin, Demo) |
| **Backend** | FastAPI (Python) | API, Orchestration, Reasoning |
| **Database** | PostgreSQL | Persistence (Users, Policies, Ledger) |
| **Cache/Queue** | Redis | Rate limiting, async job queues (Celery/Rq) |
| **Vector Store** | Chroma/Pgvector | RAG Knowledge Base |

## Authentication Model

1.  **Public**: Landing Page (Read-only).
2.  **Demo**: Transient Session (`X-DEMO-MODE: true`). Restricted capabilities.
3.  **Admin**: Persistent Key (`Authorization: Bearer <ADMIN_KEY>`). Full control.

---

## Implementation Status (Phase 3)

- [x] **Global Kill Switch**: Active.
- [x] **Rate Limiting**: Active (Memory-backed).
- [x] **Demo Guard**: Active (200KB Upload Limit, No Exec).
- [x] **Trust Ledger**: Logic implemented, UI preview available.
