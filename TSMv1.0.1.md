# TSM99 SecOps AI Platform - v1.0.1

> **The Sovereign Mechanica** — Enterprise AI That Heals, Defends & Refines
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

---

## ❓ WHY TSM99?

### The Problem

| Challenge | Reality |
|-----------|---------|
| **Alert Fatigue** | SOC teams drown in 10,000+ alerts/day |
| **Slow Response** | Average incident takes 287 days to detect |
| **Skill Shortage** | 3.5M unfilled cybersecurity jobs globally |
| **Manual Toil** | 80% of response is copy-paste from runbooks |
| **No Learning** | Same incidents repeat because nothing learns |

### The Solution

TSM99 replaces the **firefighting loop** with an **autonomous healing loop**:

```
Traditional SOC:          TSM99:
Alert → Human → Action    Alert → AI → Policy → Action → Learn
(hours to days)           (seconds to minutes)
```

---

## 🔧 THE 5 FEATURES

TSM99 delivers **5 outcomes**. Not 35 modules to manage—just 5 things that work.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TSM99 FEATURES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│   │  AUTOPILOT  │  │  DEFENDER   │  │  SENTINEL   │                │
│   │ Self-Healing│  │Threat Hunter│  │ Governance  │                │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│          │                │                │                        │
│          └────────────────┼────────────────┘                        │
│                           │                                         │
│              ┌────────────┴────────────┐                            │
│              │                         │                            │
│         ┌────┴────┐              ┌─────┴─────┐                      │
│         │ ORACLE  │              │ FORTRESS  │                      │
│         │Learning │              │Sovereignty│                      │
│         └─────────┘              └───────────┘                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 1️⃣ AUTOPILOT — Self-Healing Infrastructure

> *"Fix it before I even know it's broken—but test it first."*

| What It Does | How It Works |
|--------------|--------------|
| Auto-restart failed services | Detects failures, applies fixes, verifies recovery |
| Scale pods under pressure | Predicts load, auto-scales before degradation |
| Rollback bad deployments | Detects regressions, reverts to last-known-good |
| Patch vulnerabilities | Applies security patches with rollback capability |

#### 🧪 Liability Sandbox (Ghost Environment)

**Problem**: What if Autopilot "fixes" something and brings down a hospital network or a bank's trading floor?

**Solution**: Every fix runs in a **Ghost Environment** before touching production.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIABILITY SANDBOX FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   FIX PROPOSED ──→ 🧪 GHOST ENVIRONMENT                        │
│                         │                                       │
│                    [Simulate Fix]                               │
│                         │                                       │
│              ┌──────────┼──────────┐                           │
│              ▼          ▼          ▼                           │
│          [PASS]     [PARTIAL]   [FAIL]                         │
│              │          │          │                           │
│              ▼          ▼          ▼                           │
│         DEPLOY     HUMAN       BLOCK                           │
│        TO PROD    REVIEW     + ALERT                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 🎯 Critical Path Isolation (Practical Ghost)

**Problem**: Cloning a perfect Ghost of multi-cloud is impossible. If Ghost doesn't mirror production DB state, simulation is a lie.

**Solution**: Don't clone the whole network. Clone the **target service + immediate dependencies only**.

