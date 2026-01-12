# Use NVIDIA's official CUDA development image for compatibility
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Set non-interactive for automated builds
ENV DEBIAN_FRONTEND=noninteractive

# Install core system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    curl \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install fundamental AI libraries
RUN pip3 install --upgrade pip
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# --- THE SOVEREIGN CORE: UNSLOTH ---
# Install Unsloth with 4-bit quantization and Flash Attention 2 support
RUN pip3 install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
RUN pip3 install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes

# Install Backend API dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Set up local workspace
WORKDIR /app
COPY . .

# Environment variables for Sovereign Mode
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=http://tsm99-ollama:11434

# Expose the API port
EXPOSE 8000

# Start the TSM99 Recursive Backend
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
