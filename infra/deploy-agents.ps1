# deploy-agents.ps1 — One-command fleet deploy/teardown for Azure Container Apps.
#
#   pwsh infra/deploy-agents.ps1 preflight   # just the readiness checks
#   pwsh infra/deploy-agents.ps1 up          # preflight → Aura → master → 12 agents
#   pwsh infra/deploy-agents.ps1 down        # delete all apps + pause Aura
#
# Creds (all gitignored): infra/ghcr.local.json, infra/aura-api.local.json,
# infra/aura-instance.local.json. Reads the Container Apps env id from .env.

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
  $auraApi = Load-Json "aura-api.local.json"
  $auraInst = Load-Json "aura-instance.local.json"
  Check ([bool]$ghcr) "GHCR creds (infra/ghcr.local.json)"
  Check ([bool]$auraApi) "Aura API creds (infra/aura-api.local.json)"
  Check ([bool]$auraInst) "Aura instance creds (infra/aura-instance.local.json)"
  $ok = $ok -and $ghcr -and $auraApi -and $auraInst

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

  if ($auraApi) {
    try { $st = Aura-Status $auraApi (Aura-Token $auraApi) } catch { $st = "unreachable" }
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
  $ghcr = Load-Json "ghcr.local.json"; $auraApi = Load-Json "aura-api.local.json"; $auraInst = Load-Json "aura-instance.local.json"

  Top "AURA"; Resume-Aura $auraApi; Bot
  $kp = Get-MasterKeypair

  Top "DEPLOY MASTER"
  $kv = Load-Json "key-vault.local.json"
  $envv = @(
    "NEO4J_URI=$($auraApi.connection_url)", "NEO4J_USER=neo4j",
    "NEO4J_PASSWORD=secretref:neo4j-password", "NEO4J_DATABASE=neo4j",
    "MASTER_PRIVATE_KEY_PEM_B64=secretref:master-key-b64"
  )
  $mArgs = @(
    "containerapp", "create", "--name", "master", "--resource-group", $RG,
    "--environment", $ENV_NAME, "--subscription", $SUB,
    "--image", "$REGISTRY/$OWNER/trading-agents-master:latest",
    "--registry-server", $REGISTRY, "--registry-username", $ghcr.username,
    "--registry-password", $ghcr.pat, "--target-port", "8000", "--ingress", "internal",
    "--min-replicas", "1", "--max-replicas", "1",
    "--secrets", "neo4j-password=$($auraInst.password)", "master-key-b64=$($kp.priv_b64)",
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
    # NEO4J_* injected as plain env vars (DL-08a): each agent reads these to build
    # its GraphStore via build_graph_from_env(); only the provider uses them for S78.
    $state = az containerapp create --name $name --resource-group $RG --environment $ENV_NAME --subscription $SUB `
      --image $img --registry-server $REGISTRY --registry-username $ghcr.username --registry-password $ghcr.pat `
      --min-replicas 1 --max-replicas 1 `
      --env-vars "MASTER_URL=$masterUrl" "MASTER_PUBLIC_KEY_PEM_B64=$($kp.pub_b64)" `
                 "NEO4J_URI=$($auraApi.connection_url)" "NEO4J_USER=neo4j" "NEO4J_PASSWORD=$($auraInst.password)" `
      --query "properties.provisioningState" -o tsv 2>$null
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
