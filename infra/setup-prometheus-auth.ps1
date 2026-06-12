# Creates a service principal for local Prometheus → Azure Monitor remote_write,
# assigns the Monitoring Metrics Publisher role on the workspace,
# writes credentials into .env, and generates infra/prometheus/prometheus.local.yml.
#
# Run from repo root: .\infra\setup-prometheus-auth.ps1

$SUBSCRIPTION   = "5ef50a27-50a4-4d90-9695-da61b2309cf3"
$RESOURCE_GROUP = "trading-agents-prod"
$MONITOR_NAME   = "trading-agents-monitor"
$SP_NAME        = "trading-agents-prometheus"
$ENV_FILE       = ".env"

# ── 1. Get workspace resource ID + remote_write URL ──────────────────────────

Write-Host "`n→ Fetching Monitor Workspace details" -ForegroundColor Cyan

$WORKSPACE_ID = az monitor account show `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "id" -o tsv

$PROMETHEUS_QUERY = az monitor account show `
  --name           $MONITOR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query          "metrics.prometheusQueryEndpoint" -o tsv

$REMOTE_WRITE_URL = "$PROMETHEUS_QUERY/api/v1/write"

# ── 2. Create service principal + assign role ─────────────────────────────────

Write-Host "→ Creating service principal '$SP_NAME'" -ForegroundColor Cyan

$SP_JSON = az ad sp create-for-rbac `
  --name   $SP_NAME `
  --role   "Monitoring Metrics Publisher" `
  --scopes $WORKSPACE_ID `
  --output json | ConvertFrom-Json

$CLIENT_ID     = $SP_JSON.appId
$CLIENT_SECRET = $SP_JSON.password
$TENANT_ID     = $SP_JSON.tenant

# ── 3. Write credentials into .env ────────────────────────────────────────────

Write-Host "→ Writing credentials to $ENV_FILE" -ForegroundColor Cyan

# Replace placeholder lines in .env with real values
$content = Get-Content $ENV_FILE
$content = $content -replace "^AZURE_SP_CLIENT_ID=.*",     "AZURE_SP_CLIENT_ID=$CLIENT_ID"
$content = $content -replace "^AZURE_SP_CLIENT_SECRET=.*", "AZURE_SP_CLIENT_SECRET=$CLIENT_SECRET"
$content = $content -replace "^AZURE_SP_TENANT_ID=.*",     "AZURE_SP_TENANT_ID=$TENANT_ID"
$content = $content -replace "^PROMETHEUS_REMOTE_WRITE_URL=.*", "PROMETHEUS_REMOTE_WRITE_URL=$REMOTE_WRITE_URL"
$content | Set-Content $ENV_FILE

# ── 4. Generate prometheus.local.yml from .env values ────────────────────────

Write-Host "→ Generating infra/prometheus/prometheus.local.yml" -ForegroundColor Cyan

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

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host "`n✓ Done. Credentials written to .env — not printed here." -ForegroundColor Green
Write-Host ""
Write-Host "  prometheus.local.yml ready at infra/prometheus/"
Write-Host ""
Write-Host "  Next: download Prometheus for Windows and run:" -ForegroundColor Cyan
Write-Host "    https://github.com/prometheus/prometheus/releases/latest"
Write-Host "    (download the windows-amd64 zip, extract it)"
Write-Host ""
Write-Host "  Then run from the extracted folder:" -ForegroundColor Cyan
Write-Host "    .\prometheus.exe --config.file=`$(Resolve-Path infra\prometheus\prometheus.local.yml)"
