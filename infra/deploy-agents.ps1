# deploy-agents.ps1 — One-command fleet deploy/teardown for Azure Container Apps.
#
#   pwsh infra/deploy-agents.ps1 preflight   # just the readiness checks
#   pwsh infra/deploy-agents.ps1 up          # preflight → schema → master → 12 agents
#   pwsh infra/deploy-agents.ps1 down        # delete all apps + pause Aura
#
# Creds (all gitignored): infra/ghcr.local.json and infra/key-vault.local.json.
# POSTGRES_DSN is loaded from .env/process env; Neo4j rollback still works via
# infra/aura-api.local.json + infra/aura-instance.local.json when POSTGRES_DSN is unset.

param(
  [ValidateSet('preflight', 'up', 'down')]
  [string]$Action = 'preflight'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Config ────────────────────────────────────────────────────────────────────
$SUB = "5ef50a27-50a4-4d90-9695-da61b2309cf3"
$RG = "trading-agents"
$ENV_NAME = "trading-agents-env"
$REGISTRY = "ghcr.io"
$OWNER = "yury-gurevich"
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
      auraApi = $null
    }
  }
  $auraApi = Load-Json "aura-api.local.json"
  $auraInst = Load-Json "aura-instance.local.json"
  if ($auraApi -and $auraInst) {
    return [pscustomobject]@{
      mode = "neo4j"
      envVars = @(
        "NEO4J_URI=$($auraApi.connection_url)", "NEO4J_USER=$($auraInst.username)",
        "NEO4J_PASSWORD=secretref:neo4j-password", "NEO4J_DATABASE=$($auraInst.database)"
      )
      secrets = @("neo4j-password=$($auraInst.password)")
      auraApi = $auraApi
    }
  }
  throw "POSTGRES_DSN is required unless Neo4j rollback config is supplied"
}

function Upgrade-PostgresSchema {
  Top "POSTGRES SCHEMA"
  uv run --extra runtime --extra postgres alembic -c infra/migrations/alembic.ini upgrade head
  $ok = $LASTEXITCODE -eq 0
  Check $ok "alembic upgrade head"
  Bot
  if (-not $ok) { throw "alembic upgrade head failed" }
}

# ── Aura via API ──────────────────────────────────────────────────────────────
function Aura-Token($api) {
  $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$($api.api_client_id):$($api.api_client_secret)"))
  (Invoke-RestMethod -Method Post -Uri "https://api.neo4j.io/oauth/token" -Headers @{ Authorization = "Basic $b64" } `
      -Body @{ grant_type = "client_credentials" } -ContentType "application/x-www-form-urlencoded").access_token
}
function Aura-Status($api, $tok) {
  (Invoke-RestMethod -Uri "https://api.neo4j.io/v1/instances/$($api.instance_id)" -Headers @{ Authorization = "Bearer $tok" }).data.status
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
  Check ([bool]$graph) "graph config (Postgres default; Neo4j rollback supported)"
  $ok = $ok -and [bool]$graph
  if ($graph -and $graph.mode -eq "postgres") {
    $pgOk = Test-PostgresDsn
    Check $pgOk "Postgres connect + SELECT 1"
    $ok = $ok -and $pgOk
  }

  if ($ghcr) {
    $imgs = @()
    try {
      $resp = Invoke-RestMethod -Uri "https://api.github.com/user/packages?package_type=container&per_page=100" `
        -Headers @{ Authorization = "Bearer $($ghcr.pat)"; "User-Agent" = "trading-agents" }
      $imgs = @($resp | Where-Object { $_.name -like "trading-agents-*" })
    } catch {}
    $have = $imgs.Count
    Check ($have -ge 13) "GHCR images present: $have/13"
    $ok = $ok -and ($have -ge 13)
  }

  if ($graph -and $graph.mode -eq "neo4j") {
    try { $st = Aura-Status $graph.auraApi (Aura-Token $graph.auraApi) } catch { $st = "unreachable" }
    Check ($st -in @("running", "paused")) "Aura instance reachable (status: $st)"
  }

  Bot
  return $ok
}