```
┌─────────────────────────────────────────────────────────────────┐
│              CRITICAL PATH ISOLATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   PRODUCTION                         GHOST (Isolated)           │
│   ────────────────────               ─────────────────          │
│   ┌─────┐ ┌─────┐ ┌─────┐           ┌─────────────────┐        │
│   │ API │ │ DB  │ │Cache│           │  TARGET SERVICE │        │
│   └──┬──┘ └──┬──┘ └──┬──┘           │     (cloned)    │        │
│      │       │       │              └────────┬────────┘        │
│   ┌──┴───────┴───────┴──┐                    │                 │
│   │    Auth Service     │  ←── Clone ───→   ┌┴─────────────┐   │
│   │    (being fixed)    │                   │ Auth + Deps  │   │
│   └─────────────────────┘                   │ • DB (stub)  │   │
│                                             │ • Cache (mock)│   │
│   ❌ Don't clone: 50 other services         │ • API (mock)  │   │
│   ✅ Clone: Auth + its 3 dependencies       └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Component | Ghost Strategy |
|-----------|----------------|
| **Target Service** | Full clone (code + config) |
| **Database** | Schema clone + synthetic data |
| **Upstream APIs** | Mock with recorded responses |
| **Message Queues** | Local stub with replay |
| **Other Services** | NOT cloned (isolation boundary) |

| Risk Level | Ghost Simulation | Human Approval |
|------------|------------------|----------------|
| **LOW** (restart pod) | 5s quick check | ❌ Auto-deploy |
| **MEDIUM** (config change) | 30s full sim | ⚠️ Review if anomaly |
| **HIGH** (DB migration) | 5min deep test | ✅ **Always required** |
| **CRITICAL** (network/firewall) | Full replay | ✅ **Break-glass only** |

**What the Ghost Tests:**
- ✅ Service starts successfully
- ✅ Health checks pass
- ✅ No cascading failures
- ✅ Rollback works
- ✅ No data corruption

> *"Clone the patient, not the hospital."*

**Single Toggle**: Enable "Autopilot Mode" and walk away—the Ghost handles liability.

---

### 2️⃣ DEFENDER — Threat Detection & Response

> *"Hunt threats 24/7, respond in seconds."*

| What It Does | How It Works |
|--------------|--------------|
| Anomaly detection | AI scans logs, metrics, network for deviations |
| Threat correlation | Connects signals across your stack |
| Automated containment | Isolates threats before they spread |
| Red team simulation | Tests your defenses with synthetic attacks |

**Single Toggle**: Enable "Active Defense" for autonomous threat hunting.

---

### 3️⃣ SENTINEL — Governance, Compliance & Integration Hub

> *"Every action approved, logged, provable—and connected to your stack."*

#### 🔒 Governance Features

| What It Does | How It Works |
|--------------|--------------|
| Policy enforcement | AI proposes, policy decides, never the other way |
| Immutable audit trail | Cryptographic proof of every action |
| Kill switch | One-click emergency stop for all autonomy |
| Compliance mapping | SOC 2, ISO 27001, GDPR control evidence |

#### 🔌 Universal Adapter (Integration Hub)

**TSM99 is NOT a walled garden.** The Sentinel agent bridges your existing tools:

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION HUB                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   YOUR EXISTING TOOLS              TSM99 SENTINEL               │
│   ┌─────────────────┐             ┌─────────────────┐          │
│   │ CrowdStrike     │────────────▶│                 │          │
│   │ Splunk/SIEM     │────────────▶│   UNIVERSAL     │          │
│   │ Wiz/CSPM        │────────────▶│    ADAPTER      │──▶ BRAIN │
│   │ Okta/IAM        │────────────▶│     (Go)        │          │
│   │ PagerDuty       │────────────▶│                 │          │
│   │ Jira/ServiceNow │────────────▶│                 │          │
│   └─────────────────┘             └─────────────────┘          │
│                                                                 │
│   ✅ MCP Protocol Support (Model Context Protocol)              │
│   ✅ Bi-directional: Read alerts, Push actions                 │
│   ✅ mTLS Secured: Cryptographically signed commands           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Integration | Direction | What It Does |
|-------------|-----------|--------------|
| **CrowdStrike** | ← IN | Ingest EDR alerts, enrich with context |
| **Splunk** | ↔ BOTH | Pull logs, push incident data |
| **Wiz** | ← IN | Cloud misconfigs → auto-remediate |
| **Okta** | → OUT | Suspend compromised accounts |
| **PagerDuty** | → OUT | Escalate to humans when needed |
| **ServiceNow** | → OUT | Auto-create tickets with AI context |

#### 🩺 Integration Health-Check (Fail-Safe)

**Problem**: If Splunk updates its API and the adapter breaks, your autonomy loop dies.

**Solution**: Continuous health monitoring with automatic confidence adjustment.

```
┌─────────────────────────────────────────────────────────────────┐
│                INTEGRATION HEALTH DASHBOARD                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   TOOL           STATUS      LAST PING    CONFIDENCE            │
│   ─────────────────────────────────────────────────────────     │
│   CrowdStrike    🟢 LIVE     2s ago       100%                  │
│   Splunk         🟢 LIVE     5s ago       100%                  │
│   Wiz            🟡 SLOW     45s ago      85%  ⚠️               │
│   Okta           🟢 LIVE     1s ago       100%                  │
│   PagerDuty      🔴 DOWN     5min ago     0%   🚨               │
│                                                                 │
│   [When tool goes dark → Oracle reduces domain confidence]      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Health State | Confidence Impact | Oracle Action |
|--------------|-------------------|---------------|
| 🟢 **LIVE** | 100% trust | Normal autonomous operation |
| 🟡 **SLOW** | 85% trust | Flag decisions, prefer alternatives |
| 🟠 **DEGRADED** | 50% trust | Require human confirmation |
| 🔴 **DOWN** | 0% trust | **Block autonomous actions** for that domain |

