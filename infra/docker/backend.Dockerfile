# ===========================
#  Base builder image
# ===========================
FROM python:3.11-slim AS builder

# System deps (build tools, git if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only dependency manifests first (better layer caching)
COPY backend/requirements.txt ./requirements.txt

# Create virtual env for dependencies
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ===========================
#  Runtime image
# ===========================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Minimal system deps (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source code
COPY backend/ ./backend/

# Optional: env for FastAPI / Uvicorn
ENV APP_MODULE="backend.src.main:app" \
    HOST="0.0.0.0" \
    PORT="8000" \
    WORKERS="2"

EXPOSE 8000

# Healthcheck (basic)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD \
  curl -f http://localhost:8000/health || exit 1

# Default command: run FastAPI with Uvicorn
CMD ["sh", "-c", "uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT} --workers ${WORKERS}"]
