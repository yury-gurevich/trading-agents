# Creates a service principal for local Prometheus → Azure Monitor remote_write,
# assigns the Monitoring Metrics Publisher role on the workspace,
# and writes infra/prometheus/prometheus.local.yml ready to run.

$SUBSCRIPTION   = "5ef50a27-50a4-4d90-9695-da61b2309cf3"
$RESOURCE_GROUP = "trading-agents-prod"
$MONITOR_NAME   = "trading-agents-monitor"
$SP_NAME        = "trading-agents-prometheus"

# ── 1. Get workspace resource ID ──────────────────────────────────────────────

Write-Host "`n→ Fetching Monitor Workspace details" -ForegroundColor Cyan
$WORKSPACE_ID = az monitor account show `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "id" -o tsv

$REMOTE_WRITE_URL = az monitor account show `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "metrics.prometheusQueryEndpoint" -o tsv
$REMOTE_WRITE_URL = "$REMOTE_WRITE_URL/api/v1/write"

# ── 2. Create service principal + assign role ─────────────────────────────────

Write-Host "→ Creating service principal '$SP_NAME' with Monitoring Metrics Publisher role" -ForegroundColor Cyan
$SP_JSON = az ad sp create-for-rbac `
  --name   $SP_NAME `
  --role   "Monitoring Metrics Publisher" `
  --scopes $WORKSPACE_ID `
  --output json | ConvertFrom-Json

$CLIENT_ID     = $SP_JSON.appId
$CLIENT_SECRET = $SP_JSON.password
$TENANT_ID     = $SP_JSON.tenant

Write-Host "  client_id : $CLIENT_ID"
Write-Host "  tenant_id : $TENANT_ID"

# ── 3. Write prometheus.local.yml ─────────────────────────────────────────────

Write-Host "→ Writing infra/prometheus/prometheus.local.yml" -ForegroundColor Cyan

$PROM_CONFIG = @"
global:
  scrape_interval: 15s
  external_labels:
    app: trading-agents
    environment: local

scrape_configs:
  - job_name: trading_agents
    static_configs:
      - targets: ["localhost:8000"]
    metrics_path: /metrics

remote_write:
  - url: "$REMOTE_WRITE_URL"
    oauth2:
      client_id:     "$CLIENT_ID"
      client_secret: "$CLIENT_SECRET"
      token_url:     "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token"
      scopes:
        - "https://monitor.azure.com/.default"
    queue_config:
      max_samples_per_send: 1000
      max_shards: 10
      capacity: 2500
    write_relabel_configs:
      - source_labels: [__name__]
        regex: "trading_agents_.*"
        action: keep
"@

$PROM_CONFIG | Set-Content -Path "infra\prometheus\prometheus.local.yml"

# ── 4. Save SP credentials to .azure-outputs ─────────────────────────────────

Add-Content -Path "infra\.azure-outputs" -Value ""
Add-Content -Path "infra\.azure-outputs" -Value "SP_CLIENT_ID=$CLIENT_ID"
Add-Content -Path "infra\.azure-outputs" -Value "SP_TENANT_ID=$TENANT_ID"
Add-Content -Path "infra\.azure-outputs" -Value "REMOTE_WRITE_URL=$REMOTE_WRITE_URL"
# Note: SP secret is NOT saved to disk. Store it in your password manager.

Write-Host "`n✓ Done." -ForegroundColor Green
Write-Host ""
Write-Host "  prometheus.local.yml written to infra/prometheus/"
Write-Host ""
Write-Host "  IMPORTANT: Save this secret in your password manager now —" -ForegroundColor Yellow
Write-Host "  it will NOT be shown again and is NOT saved to disk:" -ForegroundColor Yellow
Write-Host "  SP secret: $CLIENT_SECRET" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Next: download Prometheus for Windows and run it:" -ForegroundColor Cyan
Write-Host "  https://github.com/prometheus/prometheus/releases/latest"
Write-Host "  Extract, then: .\prometheus.exe --config.file=infra\prometheus\prometheus.local.yml"