**When PagerDuty Goes Dark:**
1. Sentinel detects no heartbeat (>60s)
2. Sentinel alerts Oracle: "PagerDuty DOWN"
3. Oracle sets `escalation_confidence = 0%`
4. AUTOPILOT falls back to: Email → Slack → SMS
5. Dashboard shows 🔴 with recommended fix

> *"Integration breaks don't kill the system—they trigger fallback strategies."*

**Single Dashboard**: See every decision, why it was made, and its outcome.

---

### 4️⃣ ORACLE — Policy Refinement & Intelligence

> *"Proposes improvements. You approve. It learns."*

| What It Does | How It Works |
|--------------|--------------|
| Outcome scoring | Every action rated 0-100 for effectiveness |
| Policy proposals | AI suggests refinements, **human clicks Commit** |
| Confidence tracking | Knows when to act vs. when to ask |
| Predictive readiness | Simulates future incidents to prepare |

**Human-in-the-Loop**: All policy changes require explicit approval.

---

### 5️⃣ FORTRESS — Sovereignty & Tiered Intelligence

> *"Your AI, your data, your control. Fast AND deep."*

#### 🔥 Two-Tier Inference (Speed + Depth)

| Tier | Models | Latency | Use Case |
|------|--------|---------|----------|
| **TIER 1: EDGE** | Phi-3 (2B), Qwen-2B | **10-50ms** | Triage, classification, **HARD-STOP** |
| **TIER 2: DEEP** | DeepSeek-6.7B, Llama-70B | 1-5s | Complex reasoning, multi-signal correlation |

#### ⚡ Fast-Path Veto (The Moat)

**Problem**: What if Tier 1 makes a mistake and Tier 2 spends 2s reasoning about a false positive while the real attack slips through?

**Solution**: Tier 1 has **HARD-STOP** authority for known signatures—no waiting for Tier 2.

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAST-PATH VETO ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ALERT ──→ TIER 1 (10ms)                                      │
│                │                                                │
│       ┌────────┼────────┬──────────────┐                       │
│       ▼        ▼        ▼              ▼                       │
│   [KNOWN]  [SIMPLE]  [COMPLEX]    [UNCERTAIN]                  │
│   ATTACK    EVENT      ↓               ↓                       │
│      │        │    TIER 2 (2s)    🔒 BLOCK PATH                │
│      ▼        ▼        │          UNTIL DEEP                   │
│  ⛔ HARD    AUTO-      ↓          RESPONDS                     │
│    STOP    RESOLVE   DEEP FIX         │                        │
│   (0ms)     (10ms)    (2s)            ▼                        │
│      │                            TIER 2 DECIDES               │
│      ▼                                                         │
│   🚨 BLOCK + ALERT + LOG                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 🛑 Hard-Stop Policy (No Waiting)

