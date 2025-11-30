#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# SecOps AI — Kubernetes Deployment Script
#
# Deploys backend, frontend, and all manifests in infra/k8s/
#
# Usage:
#   ./infra/scripts/k8s_deploy.sh
#   KUBECONFIG=~/.kube/config ./infra/scripts/k8s_deploy.sh
#
###############################################################################

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
K8S_DIR="$ROOT_DIR/infra/k8s"

NAMESPACE="secops"

echo "============================================"
echo "   SecOps AI — Kubernetes Deployment Tool"
echo "============================================"
echo "Root directory: $ROOT_DIR"
echo "K8s directory:  $K8S_DIR"
echo "Deploying to namespace: $NAMESPACE"
echo ""

###############################################################################
# Check Kubeconfig
###############################################################################
if [[ -z "${KUBECONFIG:-}" ]]; then
  echo "⚠️  No KUBECONFIG provided. Using default: ~/.kube/config"
  export KUBECONFIG="$HOME/.kube/config"
fi

if [[ ! -f "$KUBECONFIG" ]]; then
  echo "❌ Kubeconfig not found: $KUBECONFIG"
  exit 1
fi

echo "📦 Using kubeconfig: $KUBECONFIG"

###############################################################################
# Ensure namespace exists
###############################################################################
echo "🔍 Checking namespace '$NAMESPACE'..."
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
  echo "📁 Creating namespace '$NAMESPACE'"
  kubectl create namespace "$NAMESPACE"
else
  echo "✔ Namespace exists."
fi

###############################################################################
# Apply all manifests in infra/k8s/
###############################################################################
echo ""
echo "🚀 Applying Kubernetes manifests from: $K8S_DIR"
kubectl apply -n "$NAMESPACE" -f "$K8S_DIR"

echo "✔ All manifests applied."
echo ""

###############################################################################
# Rollout Checks for Backend
###############################################################################
echo "🔎 Checking rollout status: backend"
if kubectl get deployment secops-backend -n "$NAMESPACE" >/dev/null 2>&1; then
  kubectl rollout status deployment/secops-backend -n "$NAMESPACE"
else
  echo "⚠️  Backend deployment not found. Skipping."
fi

###############################################################################
# Rollout Checks for Frontend
###############################################################################
echo "🔎 Checking rollout status: frontend"
if kubectl get deployment secops-frontend -n "$NAMESPACE" >/dev/null 2>&1; then
  kubectl rollout status deployment/secops-frontend -n "$NAMESPACE"
else
  echo "⚠️  Frontend deployment not found. Skipping."
fi

###############################################################################
# Show Services
###############################################################################
echo ""
echo "📡 Active Services:"
kubectl get svc -n "$NAMESPACE"

###############################################################################
# Show Pods
###############################################################################
echo ""
echo "📦 Active Pods:"
kubectl get pods -n "$NAMESPACE"

echo ""
echo "============================================"
echo "   SecOps AI — Deployment Complete 🎉"
echo "============================================"
echo ""
