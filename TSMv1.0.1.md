# TSM99 SecOps AI Platform - v1.0.1

> **The Sovereign Mechanica** — Enterprise AI That Heals, Defends & Evolves
> 
> *Policy-Governed Autonomy for Security Operations*

---

## 🎯 WHAT IS TSM99?

**TSM99 is an autonomous AI platform that runs your security operations center while you sleep.**

It's not a chatbot. It's not a dashboard. It's a **closed-loop system** that:

1. **DETECTS** threats across your infrastructure in real-time
2. **DECIDES** the best response using policy-governed reasoning
3. **EXECUTES** automated remediation (with safety rails)
4. **LEARNS** from every outcome to get smarter over time
5. **PROVES** every action in an immutable audit trail

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Autonomous Healing** | Auto-restart services, scale pods, rollback deployments |
| **Threat Detection** | AI-powered anomaly detection across logs, metrics, network |
| **Policy Governance** | Every action requires policy approval before execution |
| **Explainable AI** | See exactly WHY the AI made each decision |
| **Zero-Trust Safety** | Kill switch, blast radius limits, human escalation |
| **Offline-First** | Works without cloud APIs using local models |

---

## ❓ WHY TSM99?

### The Problem

- **Alert fatigue**: SOC teams drown in 10,000+ alerts/day
- **Slow response**: Average incident takes 287 days to detect
- **Skill shortage**: 3.5M unfilled cybersecurity jobs globally
- **Manual toil**: 80% of response is copy-paste from runbooks
- **No learning**: Same incidents repeat because nothing learns

### The Solution

TSM99 replaces the **firefighting loop** with an **autonomous healing loop**:

```
Traditional SOC:          TSM99:
Alert → Human → Action    Alert → AI → Policy → Action → Learn
(hours to days)           (seconds to minutes)
```

### Key Differentiators

| Others | TSM99 |
|--------|-------|
| Assistants that suggest | Agents that execute |
| Cloud-dependent | Runs completely offline |
| Black-box decisions | Explainable reasoning |
| Static playbooks | Self-evolving intelligence |
| Pay per API call | Self-hosted, zero API costs |

---

## 🔧 HOW IT WORKS

### The Autonomy Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    TSM99 AUTONOMY LOOP                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ OBSERVE  │───▶│  MODEL   │───▶│  POLICY  │             │
│   │ Telemetry│    │ Reasoning│    │  Engine  │             │
│   └──────────┘    └──────────┘    └────┬─────┘             │
│                                        │                    │
│                   ┌────────────────────┴───────────────┐   │
│                   ▼                    ▼               ▼   │
│              ┌─────────┐         ┌─────────┐     ┌──────┐ │
│              │  ALLOW  │         │  BLOCK  │     │ESCALATE│ │
│              └────┬────┘         └─────────┘     └──────┘ │
│                   ▼                                        │
│   ┌──────────┐    │    ┌──────────┐    ┌──────────┐       │
│   │  LEARN   │◀───┴───▶│ EXECUTE  │───▶│ OUTCOME  │       │
│   │  Replay  │         │  Tools   │    │  Scorer  │       │
│   └──────────┘         └──────────┘    └──────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The Architecture (35 Core Modules)

```
backend/src/core/
├── autonomy/      → Decision loop, policy engine, replay
├── memory/        → Episodic, semantic, policy, economic memory
├── outcomes/      → Scoring, causal attribution, failure classification
├── tools/         → Risk scoring, success mapping, metrics
├── economics/     → Cost budgets, ROI tracking, spend governance
├── evolution/     → Shadow mirror, self-improvement, axiom synthesis
├── simulation/    → Chaos agents, ghost simulation, red team
├── healing/       → Hotfix mutation, auto-remediation
├── sandbox/       → Shadow runner, isolated execution
├── vault/         → Sovereign gate, kill switch, emergency access
├── trust_ledger/  → Immutable audit trail, cryptographic proofs
├── llm/           → Poly-LLM routing, local model support
├── detection/     → Anomaly engine, threat correlation
├── training/      → Dataset synthesis, replay-based learning
└── ... (20+ more modules)
```

### Safety Architecture

```
┌────────────────────────────────────────────────┐
│              SAFETY GUARANTEES                  │
├────────────────────────────────────────────────┤
│ ✅ Policy Engine is DETERMINISTIC (no ML)      │
│ ✅ Every action logged to immutable ledger     │
│ ✅ Kill switch accessible at /admin            │
│ ✅ High-risk actions require human approval    │
│ ✅ Blast radius limits per environment         │
│ ✅ Confidence decay for unused policies        │
│ ✅ Tool blacklisting after repeated failures   │
│ ✅ Emergency cost cutoff                       │
└────────────────────────────────────────────────┘
```