| Signature Type | Tier 1 Action | Wait for Tier 2? |
|----------------|---------------|------------------|
| **Known ransomware hash** | Block immediately | ❌ NO |
| **SQL injection pattern** | Block + quarantine | ❌ NO |
| **Known C2 domain** | DNS sinkhole | ❌ NO |
| **Brute force (5+ fails)** | Lock account | ❌ NO |
| **Crypto-mining process** | Kill + alert | ❌ NO |

#### 🔒 Path Blocking (Defense in Depth)

**When Tier 1 is uncertain but suspicious:**
1. **BLOCK** the suspicious path immediately (10ms)
2. **QUEUE** to Tier 2 for deep analysis (2s)
3. **HOLD** until Tier 2 responds
4. **UNBLOCK** only if Tier 2 says safe

> *"Better to block for 2 seconds than let an attack through."*

**Why Two Tiers?**
- **Attack at 100Gbps?** → Tier 1 HARD-STOPS known patterns in **10ms**
- **Unknown threat?** → Block path, wait 2s for Tier 2 analysis
- **False positive cost** → 2s delay vs breach = acceptable trade-off

#### 🛡️ The Locked Vault Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOVEREIGNTY MODEL                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   YOUR INFRASTRUCTURE                                           │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  🔒 LOCKED VAULT                                         │  │
│   │  ├── Your logs, metrics, incidents                      │  │
│   │  ├── Your response patterns                             │  │
│   │  ├── Your infrastructure fingerprint                    │  │
│   │  └── ENCRYPTED: Only TSM99 AI can read/use              │  │
│   └─────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  ⚡ LOCAL AI (99% of work)                               │  │
│   │  ├── Trained on YOUR patterns                           │  │
│   │  ├── Responds in milliseconds                           │  │
│   │  ├── ZERO API COSTS                                     │  │
│   │  └── Works fully offline                                │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ═══════════════════════════════════════════════════════════   │
│   GLOBAL AI (1% of work - Updates Only)                        │
│   ├── Syncs new threat intelligence                            │
│   ├── Pushes model improvements                                │
│   ├── Never sees your raw data                                 │
│   └── YOU control when it connects                             │
└─────────────────────────────────────────────────────────────────┘
```

#### 💰 Zero API Cost Architecture

| What Others Do | What TSM99 Does |
|----------------|-----------------|
| Every alert → API call → $$$$ | Every alert → Local AI → **$0** |
| 10,000 alerts = $500/day | 10,000 alerts = **$0/day** |
| Data leaves your network | Data **never leaves** |
| Vendor trains on your data | Your data trains **your** AI |

**When Does Global AI Connect?**

| Trigger | Purpose | Frequency |
|---------|---------|-----------|
| Scheduled sync | Update threat signatures | Weekly (you choose) |
| New vulnerability | Push critical patches | On-demand |
| Model improvement | Deploy refined capabilities | Monthly |

**YOUR DATA NEVER LEAVES. GLOBAL LEARNS FROM PATTERNS, NOT RAW DATA.**

#### 🛡️ Adversarial Defense (3-Layer Protection)

**Problem**: What if an attacker tries to poison our AI's learning?

**Solution**: FORTRESS uses 3-layer defense against adversarial training.

```
┌─────────────────────────────────────────────────────────────────┐
│              3-LAYER ADVERSARIAL DEFENSE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   LAYER 1: STATISTICAL DRIFT DETECTION                         │
│   ├── Golden Baseline (Day 1 snapshot)                         │
│   ├── Centroid Shift alerts if "normal" moves too fast        │
│   └── Median Absolute Deviation prunes "weird" data            │
│                                                                 │
│   ─────────────────────────────────────────────────────────────│
│                                                                 │
│   LAYER 2: AXIOM ENGINE (Deterministic Veto)                   │
│   ├── Axioms = Hard-coded rules (NOT AI)                       │
│   ├── Example: "No service talks to Russian IP on weekends"    │
│   └── If AI learns conflicting pattern → VETO + ALERT          │
│                                                                 │
│   ─────────────────────────────────────────────────────────────│
│                                                                 │
│   LAYER 3: SHADOW MIRRORING                                    │
│   ├── Primary Brain: Learns in real-time                       │
│   ├── Mirror Brain: Only learns from human-verified data       │
│   └── If Primary ignores attack that Mirror catches → POISONED │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Attack Type | Legacy AI Response | TSM99 FORTRESS Response |
|-------------|-------------------|-------------------------|
| **Label Flipping** | AI thinks malware is "Safe" | Axiom Veto: Policy says malware, AI overruled |
| **Incremental Drift** | AI slowly becomes useless | Shadow Mirror: Drift detected vs Golden Baseline |
| **Targeted Trigger** | "When I see X, do nothing" | Forensic Replay: See exactly when Oracle learned "X" |

