# Dockerfile 
###############################
# Stage 1 — Builder
###############################
FROM python:3.10-slim AS builder

# Avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies to a wheels directory (cacheable)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


###############################
# Stage 2 — Final Runtime
###############################
FROM python:3.10-slim

# Create user for security
RUN useradd -m secopsuser

WORKDIR /app

# Install minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

# Copy backend source code
COPY src ./src
COPY pyproject.toml ./pyproject.toml

# Expose API port
EXPOSE 8000

# Environment (safe defaults)
ENV ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Healthcheck (optional but recommended)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER secopsuser

# Production server command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
