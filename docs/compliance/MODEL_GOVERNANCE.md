# Model Governance Policy

## Overview
TSM99 enforces strict governance over the use of Large Language Models (LLMs), treating them as untrusted components within a deterministic safety shell.

## 1. Single Model Policy
The system is architected to use a single, specific model to ensure predictable behavior and reduce attack surface.

**Evidence Source:** `docs/AUTONOMY_ARCHITECTURE.md`

- **Model**: DeepSeek-Coder 6.7B
- **Restriction**: "Single model only", "No chasing bigger models".
- **Training**: Fine-tuned on infrastructure and code specific to the domain.

## 2. No Direct Execution
The model never executes code or commands directly. It functions solely as a decision engine that selects tools from a pre-approved registry.

**Evidence Source:** `backend/src/core/autonomy/loop.py`

- **Flow**: `OBSERVATION → MODEL → POLICY → TOOLS`
- **Output**: JSON payload `{ "tool": "...", "args": {...} }`
- **Constraint**: The model's output is parsed and validated before any action is taken.

## 3. Deterministic Policy Layer ("The Moat")
All model outputs are filtered through a deterministic Policy Engine that contains **NO ML**.

**Evidence Source:** `backend/src/core/autonomy/policy_engine.py`

- **Purpose**: "The model is never trusted to execute."
- **Rules**: Hardcoded safety checks (e.g., Risk Levels, Production Blocks).
- **Override**: Policy decisions always supersede model outputs.

## 4. Confidence Thresholds
Actions are gated by confidence scores derived from the model's output.

- **High Risk**: Requires > 0.85 confidence.
- **Medium Risk**: Requires > 0.70 confidence.
- **Low Risk**: Standard execution.

## 5. Offline Learning (Replay)
Model behavior is improved via offline replay of logs, not online learning.
- **Method**: Analysis of `ReplayEntry` logs.
- **Updates**: Policy thresholds and tool definitions are updated based on replay outcomes; model weights are not modified online.
