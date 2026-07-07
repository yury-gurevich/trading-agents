# deploy-agents.ps1 — One-command fleet deploy/teardown for Azure Container Apps.
#
#   pwsh infra/deploy-agents.ps1 preflight   # just the readiness checks
#   pwsh infra/deploy-agents.ps1 up -Tag s103 # preflight → schema → master → 12 agents + cron job
#   pwsh infra/deploy-agents.ps1 down         # delete apps + dispatcher job
#
# Creds (all gitignored): infra/ghcr.local.json and infra/key-vault.local.json.
# POSTGRES_DSN is loaded from .env/process env.

param(
  [ValidateSet('preflight', 'up', 'down')]
  [string]$Action = 'preflight',
  [string]$Tag = 'latest',
  [string]$MasterScaleStart = '25 22 * * *',
  [string]$AgentScaleStart = '30 22 * * *',
  [string]$ScaleEnd = '30 00 * * *',
  [string]$ScaleTimezone = 'UTC',
  [int]$ScaleDesiredReplicas = 1,
  [string]$DispatcherCron = '30 22 * * *'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Config ────────────────────────────────────────────────────────────────────
$SUB = "5ef50a27-50a4-4d90-9695-da61b2309cf3"
$RG = "trading-agents"
$ENV_NAME = "trading-agents-env"
$REGISTRY = "ghcr.io"
$OWNER = "yury-gurevich"
$DISPATCHER_JOB = "dispatcher-cron"
# Container App name → GHCR image suffix (app names can't contain underscores).
$AGENTS = [ordered]@{
  scanner = "scanner"; analyst = "analyst"; "portfolio-manager" = "portfolio_manager"
  execution = "execution"; monitor = "monitor"; reporter = "reporter"
  forecaster = "forecaster"; operator = "operator"; supervisor = "supervisor"
  curator = "curator"; researcher = "researcher"; provider = "provider"
}

# ── UI helpers ────────────────────────────────────────────────────────────────
function Line($t) { Write-Host "│ $t" }
function Head($t) { Write-Host "│" ; Write-Host "│ $t" -ForegroundColor Yellow }
function Top($t) { Write-Host ("┌─ $t " + ("─" * [Math]::Max(0, 54 - $t.Length))) -ForegroundColor Cyan }
function Bot { Write-Host "└────────────────────────────────────────────────────────────" -ForegroundColor Cyan }
function Check($ok, $label) {
  if ($ok) { Write-Host "│   " -NoNewline; Write-Host "[OK] " -ForegroundColor Green -NoNewline; Write-Host $label }
  else { Write-Host "│   " -NoNewline; Write-Host "[XX] " -ForegroundColor Red -NoNewline; Write-Host $label }
}

# ── Cred loaders ──────────────────────────────────────────────────────────────
function Load-Json($name) {
  $p = Join-Path $PSScriptRoot $name
  if (-not (Test-Path $p)) { return $null }
  Get-Content $p -Raw | ConvertFrom-Json
}

function Load-DotEnv {
  $p = Join-Path $PSScriptRoot "..\.env"
  if (-not (Test-Path $p)) { return }
  foreach ($line in Get-Content $p) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { continue }
    $key = $line.Substring(0, $idx).Trim()
    $value = $line.Substring($idx + 1).Trim()
    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
      $value = $value.Substring(1, $value.Length - 2)
    }
    if (-not [Environment]::GetEnvironmentVariable($key, "Process")) {
      [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
  }
}

function Test-PostgresDsn {
  if (-not $env:POSTGRES_DSN) { return $false }
  $py = "import os, psycopg; d=os.environ.get('POSTGRES_DSN',''); " +
        "c=psycopg.connect(d, connect_timeout=10); cur=c.cursor(); " +
        "cur.execute('SELECT 1'); row=cur.fetchone(); c.close(); " +
        "raise SystemExit(0 if row and row[0] == 1 else 1)"
  uv run --extra runtime python -c $py *> $null
  return $LASTEXITCODE -eq 0
}

function Get-GraphConfig {
  if ($env:POSTGRES_DSN) {
    return [pscustomobject]@{
      mode = "postgres"
      envVars = @("POSTGRES_DSN=secretref:postgres-dsn")
      secrets = @("postgres-dsn=$($env:POSTGRES_DSN)")
    }
  }
  throw "POSTGRES_DSN is required after ADR-0014; Neo4j env-var rollback was removed in S118"
}

function Get-ServiceBusConfig {
  $conn = $env:AZURE_SERVICEBUS_CONNECTION_STRING
  if (-not $conn) { $conn = $env:SERVICEBUS_CONNECTION_STRING }
  if ($conn) {
    return [pscustomobject]@{
      envVars = @("AZURE_SERVICEBUS_CONNECTION_STRING=secretref:servicebus-connection-string")
      secrets = @("servicebus-connection-string=$conn")
    }
  }
  throw "AZURE_SERVICEBUS_CONNECTION_STRING or SERVICEBUS_CONNECTION_STRING is required for distributed serve transport"
}

function Upgrade-PostgresSchema {
  Top "POSTGRES SCHEMA"
  uv run --extra runtime --extra postgres alembic -c infra/migrations/alembic.ini upgrade head
  $ok = $LASTEXITCODE -eq 0
  Check $ok "alembic upgrade head"
  Bot
  if (-not $ok) { throw "alembic upgrade head failed" }
}

function Prepare-ServiceBusRoutes {
  Top "SERVICE BUS ROUTES"
  uv run --extra azure python scripts/servicebus_prepare_routes.py
  $ok = $LASTEXITCODE -eq 0
  Check $ok "served request topics + subscriptions"
  Bot
  if (-not $ok) { throw "Service Bus route preparation failed" }
}

function Get-CronScaleArgs($ruleName, $start) {
  return @(
    "--min-replicas", "0", "--max-replicas", "1",
    "--scale-rule-name", $ruleName,
    "--scale-rule-type", "cron",
    "--scale-rule-metadata",
    "timezone=$ScaleTimezone",
    "start=$start",
    "end=$ScaleEnd",
    "desiredReplicas=$ScaleDesiredReplicas"
  )
}

function Deploy-DispatcherJob($ghcr, $graph, $serviceBus) {
  Top "DEPLOY DISPATCHER JOB"
  $envv = @("POSTGRES_DSN=secretref:postgres-dsn") + @($serviceBus.envVars)
  $secrets = @($graph.secrets) + @($serviceBus.secrets)
  $image = "$REGISTRY/$OWNER/trading-agents-dispatcher:$Tag"
  $exists = az containerapp job show --name $DISPATCHER_JOB --resource-group $RG `
    --subscription $SUB --query name -o tsv 2>$null
  if ($exists) {
    $jobId = az containerapp job show --name $DISPATCHER_JOB --resource-group $RG `
      --subscription $SUB --query id -o tsv 2>$null
    az resource update --ids $jobId --set properties.configuration.triggerType=Schedule `
      properties.configuration.scheduleTriggerConfig.cronExpression="$DispatcherCron" `
      2>$null | Out-Null
    $state = az containerapp job update --name $DISPATCHER_JOB --resource-group $RG `
      --subscription $SUB --image $image --cron-expression $DispatcherCron `
      --replica-timeout 1800 --replica-retry-limit 0 --parallelism 1 `
      --replica-completion-count 1 --set-env-vars $envv `
      --query properties.provisioningState -o tsv 2>$null
    Check ($state -eq "Succeeded") "$DISPATCHER_JOB updated ($DispatcherCron UTC)"
  }
  else {
    $state = az containerapp job create --name $DISPATCHER_JOB --resource-group $RG `
      --environment $ENV_NAME --subscription $SUB --trigger-type Schedule `
      --cron-expression $DispatcherCron --image $image `
      --registry-server $REGISTRY --registry-username $ghcr.username `
      --registry-password $ghcr.pat --replica-timeout 1800 `
      --replica-retry-limit 0 --parallelism 1 --replica-completion-count 1 `
      --cpu 0.5 --memory 1.0Gi --secrets $secrets --env-vars $envv `
      --query properties.provisioningState -o tsv 2>$null
    Check ($state -eq "Succeeded") "$DISPATCHER_JOB created ($DispatcherCron UTC)"
  }
  Bot
}

# ── Preflight ─────────────────────────────────────────────────────────────────
function Preflight {
  Top "FLEET PREFLIGHT"
  Load-DotEnv
  $ok = $true

  $acct = az account show --query "{n:name}" -o json 2>$null | ConvertFrom-Json
  $loggedIn = [bool]$acct
  Check $loggedIn ("Azure CLI logged in" + ($(if ($loggedIn) { " ($($acct.n))" } else { " — run: az login" })))
  $ok = $ok -and $loggedIn

  $ext = az extension list --query "[?name=='containerapp'].name" -o tsv 2>$null
  Check ([bool]$ext) "containerapp CLI extension"
  $ok = $ok -and [bool]$ext

  if ($loggedIn) {
    $envExists = az containerapp env show --name $ENV_NAME --resource-group $RG --subscription $SUB --query name -o tsv 2>$null
    Check ([bool]$envExists) "Container Apps env: $ENV_NAME"
    $ok = $ok -and [bool]$envExists
  }

  $ghcr = Load-Json "ghcr.local.json"
  Check ([bool]$ghcr) "GHCR creds (infra/ghcr.local.json)"
  $ok = $ok -and $ghcr

  try { $graph = Get-GraphConfig } catch { $graph = $null }
  Check ([bool]$graph) "graph config (Postgres required)"
  $ok = $ok -and [bool]$graph
  if ($graph -and $graph.mode -eq "postgres") {
    $pgOk = Test-PostgresDsn
    Check $pgOk "Postgres connect + SELECT 1"
    $ok = $ok -and $pgOk
  }

  try { $serviceBus = Get-ServiceBusConfig } catch { $serviceBus = $null }
  Check ([bool]$serviceBus) "Service Bus connection config"
  $ok = $ok -and [bool]$serviceBus

  if ($ghcr) {
    $imgs = @()
    try {
      $resp = Invoke-RestMethod -Uri "https://api.github.com/user/packages?package_type=container&per_page=100" `
        -Headers @{ Authorization = "Bearer $($ghcr.pat)"; "User-Agent" = "trading-agents" }
      $imgs = @($resp | Where-Object { $_.name -like "trading-agents-*" })
    } catch {}
    $have = $imgs.Count
    Check ($have -ge 14) "GHCR images present: $have/14"
    $ok = $ok -and ($have -ge 14)
  }

  Bot
  return $ok
}

