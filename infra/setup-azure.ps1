# Azure observability stack — Azure Monitor Workspace + Azure Managed Grafana
# Run from repo root: .\infra\setup-azure.ps1

$SUBSCRIPTION   = "5ef50a27-50a4-4d90-9695-da61b2309cf3"
$RESOURCE_GROUP = "trading-agents-prod"
$LOCATION       = "australiaeast"
$MONITOR_NAME   = "trading-agents-monitor"
$GRAFANA_NAME   = "trading-agents-grafana"

Write-Host "`n→ Setting subscription" -ForegroundColor Cyan
az account set --subscription $SUBSCRIPTION

Write-Host "→ Creating resource group" -ForegroundColor Cyan
az group create `
  --name     $RESOURCE_GROUP `
  --location $LOCATION `
  --output   none

Write-Host "→ Installing Azure Managed Grafana CLI extension" -ForegroundColor Cyan
az extension add --name amg --upgrade --only-show-errors

Write-Host "→ Creating Azure Monitor Workspace (managed Prometheus storage)" -ForegroundColor Cyan
az monitor account create `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --location       $LOCATION `
  --output         table

Write-Host "→ Creating Azure Managed Grafana" -ForegroundColor Cyan
az grafana create `
  --name           $GRAFANA_NAME `
  --resource-group $RESOURCE_GROUP `
  --location       $LOCATION `
  --output         table

# ── Collect outputs ───────────────────────────────────────────────────────────

$GRAFANA_ENDPOINT = az grafana show `
  --name           $GRAFANA_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "properties.endpoint" -o tsv

$PROMETHEUS_QUERY = az monitor account show `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "metrics.prometheusQueryEndpoint" -o tsv

$REMOTE_WRITE_URL = "${PROMETHEUS_QUERY}/api/v1/write"

# ── Save for later use (local prometheus config etc.) ────────────────────────

@"
GRAFANA_ENDPOINT=$GRAFANA_ENDPOINT
PROMETHEUS_QUERY=$PROMETHEUS_QUERY
REMOTE_WRITE_URL=$REMOTE_WRITE_URL
"@ | Set-Content -Path "infra\.azure-outputs"

Write-Host "`n✓ Done." -ForegroundColor Green
Write-Host ""
Write-Host "  Grafana :  https://$GRAFANA_ENDPOINT" -ForegroundColor Yellow
Write-Host "  Prom URL:  $REMOTE_WRITE_URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Outputs saved to infra/.azure-outputs"
