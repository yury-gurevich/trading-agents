# setup-container-apps.ps1 — Deploy Container Apps Environment and write
# outputs into .env.
#
# Prerequisites:
#   az CLI >= 2.60, logged in (az login)
#
# Run from repo root:
#   pwsh infra/setup-container-apps.ps1
#
# Re-running is safe (idempotent). On first run (~2 min) it creates:
#   • Log Analytics Workspace  (trading-agents-logs)
#   • Container Apps Environment  (trading-agents-env)
#
# After this script succeeds, run deploy.sh to build and push the container
# image and create/update the Container App itself.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SUBSCRIPTION   = "5ef50a27-50a4-4d90-9695-da61b2309cf3"
$RESOURCE_GROUP = "traiding-agent"
$LOCATION       = "australiaeast"
$PREFIX         = "trading-agents"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ENV_FILE   = Join-Path $SCRIPT_DIR ".." ".env"
$BICEP_FILE = Join-Path $SCRIPT_DIR "container-apps.bicep"

# ── 1. Set subscription ───────────────────────────────────────────────────────

Write-Host "`n→ Setting subscription ${SUBSCRIPTION}" -ForegroundColor Cyan
az account set --subscription $SUBSCRIPTION

# ── 2. Ensure resource group exists ──────────────────────────────────────────

Write-Host "→ Creating resource group ${RESOURCE_GROUP} in ${LOCATION} (idempotent)" -ForegroundColor Cyan
az group create `
  --name     $RESOURCE_GROUP `
  --location $LOCATION `
  --output   none

# ── 3. Ensure Bicep CLI is installed ────────────────────────────────────────

Write-Host "→ Ensuring Bicep CLI is installed" -ForegroundColor Cyan
az bicep install 2>$null; az bicep upgrade 2>$null

# ── 4. Deploy Bicep stack ────────────────────────────────────────────────────

Write-Host "→ Deploying container-apps.bicep (~2 min on first run)" -ForegroundColor Cyan
$RAW = az deployment group create `
  --resource-group  $RESOURCE_GROUP `
  --template-file   $BICEP_FILE `
  --parameters      location=$LOCATION prefix=$PREFIX `
  --query           "properties.outputs" `
  --output          json

if (-not $RAW) {
  Write-Host "✗ Bicep deployment returned no output. Check the error above." -ForegroundColor Red
  exit 1
}

$OUTPUT = $RAW | ConvertFrom-Json

$CA_ENV_NAME       = $OUTPUT.caEnvName.value
$CA_ENV_ID         = $OUTPUT.caEnvId.value
$CA_DEFAULT_DOMAIN = $OUTPUT.caDefaultDomain.value
$LA_WORKSPACE_ID   = $OUTPUT.logAnalyticsWorkspaceId.value

Write-Host ""
Write-Host "  CA env:     ${CA_ENV_NAME}" -ForegroundColor Green
Write-Host "  Domain:     ${CA_DEFAULT_DOMAIN}" -ForegroundColor Green
Write-Host "  LA ID:      ${LA_WORKSPACE_ID}" -ForegroundColor Green

# ── 4. Write outputs to .env ─────────────────────────────────────────────────
# Replaces the placeholder lines in the Azure Container Apps section using
# the same line-replace pattern as setup-prometheus-auth.ps1.

Write-Host "`n→ Writing outputs to .env" -ForegroundColor Cyan

$today   = Get-Date -Format "yyyy-MM-dd HH:mm"
$content = Get-Content (Resolve-Path $ENV_FILE)

$content = $content -replace "^AZURE_CA_ENV_NAME=.*",       "AZURE_CA_ENV_NAME=${CA_ENV_NAME}"
$content = $content -replace "^AZURE_CA_ENV_ID=.*",         "AZURE_CA_ENV_ID=${CA_ENV_ID}"
$content = $content -replace "^AZURE_CA_DEFAULT_DOMAIN=.*", "AZURE_CA_DEFAULT_DOMAIN=${CA_DEFAULT_DOMAIN}"
$content = $content -replace "^AZURE_LA_WORKSPACE_ID=.*",   "AZURE_LA_WORKSPACE_ID=${LA_WORKSPACE_ID}"

# Update the "last run" datestamp in the section header
$content = $content -replace `
  "(# Set by infra/setup-container-apps\.ps1 — last run:).*", `
  "`$1 ${today}"

$content | Set-Content (Resolve-Path $ENV_FILE) -Encoding UTF8

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "✓ Container Apps Environment ready." -ForegroundColor Green
Write-Host ""
Write-Host "  AZURE_CA_ENV_NAME       = ${CA_ENV_NAME}"
Write-Host "  AZURE_CA_DEFAULT_DOMAIN = ${CA_DEFAULT_DOMAIN}"
Write-Host "  AZURE_LA_WORKSPACE_ID   = ${LA_WORKSPACE_ID}"
Write-Host ""
Write-Host "  Next step: run ./infra/deploy.sh to build and push the container image." -ForegroundColor Yellow