---

## 📦 WHAT'S IN v1.0.1

### Backend (Python/FastAPI)

| Module | Files | Purpose |
|--------|-------|---------|
| **Autonomy** | 7 | Core decision loop, policy engine, replay |
| **Memory** | 7 | 4-layer memory (episodic/semantic/policy/economic) |
| **Outcomes** | 8 | Scoring, causal graphs, failure classification |
| **Tools** | 5 | Risk modeling, success mapping, metrics |
| **Economics** | 6 | Budgets, cost tracking, ROI, cloud optimizer |
| **Evolution** | 21 | Shadow mirror, self-improvement, mutation |
| **Simulation** | 7 | Chaos agents, ghost sim, red team |
| **Healing** | 4 | Hotfix mutator, auto-remediation |
| **LLM** | 13 | Poly-LLM router, local providers |
| **Training** | 8 | Dataset builders, replay learning |

### Frontend (Next.js)

| Category | Components |
|----------|------------|
| **Autonomy Views** | ReasoningViewer, ReplayTimeline, CostDashboard, ToolRiskHeatmap, PolicyConfidenceDashboard |
| **Executive Views** | ExplainableAIPanel, StrategicRoadmap, TrainingControl |
| **Vault Views** | VaultStatus, SovereignReport, ShutterTransition |
| **Admin** | Kill Switch, Emergency Access, Policy Editor |

### Tests (65+ test files)

```
backend/tests/
├── core/autonomy/     → test_autonomy_loop, policy_engine, replay
├── core/economics/    → test_cloud_optimizer, economic_negotiator
├── core/evolution/    → test_shadow_mirror
├── core/healing/      → test_hotfix_mutator
├── core/simulation/   → test_chaos_agent, ghost_sim
├── core/vault/        → test_sovereign_gate
└── ... (comprehensive coverage)
```

### Compliance Documentation

```
docs/compliance/
├── ACCESS_CONTROL.md       → Identity & access policies
├── AUDIT_LOGGING.md        → What gets logged, retention
├── AUTONOMY_SAFETY.md      → AI decision governance
├── CHANGE_MANAGEMENT.md    → Deployment controls
├── CONTROL_MAPPING.md      → SOC 2 / ISO 27001 mapping
├── INCIDENT_RESPONSE.md    → Playbooks & escalation
└── MODEL_GOVERNANCE.md     → LLM safety & selection
```

### Deployment Tools

```
tools/
├── ice-age/               → Offline sovereign deployment
│   ├── setup.sh           → Full installation script
│   ├── offline-mode.sh    → Block all outbound traffic
│   ├── forensic-replay.sh → Post-incident analysis CLI
│   ├── cold-boot-recovery.sh → Immutable snapshots
│   ├── cpu-only-mode.sh   → GPU optional, CPU default
│   └── local_trainer.py   → On-premise model training
└── sentinel/              → Go-based monitoring agent
    ├── main.go
    └── go.mod
```

---

## 🚀 QUICK START

### 1. Install Ollama (Local LLM)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull deepseek-coder:6.7b-instruct-q4_K_M
```

### 2. Start Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Access
- **Dashboard**: http://localhost:3000
- **Admin Panel**: http://localhost:3000/admin
- **API Docs**: http://localhost:8000/docs

---

## 📊 SCORECARD

| Dimension | Score | Evidence |
|-----------|-------|----------|
| **Architecture** | 10/10 | 35 core modules, closed-loop design |
| **Safety** | 10/10 | Deterministic policy, kill switch, audit trail |
| **Autonomy** | 10/10 | Self-healing, self-evolving, self-learning |
| **Enterprise** | 10/10 | SOC 2 ready, cost governance, RBAC |
| **Sovereignty** | 10/10 | Offline-first, local models, no API dependency |
| **Learning** | 10/10 | 4-layer memory, replay engine, outcome scoring |

---

## 📞 CONTACT

- **Founder**: founder@thesovereignmechanica.ai
- **Repository**: https://github.com/noData0079/SecOPS.v1
- **Documentation**: `/docs/` directory

---

*TSM99 — The Sovereign Mechanica v1.0.1*
*Built for those who demand AI that works FOR them, not ON them.*
