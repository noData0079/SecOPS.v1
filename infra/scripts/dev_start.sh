#!/usr/bin/env bash
set -e

###############################################################################
# SecOps AI — Development Bootstrap Script
# Runs Backend + Frontend + Optional DB locally in parallel.
# Works on macOS, Linux, and WSL.
###############################################################################

echo "============================================"
echo "   SecOps AI — Local Development Launcher"
echo "============================================"
echo ""

# Detect directories
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

###############################################################################
# Function: start_backend
###############################################################################
start_backend() {
  echo "🔧 Starting FASTAPI backend..."
  cd "$BACKEND_DIR"

  # Ensure venv exists
  if [ ! -d "venv" ]; then
    echo "📦 Creating Python venv..."
    python3 -m venv venv
  fi

  # Activate venv
  source venv/bin/activate

  # Install deps if needed
  echo "📦 Installing backend dependencies..."
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt >/dev/null

  echo "🚀 Backend running → http://localhost:8000"
  uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
}

###############################################################################
# Function: start_frontend
###############################################################################
start_frontend() {
  echo "🎨 Starting Next.js frontend..."
  cd "$FRONTEND_DIR"

  # Install dependencies
  echo "📦 Installing frontend dependencies..."
  npm install >/dev/null

  echo "🚀 Frontend running → http://localhost:3000"
  npm run dev
}

###############################################################################
# Function: start_postgres (optional)
###############################################################################
start_postgres() {
  echo "🐘 Starting local PostgreSQL (Docker)..."

  docker run -d \
    --name secops-postgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=secops \
    -p 5432:5432 \
    postgres:15

  echo "📚 PostgreSQL running → localhost:5432"
}

###############################################################################
# Run all processes in parallel
###############################################################################

echo "What do you want to start?"
echo "1) Backend only"
echo "2) Frontend only"
echo "3) Backend + Frontend"
echo "4) Backend + Frontend + Postgres"
echo ""
read -p "Select option (1-4): " choice

case $choice in
  1)
    start_backend
    ;;
  2)
    start_frontend
    ;;
  3)
    # Run both with concurrency
    start_backend & 
    BACK_PID=$!
    start_frontend &
    FRONT_PID=$!

    wait $BACK_PID $FRONT_PID
    ;;
  4)
    start_postgres
    start_backend &
    BACK_PID=$!
    start_frontend &
    FRONT_PID=$!

    wait $BACK_PID $FRONT_PID
    ;;
  *)
    echo "❌ Invalid choice. Exiting."
    exit 1
    ;;
esac
