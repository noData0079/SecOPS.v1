# 🧱 TSM99 Final Autonomy Architecture (LOCKED)

> **Status**: FROZEN - Do not modify without explicit founder approval.

## Core Loop

```
OBSERVATION → MODEL → POLICY → TOOLS → OUTCOME → REPLAY
```

This loop is **autonomy**.

---

## Layer Breakdown

### 1. OBSERVATION
- Logs, metrics, events
- Input to decision engine

### 2. MODEL (DeepSeek-Coder 6.7B)
- **Single model only**
- Trained on infra + code
- JSON discipline
- Works on Colab T4 with QLoRA
- **Job**: Choose the next action (NOTHING ELSE)

### 3. POLICY (Deterministic Rules)
- **No ML** — This is the moat
- Auditable, explainable, trusted
- Enforces: action limits, risk gates, environment blocks

### 4. TOOLS (Sandboxed Executors)
- Static JSON registry
- Model NEVER executes directly
- Model emits: `{ "tool": "...", "args": {...} }`

### 5. OUTCOME
- Success / Fail / Metrics
- Fed back into next prompt

### 6. REPLAY (Offline Learning)
- Store incident → actions → outcome
- Re-simulate paths WITHOUT GPUs
- Update policy thresholds, not weights

---

## ⚠️ Design Rules (DO NOT BREAK)

| Rule | Reason |
|------|--------|
| ❌ Do not remove policy | System becomes unsafe |
| ❌ Do not let model execute commands | Disaster prevention |
| ❌ Do not chase bigger models | Cost explosion |
| ❌ Do not skip replay | Learning stops |
| ❌ Do not optimize for demos | Production breaks |

---

## File Locations

| Component | Path |
|-----------|------|
| Tool Registry | `backend/src/core/autonomy/tool_registry.json` |
| Policy Engine | `backend/src/core/autonomy/policy_engine.py` |
| Autonomy Loop | `backend/src/core/autonomy/loop.py` |
| Replay Engine | `backend/src/core/autonomy/replay.py` |

---

## Target Metrics

- **60–70% task automation**
- **Zero hallucinated actions**
- **Deterministic behavior**
- **Free compute**
- **Enterprise-safe design**
