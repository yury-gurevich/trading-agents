#!/usr/bin/env bash
# deploy.sh — one-shot Azure infrastructure + image deployment for trading-agents.
#
# Prerequisites:
#   az CLI >= 2.60    (brew install azure-cli  OR  winget install Microsoft.AzureCLI)
#   docker            (Docker Desktop or Rancher Desktop)
#   Container Apps Environment already created:
#     pwsh infra/setup-container-apps.ps1   ← run once before first deploy
#
# Usage:
#   chmod +x infra/deploy.sh
#   ./infra/deploy.sh               # first run: creates all resources
#   ./infra/deploy.sh --images-only # rebuild and push images without re-running Bicep
#
# The script is idempotent: re-running it updates what changed.

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────

SUBSCRIPTION="5ef50a27-50a4-4d90-9695-da61b2309cf3"
RESOURCE_GROUP="trading-agents"
LOCATION="australiaeast"
PREFIX=""
IMAGE_TAG="${IMAGE_TAG:-latest}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGES_ONLY=false
if [[ "${1:-}" == "--images-only" ]]; then
  IMAGES_ONLY=true
fi

# ── 1. Login + subscription ───────────────────────────────────────────────────

echo "→ Setting subscription ${SUBSCRIPTION}"
az account set --subscription "${SUBSCRIPTION}"

# ── 1a. Prerequisite: Container Apps Environment must exist ───────────────────

if ! az containerapp env show \
       --name "${PREFIX}-env" \
       --resource-group "${RESOURCE_GROUP}" \
       --output none 2>/dev/null; then
  echo ""
  echo "✗ Container Apps Environment '${PREFIX}-env' not found."
  echo "  Run first:  pwsh infra/setup-container-apps.ps1"
  exit 1
fi

# ── 2. Resource group ─────────────────────────────────────────────────────────

echo "→ Creating resource group ${RESOURCE_GROUP} in ${LOCATION}"
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --output none

# ── 3. Bicep deployment ───────────────────────────────────────────────────────

if [[ "${IMAGES_ONLY}" == false ]]; then
  echo "→ Deploying Bicep stack (this takes ~3 minutes on first run)"
  DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group "${RESOURCE_GROUP}" \
    --template-file "${SCRIPT_DIR}/main.bicep" \
    --parameters "${SCRIPT_DIR}/parameters.json" \
    --query properties.outputs \
    --output json)

  ACR_LOGIN_SERVER=$(echo "${DEPLOYMENT_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['acrLoginServer']['value'])")
  REMOTE_WRITE_URL=$(echo "${DEPLOYMENT_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['remoteWriteUrl']['value'])")
  MANAGED_IDENTITY_CLIENT_ID=$(echo "${DEPLOYMENT_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['managedIdentityClientId']['value'])")
  GRAFANA_ENDPOINT=$(echo "${DEPLOYMENT_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['grafanaEndpoint']['value'])")

  # Persist outputs so --images-only runs can reuse them
  cat > "${SCRIPT_DIR}/.deploy-outputs" <<EOF
ACR_LOGIN_SERVER=${ACR_LOGIN_SERVER}
REMOTE_WRITE_URL=${REMOTE_WRITE_URL}
MANAGED_IDENTITY_CLIENT_ID=${MANAGED_IDENTITY_CLIENT_ID}
GRAFANA_ENDPOINT=${GRAFANA_ENDPOINT}
EOF
  echo "→ Outputs saved to infra/.deploy-outputs"
else
  # shellcheck source=/dev/null
  source "${SCRIPT_DIR}/.deploy-outputs"
  echo "→ Loaded outputs from infra/.deploy-outputs"
fi

# ── 4. Generate prometheus.yml with real values ───────────────────────────────

echo "→ Generating prometheus.yml with remote_write URL"
sed \
  -e "s|REMOTE_WRITE_URL|${REMOTE_WRITE_URL}|g" \
  -e "s|MANAGED_IDENTITY_CLIENT_ID|${MANAGED_IDENTITY_CLIENT_ID}|g" \
  "${SCRIPT_DIR}/prometheus/prometheus.yml" \
  > "${SCRIPT_DIR}/prometheus/prometheus.generated.yml"

# ── 5. ACR login ──────────────────────────────────────────────────────────────

echo "→ Logging in to ACR ${ACR_LOGIN_SERVER}"
az acr login --name "${ACR_LOGIN_SERVER%%.*}"

# ── 6. Build and push trading-agents image ────────────────────────────────────

echo "→ Building trading-agents:${IMAGE_TAG}"
docker build \
  --tag "${ACR_LOGIN_SERVER}/${PREFIX}:${IMAGE_TAG}" \
  --file "${REPO_ROOT}/Dockerfile" \
  "${REPO_ROOT}"

echo "→ Pushing trading-agents:${IMAGE_TAG}"
docker push "${ACR_LOGIN_SERVER}/${PREFIX}:${IMAGE_TAG}"

# ── 7. Build and push Prometheus sidecar image ────────────────────────────────

echo "→ Building prometheus-trading:${IMAGE_TAG}"
# Build from a temp context so the generated config is named prometheus.yml
PROM_BUILD_DIR=$(mktemp -d)
cp "${SCRIPT_DIR}/prometheus/Dockerfile" "${PROM_BUILD_DIR}/"
cp "${SCRIPT_DIR}/prometheus/prometheus.generated.yml" "${PROM_BUILD_DIR}/prometheus.yml"
docker build \
  --tag "${ACR_LOGIN_SERVER}/prometheus-trading:${IMAGE_TAG}" \
  "${PROM_BUILD_DIR}"
rm -rf "${PROM_BUILD_DIR}"

echo "→ Pushing prometheus-trading:${IMAGE_TAG}"
docker push "${ACR_LOGIN_SERVER}/prometheus-trading:${IMAGE_TAG}"

# ── 8. Update Container App to pick up new images ─────────────────────────────

echo "→ Restarting Container App to pull new images"
az containerapp update \
  --name "${PREFIX}" \
  --resource-group "${RESOURCE_GROUP}" \
  --image "${ACR_LOGIN_SERVER}/${PREFIX}:${IMAGE_TAG}" \
  --output none

# ── 9. Import Grafana dashboard ───────────────────────────────────────────────

echo "→ Importing trading-agents Grafana dashboard"
GRAFANA_NAME="${PREFIX}-grafana"
az grafana dashboard import \
  --name "${GRAFANA_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --definition "@${SCRIPT_DIR}/grafana/dashboards/trading-agents.json" \
  --output none 2>/dev/null || echo "   (dashboard already exists or az grafana extension not installed — import manually)"

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "✓ Deployment complete."
echo ""
echo "  Grafana:  ${GRAFANA_ENDPOINT}"
echo "  ACR:      ${ACR_LOGIN_SERVER}"
echo ""
echo "  First-time Grafana setup:"
echo "  1. Open ${GRAFANA_ENDPOINT}"
echo "  2. Go to Connections → Data sources → Add data source → Prometheus"
echo "  3. URL: ${REMOTE_WRITE_URL%/api/v1/write}"
echo "  4. Auth: Azure authentication → Managed Identity"
echo "  5. Dashboards → Import → Upload JSON → infra/grafana/dashboards/trading-agents.json"