#### 🛠️ Sovereign Recovery (If Poisoned)

**Step 1: Forensic Rewind**
```bash
# Find when the AI's confidence in a malicious pattern began rising
./tools/ice-age/forensic-replay.sh --module oracle --topic ssh --since 48h
```

**Step 2: Differential Privacy**
Enable in `economics/config.yaml` to add mathematical noise—forces AI to only learn from strong, repeated patterns.

**Step 3: Snapshot Rollback**
1. Navigate to Vault Dashboard
2. Select "Pre-Incident" snapshot
3. Click "Restore Sovereign State"
4. System reverts to clean, non-poisoned intelligence

> *"TSM99 Sovereignty isn't just data residency—it's Cognitive Sovereignty."*

**One Script**: `./tools/ice-age/setup.sh` for complete sovereignty.

---

## ⚡ HOW IT WORKS (Under the Hood)

For those who want the details, here's what powers each feature:

| Feature | Internal Modules |
|---------|------------------|
| **AUTOPILOT** | Healing, Execution, Outcomes, Sandbox |
| **DEFENDER** | Detection, Simulation, Security, Telemetry |
| **SENTINEL** | Autonomy, Trust Ledger, Vault, Compliance |
| **ORACLE** | Memory, Learning, Policy Refinement, Training |
| **FORTRESS** | LLM, Economics, Data Resident, Network |

Total: **35 production-hardened modules** packaged into **5 simple toggles**.

---

## 🕐 CAUSAL TIME-TRAVEL (Forensic Replay)

> *This is NOT training rollback. This is NOT simple logs. This is **Causal Time-Travel for Autonomous Systems.***

### The Core Principle (Non-Negotiable)

**Deterministic Execution** = Same inputs + same policy + same model = **Same output every time**

| Rule | Implementation |
|------|----------------|
| No uncontrolled randomness | `torch.use_deterministic_algorithms(True)` |
| No async side effects | All actions have UUIDs |
| No hidden state mutation | Event-sourced everything |

### Event-Sourced Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              EVENT-SOURCED ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Sensor/Input ──→ EVENT LEDGER (append-only, immutable)       │
│                         │                                       │
│                         ▼                                       │
│                    DECISION VM ──→ Pure function               │
│                    (Oracle)        Same input = Same output    │
│                         │                                       │
│                         ▼                                       │
│                    ACTION EXEC ──→ Logged with UUID            │
│                         │                                       │
│                         ▼                                       │
│                    OUTCOME EVAL                                 │
│                         │                                       │
│                         ▼                                       │
│                    LEARNING LOG ──→ Deltas ONLY                │
│                                     (not weights)              │
│                                                                 │
│   🔒 State is DERIVED, not persisted. Events are truth.        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Model (The Ledger)

| Table | Purpose | Key |
|-------|---------|-----|
| `event_log` | Append-only events | `hash + prev_hash` (blockchain-style) |
| `decision_trace` | Model + policy version + input → output | `model_version, policy_version` |
| `action_exec` | Side effects logged | `execution_context` |
| `learning_delta` | Diffs, not weights | `before_hash, after_hash, delta_blob` |

> **Learning = git commit for AI, not code**

### Git-Like Operations

```bash
# Checkout state at specific time
oracle checkout --time "2026-01-12T12:41:02"

# Diff learning between deltas
oracle diff --from delta_331 --to delta_339

# Revert specific learning
oracle revert delta_334

# Branch reality for investigation
oracle branch incident_2026_01_12

# Cherry-pick policy fix (not weights)
oracle cherry-pick policy_fix_007
```

