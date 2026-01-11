#!/bin/bash
cd ~/projects/SecOps-ai
source .venv-iceage/bin/activate
cd backend/src
python -c "from core.autonomy import PolicyEngine, AutonomyLoop, ReplayEngine; print('[OK] Autonomy module imports successfully')"
