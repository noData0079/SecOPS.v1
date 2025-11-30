#!/usr/bin/env bash
set -e

###############################################################################
# SecOps AI — Database Migration Script
# Uses Alembic to run migrations OR create new revision files.
###############################################################################

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

ALEMBIC_DIR="$BACKEND_DIR/db"
ENV_FILE="$BACKEND_DIR/.env"

echo "============================================"
echo "     SecOps AI — Database Migration Tool"
echo "============================================"
echo ""

# -----------------------------------------------------------------------------
# Load .env if exists (for DATABASE_URL)
# -----------------------------------------------------------------------------
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
  echo "📦 Loaded environment variables from .env"
else
  echo "⚠️  No .env found. Ensure DATABASE_URL is exported."
fi

# -----------------------------------------------------------------------------
# Check Alembic installation and config
# -----------------------------------------------------------------------------
if [ ! -f "$BACKEND_DIR/alembic.ini" ]; then
  echo "❌ alembic.ini not found in backend/. Make sure Alembic is initialized."
  exit 1
fi

if ! command -v alembic >/dev/null 2>&1; then
  echo "❌ Alembic is not installed."
  echo "➡️  Install it via: pip install alembic"
  exit 1
fi

# -----------------------------------------------------------------------------
# Menu options
# -----------------------------------------------------------------------------
echo "📘 What do you want to do?"
echo "1) Run migrations (upgrade to latest)"
echo "2) Create new migration (autogenerate)"
echo "3) Downgrade one revision"
echo "4) Downgrade to base"
echo "5) Show current revision"
echo ""
read -p "Select option (1-5): " choice

cd "$BACKEND_DIR"

case $choice in
  1)
    echo "🚀 Running migrations → alembic upgrade head"
    alembic upgrade head
    echo "✅ Migrations completed."
    ;;
  2)
    read -p "Enter migration message: " msg
    if [ -z "$msg" ]; then
      echo "❌ Migration message cannot be empty."
      exit 1
    fi
    echo "📝 Creating new migration → alembic revision --autogenerate"
    alembic revision --autogenerate -m "$msg"
    echo "✅ Migration file created."
    ;;
  3)
    echo "⚠️  Downgrading one revision..."
    alembic downgrade -1
    echo "🔻 Downgraded by one revision."
    ;;
  4)
    echo "⚠️  FULL RESET: Downgrade to base."
    read -p "Are you sure? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
      alembic downgrade base
      echo "🧹 Rolled back all migrations to base."
    else
      echo "❌ Cancelled."
    fi
    ;;
  5)
    echo "📍 Current revision:"
    alembic current
    ;;
  *)
    echo "❌ Invalid option."
    exit 1
    ;;
esac