# ── Aura resume + wait ────────────────────────────────────────────────────────
function Resume-Aura($api) {
  $tok = Aura-Token $api
  if ((Aura-Status $api $tok) -eq "running") { Line "Aura already running"; return }
  Invoke-RestMethod -Method Post -Uri "https://api.neo4j.io/v1/instances/$($api.instance_id)/resume" `
    -Headers @{ Authorization = "Bearer $tok" } -Body "{}" -ContentType "application/json" | Out-Null
  for ($i = 0; $i -lt 18; $i++) {
    $s = Aura-Status $api $tok
    Line ("Aura: {0}" -f $s)
    if ($s -eq "running") { return }
    Start-Sleep -Seconds 20
  }
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
  $ghcr = Load-Json "ghcr.local.json"; $graph = Get-GraphConfig

  if ($graph.mode -eq "postgres") { Upgrade-PostgresSchema }
  else { Top "AURA ROLLBACK"; Resume-Aura $graph.auraApi; Bot }
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
  ) + @($graph.envVars)
  $masterSecrets = @($graph.secrets) + @("master-key-b64=$($kp.priv_b64)")
  $mArgs = @(
    "containerapp", "create", "--name", "master", "--resource-group", $RG,
    "--environment", $ENV_NAME, "--subscription", $SUB,
    "--image", "$REGISTRY/$OWNER/trading-agents-master:latest",
    "--registry-server", $REGISTRY, "--registry-username", $ghcr.username,
    "--registry-password", $ghcr.pat, "--target-port", "8000", "--ingress", "internal",
    "--min-replicas", "1", "--max-replicas", "1",
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
  $mArgs += @("--env-vars") + $envv
  az @mArgs 2>$null | Out-Null
  $fqdn = az containerapp show --name master --resource-group $RG --subscription $SUB --query "properties.configuration.ingress.fqdn" -o tsv 2>$null
  Check ([bool]$fqdn) "master @ https://$fqdn"
  Bot
  $masterUrl = "https://$fqdn"

  Top "DEPLOY AGENTS ($($AGENTS.Count))"
  foreach ($name in $AGENTS.Keys) {
    $img = "$REGISTRY/$OWNER/trading-agents-$($AGENTS[$name]):latest"
    $agentEnv = @("MASTER_URL=$masterUrl", "MASTER_PUBLIC_KEY_PEM_B64=$($kp.pub_b64)") + @($graph.envVars)
    $agentArgs = @(
      "containerapp", "create", "--name", $name, "--resource-group", $RG,
      "--environment", $ENV_NAME, "--subscription", $SUB,
      "--image", $img, "--registry-server", $REGISTRY, "--registry-username",
      $ghcr.username, "--registry-password", $ghcr.pat,
      "--min-replicas", "1", "--max-replicas", "1",
      "--secrets"
    ) + @($graph.secrets) + @(
      "--env-vars"
    ) + $agentEnv + @(
      "--query", "properties.provisioningState", "-o", "tsv"
    )
    $state = az @agentArgs 2>$null
    Check ($state -eq "Succeeded") $name
  }
  Bot
  Write-Host "`nFleet up (signature verification ON). Watch:  pwsh infra/status.ps1 -Watch" -ForegroundColor Green
}

function Down {
  Top "TEARDOWN"
  $all = @("master") + @($AGENTS.Keys)
  foreach ($name in $all) {
    az containerapp delete --name $name --resource-group $RG --subscription $SUB --yes 2>$null | Out-Null
    Check $true "deleted $name"
  }
  $auraApi = Load-Json "aura-api.local.json"
  if ($auraApi) {
    $tok = Aura-Token $auraApi
    Invoke-RestMethod -Method Post -Uri "https://api.neo4j.io/v1/instances/$($auraApi.instance_id)/pause" `
      -Headers @{ Authorization = "Bearer $tok" } -Body "{}" -ContentType "application/json" 2>$null | Out-Null
    Line "Aura paused"
  }
  Bot
  Write-Host "`nFleet down. Spend stopped." -ForegroundColor Green
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
az account set --subscription $SUB 2>$null
switch ($Action) {
  'preflight' { Preflight | Out-Null }
  'up' { Up }
  'down' { Down }
}
