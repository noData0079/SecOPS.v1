#!/bin/bash
# tools/ice-age/cpu-only-mode.sh
# Configure system for CPU-only operation (no GPU required)

set -e

# Ensure we are root
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

log() {
    echo -e "\033[1;32m[CPU-MODE] $1\033[0m"
}

log "Configuring CPU-only mode for TSM99..."

# Set environment variables for CPU-only operation
export CUDA_VISIBLE_DEVICES=""
export TORCH_DEVICE="cpu"
export VLLM_CPU_ONLY="1"
export OLLAMA_NUM_GPU="0"

# Create persistent config
CONFIG_FILE="/etc/tsm99/cpu-mode.conf"
mkdir -p /etc/tsm99

cat > "$CONFIG_FILE" << 'EOF'
# TSM99 CPU-Only Mode Configuration
# GPU is OPTIONAL - this is the default mode

# Disable GPU for PyTorch
CUDA_VISIBLE_DEVICES=""
TORCH_DEVICE="cpu"

# Disable GPU for vLLM
VLLM_CPU_ONLY="1"

# Disable GPU for Ollama
OLLAMA_NUM_GPU="0"

# Use quantized models for efficiency
DEFAULT_MODEL="deepseek-coder:6.7b-instruct-q4_K_M"
FALLBACK_MODEL="qwen2.5:7b-instruct-q4_K_M"

# Memory limits for CPU inference
OMP_NUM_THREADS="4"
MKL_NUM_THREADS="4"
EOF

log "CPU-only configuration saved to: $CONFIG_FILE"

# Source for current session
source "$CONFIG_FILE"

# Verify no GPU usage
log "Verifying CPU-only mode..."

if command -v nvidia-smi &> /dev/null; then
    log "NVIDIA GPU detected but DISABLED (CUDA_VISIBLE_DEVICES='')"
fi

log "CPU-only mode ACTIVATED"
log ""
log "Recommended quantized models for CPU:"
log "  - deepseek-coder:6.7b-instruct-q4_K_M (4-bit, ~4GB RAM)"
log "  - qwen2.5:7b-instruct-q4_K_M (4-bit, ~5GB RAM)"
log "  - phi3:3.8b-instruct-q4_K_M (4-bit, ~2GB RAM)"
log ""
log "To install with Ollama:"
log "  ollama pull deepseek-coder:6.7b-instruct-q4_K_M"