### Rewind Mechanism (Second-by-Second)

```
[ ⏪ ] 12:41:03
Event: inbound firewall log
Decision: classify as benign
Confidence: 0.92
Learning: reward +0.4

[ ⏪ ] 12:41:04
Event: privilege escalation
Decision: allow (❌)
Learning: pattern reinforced
         ↑
    "THIS decision polluted the model."
```

### 📸 Snapshot Checkpoints (Performance Optimization)

**Problem**: Replaying 100 million events to find one poisoned commit is computationally expensive.

**Solution**: Every 24 hours, flatten the ledger into a **Golden Snapshot**.

```
┌─────────────────────────────────────────────────────────────────┐
│              SNAPSHOT CHECKPOINT ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   DAY 1        DAY 2        DAY 3        DAY 4        NOW      │
│     │            │            │            │            │       │
│   ┌─▼─┐        ┌─▼─┐        ┌─▼─┐        ┌─▼─┐        ┌─▼─┐    │
│   │ 📸 │        │ 📸 │        │ 📸 │        │ 📸 │        │ 🔴 │    │
│   │SNAP│        │SNAP│        │SNAP│        │SNAP│        │LIVE│    │
│   └───┘        └───┘        └───┘        └───┘        └───┘    │
│     ↓                                       ↓            ↓      │
│   [Archive]                              [Active]    [Events]   │
│                                                                 │
│   Replay starts from nearest snapshot, not Day 1               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Checkpoint Type | Frequency | Contents | Retention |
|-----------------|-----------|----------|-----------|
| **Hourly Mini** | Every 1h | Event count + hash | 7 days |
| **Daily Golden** | Every 24h | Full state + weights + policies | 90 days |
| **Monthly Archive** | Every 30d | Compressed golden + all deltas | 7 years |

**Replay Performance:**

| Without Checkpoints | With Checkpoints |
|---------------------|------------------|
| Replay 100M events | Replay from nearest snapshot |
| **~45 minutes** | **~30 seconds** |
| High CPU/memory | Minimal resources |

```bash
# Create manual checkpoint
oracle snapshot create --name "pre-incident-443"

# List available checkpoints
oracle snapshot list

# Replay from specific checkpoint
oracle replay --from snapshot_2026_01_12 --to now

# Promote checkpoint to "trusted baseline"
oracle snapshot promote snapshot_2026_01_12 --golden
```

> *"Checkpoints = git tags for your AI's cognitive state."*

### Safe Autonomy Mode (Production)

| Component | Mode |
|-----------|------|
| Model weights | **Frozen** (read-only) |
| Learning | **Shadow only** (proposals, not updates) |
| Logs | **Immutable** (no UPDATE, no DELETE) |
| Decisions | **Deterministic** (seeded randomness) |
| Rollback | **Instant** (adapter swap) |
| Promotion | **Gated** (human approval) |

### Learning Gate Policy

```yaml
learning_rules:
  - condition: confidence < 0.8
    action: forbid
  - condition: incident_severity >= HIGH
    action: require_human_approval
  - condition: domain == "auth"
    action: shadow_learn_only
```

> *"The model SUGGESTS learning. Humans APPROVE. This is how AWS, Google, banks, and defense do it."*

---

## 🚀 QUICK START

### Option A: Full Sovereign (Recommended)
```bash
git clone https://github.com/noData0079/SecOPS.v1
cd SecOPS.v1
./tools/ice-age/setup.sh
```

### Option B: Developer Mode
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

### Access Points
- **Dashboard**: http://localhost:3000
- **Admin Panel**: http://localhost:3000/admin
- **API Docs**: http://localhost:8000/docs

---

## 📞 CONTACT

- **Founder**: founder@thesovereignmechanica.ai
- **Repository**: https://github.com/noData0079/SecOPS.v1
- **Documentation**: `/docs/` directory

---

*TSM99 — The Sovereign Mechanica v1.0.1*
*5 Features. 1 Platform. Zero Babysitting.*
