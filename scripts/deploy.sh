#!/usr/bin/env bash
# =============================================================
# CloudPulse deploy.sh
# Called by Terraform null_resource after infra provisioning.
# Builds images, pushes to ACR, deploys Helm to AKS cluster.
# Required env vars are injected by Terraform local-exec.
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
HELM_CHART="$ROOT_DIR/helm/cloudpulse"
SERVICES=("metrics-svc" "alerts-svc" "cost-svc" "frontend")

log()  { echo -e "\033[1;36m[CloudPulse]\033[0m $*"; }
ok()   { echo -e "\033[1;32m[✓]\033[0m $*"; }
fail() { echo -e "\033[1;31m[✗]\033[0m $*" >&2; exit 1; }

# ── Validate required env vars ────────────────────────────────
: "${PROJECT_NAME:?}" "${IMAGE_TAG:?}"
: "${AZURE_RG:?}"  "${AKS_NAME:?}" "${ACR_SERVER:?}" "${ACR_USERNAME:?}" "${ACR_PASSWORD:?}"

# ── Auto-generate frontend .env from Terraform outputs ────────
if [ -n "${ENTRA_CLIENT_ID:-}" ] && [ -n "${ENTRA_TENANT_ID:-}" ]; then
  log "Writing frontend/.env with Entra ID credentials..."
  cat > "$ROOT_DIR/frontend/.env" <<EOF
VITE_AZURE_CLIENT_ID=${ENTRA_CLIENT_ID}
VITE_AZURE_TENANT_ID=${ENTRA_TENANT_ID}
EOF
  ok "frontend/.env updated"
fi

# ── Build & push to ACR ───────────────────────────────────────
log "Authenticating with ACR..."
echo "$ACR_PASSWORD" | docker login "$ACR_SERVER" \
  --username "$ACR_USERNAME" --password-stdin

for svc in "${SERVICES[@]}"; do
  SRC_DIR="$ROOT_DIR/services/$svc"
  [ "$svc" = "frontend" ] && SRC_DIR="$ROOT_DIR/frontend"
  ACR_IMAGE="$ACR_SERVER/$PROJECT_NAME/$svc:$IMAGE_TAG"

  log "Building $svc..."
  docker build -t "$ACR_IMAGE" "$SRC_DIR"
  docker push "$ACR_IMAGE"
  ok "$svc → ACR: $ACR_IMAGE"
done

# ── Deploy to AKS ─────────────────────────────────────────────
log "Configuring kubectl for AKS ($AKS_NAME)..."
az aks get-credentials \
  --resource-group "$AZURE_RG" \
  --name "$AKS_NAME" \
  --context aks-cloudpulse \
  --overwrite-existing

log "Installing nginx-ingress on AKS..."
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --kube-context aks-cloudpulse \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer \
  --wait --timeout 20m

log "Deploying CloudPulse Helm chart to AKS..."
helm upgrade --install cloudpulse "$HELM_CHART" \
  --kube-context aks-cloudpulse \
  --namespace cloudpulse --create-namespace \
  -f "$HELM_CHART/values-azure.yaml" \
  --set global.imageRegistry="$ACR_SERVER/$PROJECT_NAME" \
  --set global.imageTag="$IMAGE_TAG" \
  --set global.azureClientId="$AZURE_CLIENT_ID" \
  --wait --timeout 20m

# ── Wait for LoadBalancer IP and write URL file ────────────────
log "Waiting for LoadBalancer IP..."

get_lb_ip() {
  local ctx="$1"
  for i in {1..24}; do
    IP=$(kubectl get ingress cloudpulse-ingress \
      --context "$ctx" \
      --namespace cloudpulse \
      -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
    [ -z "$IP" ] && IP=$(kubectl get ingress cloudpulse-ingress \
      --context "$ctx" \
      --namespace cloudpulse \
      -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
    if [ -n "$IP" ]; then
      echo "$IP"
      return 0
    fi
    log "  Attempt $i/24 — waiting for IP..."
    sleep 10
  done
  echo "PENDING"
}

AZURE_IP=$(get_lb_ip aks-cloudpulse)

printf '%s' "$AZURE_IP" > "$ROOT_DIR/.azure_url"

ok "============================================"
ok "Dashboard → http://$AZURE_IP"
ok "============================================"
