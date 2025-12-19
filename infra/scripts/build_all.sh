#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# T79 AI — Build All Docker Images
#
# Builds:
#   - Backend image (FastAPI)
#   - Frontend image (Next.js)
#
# Usage:
#   ./infra/scripts/build_all.sh
#   ./infra/scripts/build_all.sh v0.1.0
#   REGISTRY=ghcr.io/your-org ./infra/scripts/build_all.sh v0.1.0
#
# If REGISTRY is set, images will be tagged as:
#   $REGISTRY/t79-backend:<tag>
#   $REGISTRY/t79-frontend:<tag>
#
# Otherwise, they will be tagged locally as:
#   t79-backend:<tag>
#   t79-frontend:<tag>
###############################################################################

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

TAG="${1:-latest}"
REGISTRY="${REGISTRY:-}"

BACKEND_DOCKERFILE="$ROOT_DIR/infra/docker/backend.Dockerfile"
FRONTEND_DOCKERFILE="$ROOT_DIR/infra/docker/frontend.Dockerfile"

if [[ -n "$REGISTRY" ]]; then
  BACKEND_IMAGE="${REGISTRY%/}/t79-backend:${TAG}"
  FRONTEND_IMAGE="${REGISTRY%/}/t79-frontend:${TAG}"
else
  BACKEND_IMAGE="t79-backend:${TAG}"
  FRONTEND_IMAGE="t79-frontend:${TAG}"
fi

echo "============================================"
echo "   T79 AI — Build All Docker Images"
echo "============================================"
echo "Root directory:     $ROOT_DIR"
echo "Backend Dockerfile: $BACKEND_DOCKERFILE"
echo "Frontend Dockerfile:$FRONTEND_DOCKERFILE"
echo "Tag:                $TAG"
if [[ -n "$REGISTRY" ]]; then
  echo "Registry:           $REGISTRY"
else
  echo "Registry:           (local only)"
fi
echo ""

###############################################################################
# Build Backend
###############################################################################
echo "🔧 Building backend image: $BACKEND_IMAGE"
docker build \
  -f "$BACKEND_DOCKERFILE" \
  -t "$BACKEND_IMAGE" \
  "$ROOT_DIR"

echo "✅ Backend image built: $BACKEND_IMAGE"
echo ""

###############################################################################
# Build Frontend
###############################################################################
echo "🎨 Building frontend image: $FRONTEND_IMAGE"
docker build \
  -f "$FRONTEND_DOCKERFILE" \
  -t "$FRONTEND_IMAGE" \
  "$ROOT_DIR"

echo "✅ Frontend image built: $FRONTEND_IMAGE"
echo ""

###############################################################################
# Summary
###############################################################################
echo "============================================"
echo "   Build Complete"
echo "============================================"
echo "Backend image:  $BACKEND_IMAGE"
echo "Frontend image: $FRONTEND_IMAGE"
echo ""

if [[ -n "$REGISTRY" ]]; then
  cat <<EOF
To push images:

  docker push $BACKEND_IMAGE
  docker push $FRONTEND_IMAGE

EOF
else
  cat <<EOF
Images are available locally.

To run:

  docker run --rm -p 8000:8000 $BACKEND_IMAGE
  docker run --rm -p 3000:3000 $FRONTEND_IMAGE

EOF
fi
