# Wires the Azure Monitor Workspace to Grafana as a native Prometheus data source,
# assigns the Monitoring Reader role to Grafana's managed identity,
# and updates the imported dashboard to use the real data source UID.
#
# Run from repo root: .\infra\setup-grafana-datasource.ps1

$RESOURCE_GROUP = "trading-agents-prod"
$MONITOR_NAME   = "trading-agents-monitor"
$GRAFANA_NAME   = "trading-agents-grafana"
$DS_UID         = "azure-monitor-prometheus"

# ── 1. Gather IDs ─────────────────────────────────────────────────────────────

Write-Host "`n→ Fetching resource IDs" -ForegroundColor Cyan

$GRAFANA_PRINCIPAL = az grafana show `
  --name           $GRAFANA_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "identity.principalId" -o tsv

$WORKSPACE_ID = az monitor account show `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "id" -o tsv

$QUERY_ENDPOINT = az monitor account show `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "metrics.prometheusQueryEndpoint" -o tsv

Write-Host "  Grafana principal : $GRAFANA_PRINCIPAL"
Write-Host "  Prometheus URL    : $QUERY_ENDPOINT"

# ── 2. Grant Grafana's managed identity Monitoring Reader on the workspace ────

Write-Host "→ Assigning Monitoring Reader to Grafana managed identity" -ForegroundColor Cyan
az role assignment create `
  --assignee   $GRAFANA_PRINCIPAL `
  --role       "Monitoring Reader" `
  --scope      $WORKSPACE_ID `
  --output     none 2>&1 | Where-Object { $_ -notmatch "already exists" }

# ── 3. Create Prometheus data source with a fixed UID ─────────────────────────

Write-Host "→ Creating Prometheus data source (uid: $DS_UID)" -ForegroundColor Cyan

$DS_DEF = [ordered]@{
  name     = "Azure Monitor Prometheus"
  type     = "prometheus"
  uid      = $DS_UID
  url      = $QUERY_ENDPOINT
  access   = "proxy"
  jsonData = [ordered]@{
    httpMethod       = "POST"
    azureCredentials = @{ authType = "msi" }
  }
} | ConvertTo-Json -Depth 5 -Compress

az grafana data-source create `
  --name           $GRAFANA_NAME `
  --resource-group $RESOURCE_GROUP `
  --definition     $DS_DEF `
  --output         none

# ── 4. Patch the imported dashboard to use the real data source UID ───────────

Write-Host "→ Patching dashboard data source references" -ForegroundColor Cyan

# Read the current dashboard from Grafana, replace ${DS_PROMETHEUS} with the real UID
$current = az grafana dashboard show `
  --name           $GRAFANA_NAME `
  --resource-group $RESOURCE_GROUP `
  --dashboard      "trading-agents-main" `
  --output         json | ConvertFrom-Json

$dashJson = $current | ConvertTo-Json -Depth 20 -Compress
$dashJson = $dashJson -replace [regex]::Escape('${DS_PROMETHEUS}'), $DS_UID

# az grafana dashboard update expects the dashboard model wrapped in {"dashboard": ...}
$wrapped = "{`"dashboard`":$dashJson,`"overwrite`":true}"
$tmpFile = [System.IO.Path]::GetTempFileName() + ".json"
$wrapped | Set-Content -Path $tmpFile

az grafana dashboard update `
  --name           $GRAFANA_NAME `
  --resource-group $RESOURCE_GROUP `
  --definition     $tmpFile `
  --output         none

Remove-Item $tmpFile

# ── Done ──────────────────────────────────────────────────────────────────────

$GRAFANA_URL = az grafana show `
  --name           $GRAFANA_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "properties.endpoint" -o tsv

Write-Host "`n✓ Done." -ForegroundColor Green
Write-Host ""
Write-Host "  Open your dashboard:" -ForegroundColor Yellow
Write-Host "  $GRAFANA_URL/d/trading-agents-main"