# ── Master keypair (stable, for ACTIVATE signature verification) ──────────────
function Get-MasterKeypair {
  $path = Join-Path $PSScriptRoot "master-keypair.local.json"
  if (Test-Path $path) { return Get-Content $path -Raw | ConvertFrom-Json }
  Line "generating stable master RSA keypair (first deploy)"
  $py = "from kernel.crypto import generate_keypair; import base64; " +
  "pr,pu=generate_keypair(); print(base64.b64encode(pr.encode()).decode()); " +
  "print(base64.b64encode(pu.encode()).decode())"
  $lines = (uv run python -c $py) -split "`n" | Where-Object { $_.Trim() }
  $kp = [pscustomobject]@{ priv_b64 = $lines[0].Trim(); pub_b64 = $lines[1].Trim() }
  $kp | ConvertTo-Json | Out-File $path -Encoding utf8
  return $kp
}

# ── Deploy ────────────────────────────────────────────────────────────────────
function Up {
  if (-not (Preflight)) { Write-Host "`nPreflight failed — fix the [XX] items above." -ForegroundColor Red; return }
  $ghcr = Load-Json "ghcr.local.json"; $graph = Get-GraphConfig; $serviceBus = Get-ServiceBusConfig

  Upgrade-PostgresSchema
  Prepare-ServiceBusRoutes
  $kp = Get-MasterKeypair

  Top "DEPLOY MASTER"
  $kv = Load-Json "key-vault.local.json"
  # Inject the trading pack policy + secret map as base64 env content (not baked
  # into the substrate image — keeps the master image pack-agnostic; S86 / DL-12).
  $packs = Join-Path $PSScriptRoot "..\orchestration\packs"
  $grantB64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $packs "trading_grants.json")))
  $secretB64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $packs "trading_secrets.json")))
  $envv = @(
    "MASTER_GRAPH=auto",
    "MASTER_PRIVATE_KEY_PEM_B64=secretref:master-key-b64",
    "MASTER_GRANT_POLICY_B64=$grantB64", "MASTER_SECRET_MAP_B64=$secretB64"
  ) + @($graph.envVars) + @($serviceBus.envVars)
  $masterSecrets = @($graph.secrets) + @($serviceBus.secrets) + @("master-key-b64=$($kp.priv_b64)")
  $mArgs = @(
    "containerapp", "create", "--name", "master", "--resource-group", $RG,
    "--environment", $ENV_NAME, "--subscription", $SUB,
    "--image", "$REGISTRY/$OWNER/trading-agents-master:$Tag",
    "--registry-server", $REGISTRY, "--registry-username", $ghcr.username,
    "--registry-password", $ghcr.pat, "--target-port", "8000", "--ingress", "internal",
    "--secrets"
  ) + $masterSecrets + @(
    "--query", "properties.provisioningState", "-o", "tsv"
  )
  if ($kv) {
    $envv += @("MASTER_KEY_VAULT_URL=$($kv.vault_url)", "AZURE_CLIENT_ID=$($kv.client_id)")
    $mArgs += @("--user-assigned", $kv.resource_id)
    Line "Key Vault wired: $($kv.vault_url)"
  }
  else { Line "no Key Vault — master uses env-var secrets" }
  $mArgs += @("--env-vars") + $envv + (Get-CronScaleArgs "daily-master-window" $MasterScaleStart)
  az @mArgs 2>$null | Out-Null
  $fqdn = az containerapp show --name master --resource-group $RG --subscription $SUB --query "properties.configuration.ingress.fqdn" -o tsv 2>$null
  Check ([bool]$fqdn) "master @ https://$fqdn"
  Bot
  $masterUrl = "https://$fqdn"

  Top "DEPLOY AGENTS ($($AGENTS.Count))"
  foreach ($name in $AGENTS.Keys) {
    $img = "$REGISTRY/$OWNER/trading-agents-$($AGENTS[$name]):$Tag"
    $agentEnv = @("MASTER_URL=$masterUrl", "MASTER_PUBLIC_KEY_PEM_B64=$($kp.pub_b64)") + @($graph.envVars) + @($serviceBus.envVars)
    $agentArgs = @(
      "containerapp", "create", "--name", $name, "--resource-group", $RG,
      "--environment", $ENV_NAME, "--subscription", $SUB,
      "--image", $img, "--registry-server", $REGISTRY, "--registry-username",
      $ghcr.username, "--registry-password", $ghcr.pat,
      "--secrets"
    ) + @($graph.secrets) + @($serviceBus.secrets) + @(
      "--env-vars"
    ) + $agentEnv + @(
      "--query", "properties.provisioningState", "-o", "tsv"
    ) + (Get-CronScaleArgs "daily-agent-window" $AgentScaleStart)
    $state = az @agentArgs 2>$null
    Check ($state -eq "Succeeded") $name
  }
  Bot
  Deploy-DispatcherJob $ghcr $graph $serviceBus
  Write-Host "`nFleet deployed with cron scale windows and dispatcher job. Watch:  pwsh infra/status.ps1 -Watch" -ForegroundColor Green
}

function Down {
  Top "TEARDOWN"
  az containerapp job delete --name $DISPATCHER_JOB --resource-group $RG `
    --subscription $SUB --yes 2>$null | Out-Null
  Check $true "deleted $DISPATCHER_JOB job"
  $all = @("master") + @($AGENTS.Keys)
  foreach ($name in $all) {
    az containerapp delete --name $name --resource-group $RG --subscription $SUB --yes 2>$null | Out-Null
    Check $true "deleted $name"
  }
  Bot
  Write-Host "`nFleet down. Scheduler removed and spend stopped." -ForegroundColor Green
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
az account set --subscription $SUB 2>$null
switch ($Action) {
  'preflight' { Preflight | Out-Null }
  'up' { Up }
  'down' { Down }
}
