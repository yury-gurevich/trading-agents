# deploy-agents.ps1 — One-command fleet deploy/teardown for Azure Container Apps.
#
#   pwsh infra/deploy-agents.ps1 preflight   # just the readiness checks
#   pwsh infra/deploy-agents.ps1 up -Tag s103 # preflight → schema → master → 15 agents + cron job
#   pwsh infra/deploy-agents.ps1 down         # delete apps + dispatcher job
#
# Operator tunables and the dispatcher cron come from the pack
# (orchestration/packs/trading_tunables.json), never from live cluster state: a
# full `up` REPLACES each app's env set, so anything set by hand was silently
# reverted to its code default (DL-100). `up` refuses if it would drop a live env
# key the pack does not carry; -DropEnv KEY1,KEY2 acknowledges an intended removal.
#
# Creds (all gitignored): infra/ghcr.local.json and infra/key-vault.local.json.
# POSTGRES_DSN is the schema/admin DSN; fleet roles use per-target DSNs.

param(
  [ValidateSet('preflight', 'up', 'postgres-flip', 'servicebus-flip', 'down')]
  [string]$Action = 'preflight',
  [string]$Tag = 'latest',
  [string]$MasterScaleStart = '25 22 * * *',
  [string]$AgentScaleStart = '30 22 * * *',
  [string]$ScaleEnd = '30 00 * * *',
  [string]$ScaleTimezone = 'UTC',
  [int]$ScaleDesiredReplicas = 1,
  [string]$DispatcherCron = '',
  [string[]]$DropEnv = @(),
  [switch]$UseSharedPostgresDsn,
  [switch]$UseSharedServiceBusDsn
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
$POSTGRES_APP_SECRET = "postgres-dsn" # pragma: allowlist secret
$SERVICEBUS_APP_SECRET = "servicebus-connection-string" # pragma: allowlist secret
$SERVICEBUS_BUNDLE_SECRET = "servicebus-connection-strings" # pragma: allowlist secret
# Container App name → GHCR image suffix (app names can't contain underscores).
$AGENTS = [ordered]@{
  scanner = "scanner"; analyst = "analyst"; "portfolio-manager" = "portfolio_manager"
  "deliberator-manager" = "deliberator"; "deliberator-proponent" = "deliberator"
  "deliberator-opponent" = "deliberator"
  execution = "execution"; monitor = "monitor"; reporter = "reporter"
  forecaster = "forecaster"; operator = "operator"; supervisor = "supervisor"
  curator = "curator"; researcher = "researcher"; provider = "provider"
}

# ── UI helpers ────────────────────────────────────────────────────────────────
function Line($t) { Write-Host "│ $t" }
function Head($t) { Write-Host "│" ; Write-Host "│ $t" -ForegroundColor Yellow }
function Top($t) { Write-Host ("┌─ $t " + ("─" * [Math]::Max(0, 54 - $t.Length))) -ForegroundColor Cyan }
function Bot { Write-Host "└────────────────────────────────────────────────────────────" -ForegroundColor Cyan }
# Every [XX] is recorded, not just printed. A deploy that cannot report its own
# failure is the defect that let the 2026-08-02 :s155 attempt print "Fleet
# deployed" and exit 0 after all 15 agents failed (DL-85).
$script:Failures = @()

function Check($ok, $label) {
  if ($ok) { Write-Host "│   " -NoNewline; Write-Host "[OK] " -ForegroundColor Green -NoNewline; Write-Host $label }
  else {
    $script:Failures += $label
    Write-Host "│   " -NoNewline; Write-Host "[XX] " -ForegroundColor Red -NoNewline; Write-Host $label
  }
}

function Reset-Failures { $script:Failures = @() }

# `az` on Windows is az.cmd, a cmd.exe batch wrapper, so every invocation
# inherits cmd's ~8,191-character command-line ceiling. GRAPH_VOCABULARY_B64
# alone is >12,000 characters, so it cannot be passed at all through that
# wrapper — not even in a call carrying nothing else (measured: 12,053 chars →
# "The command line is too long.", exit 1). Invoking the CLI's own Python
# entry point goes through CreateProcess instead, whose limit is 32,767.
# Resolved once; falls back to `az` where the interpreter is not found (Linux,
# CI, a differently-packaged install), which is safe because those paths do not
# have cmd's ceiling. See DL-85.
$script:AzPython = $null
function Get-AzPython {
  if ($null -ne $script:AzPython) { return $script:AzPython }
  $script:AzPython = ""
  $cmd = Get-Command az -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -and $cmd.Source.EndsWith(".cmd")) {
    # …\CLI2\wbin\az.cmd → …\CLI2\python.exe
    $candidate = Join-Path (Split-Path (Split-Path $cmd.Source -Parent) -Parent) "python.exe"
    if (Test-Path $candidate) { $script:AzPython = $candidate }
  }
  return $script:AzPython
}

# Run an az command and return its STDOUT. stderr goes to a file and never into
# the returned value.
#
# The old shape merged with `2>&1` and took "the last non-empty line that does
# not start with WARNING:". Its own comment admitted it could not trust order —
# and that is exactly the defect (row Q). The containerapp extension writes more
# than the WARNING banner to stderr, and **any** such line arriving *after* the
# tsv value becomes "the state". Reproduced 2026-08-05 with a stub emitting
# `Succeeded` on stdout and a deprecation notice on stderr afterwards: the old
# heuristic returns the notice text, so `$state -eq "Succeeded"` is false and
# every target prints [XX] while the deploy actually succeeded — the :s155 run,
# and again on 2026-08-05 with "Deploy FAILED for 17 target(s)", exit 1, all of
# it wrong. Separating the streams returns `Succeeded` and needs no filtering.
#
# stderr is still surfaced on failure: the old `2>$null` hid "The command line is
# too long." fifteen times over (DL-85), and that must not come back.
function Invoke-Az([string[]]$azArgs) {
  $py = Get-AzPython
  $errFile = [System.IO.Path]::GetTempFileName()
  try {
    if ($py) { $out = & $py -m azure.cli @azArgs 2>$errFile }
    else { $out = az @azArgs 2>$errFile }
    if ($LASTEXITCODE -ne 0) {
      foreach ($line in @(Get-Content -LiteralPath $errFile -ErrorAction SilentlyContinue)) {
        Write-Host "      $line" -ForegroundColor DarkYellow
      }
      foreach ($line in @($out)) { Write-Host "      $line" -ForegroundColor DarkYellow }
      return $null
    }
    return (@($out) | ForEach-Object { "$_".Trim() } | Where-Object { $_ } | Select-Object -Last 1)
  }
  finally { Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue }
}

# Read provisioning state from the resource itself, not from the output of the
# call that changed it. Row Q's recommended fix: a mutating call's stream carries
# banners and notices, while `show` answers one question with one value. A deploy
# is the one operation with no cheap undo, so its report is worth a second call.
function Get-AppState([string]$name) {
  return Invoke-Az @(
    "containerapp", "show", "--name", $name, "--resource-group", $RG,
    "--subscription", $SUB, "--query", "properties.provisioningState", "-o", "tsv"
  )
}

function Get-JobState([string]$name) {
  return Invoke-Az @(
    "containerapp", "job", "show", "--name", $name, "--resource-group", $RG,
    "--subscription", $SUB, "--query", "properties.provisioningState", "-o", "tsv"
  )
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

function Get-PostgresDsnEnvName($target) {
  return "POSTGRES_DSN_" + $target.ToUpperInvariant().Replace("-", "_")
}

function Get-PostgresDsnSecretName($target) {
  return "postgres-dsn-" + $target.ToLowerInvariant().Replace("_", "-")
}

function Get-KeyVaultName {
  if ($env:POSTGRES_ROLE_KEY_VAULT) { return $env:POSTGRES_ROLE_KEY_VAULT }
  $kv = Load-Json "key-vault.local.json"
  if (-not $kv -or -not $kv.vault_url) { return "" }
  try { return ([uri]$kv.vault_url).Host.Split(".")[0] } catch { return "" }
}

function Get-TargetPostgresDsn($target) {
  if ($UseSharedPostgresDsn) { return $env:POSTGRES_DSN }
  $envName = Get-PostgresDsnEnvName $target
  $value = [Environment]::GetEnvironmentVariable($envName, "Process")
  if ($value) { return $value }
  $vault = Get-KeyVaultName
  if (-not $vault) { return "" }
  $secretName = Get-PostgresDsnSecretName $target
  $value = az keyvault secret show --vault-name $vault --name $secretName `
    --query value -o tsv 2>$null
  if ($LASTEXITCODE -ne 0) { return "" }
  return $value.Trim()
}

function Get-GraphConfig($target = "") {
  if ($target) {
    $secretValue = Get-TargetPostgresDsn $target
    if (-not $secretValue) {
      $envName = Get-PostgresDsnEnvName $target
      $secretName = Get-PostgresDsnSecretName $target
      throw "per-role Postgres DSN missing for $target ($envName or Key Vault $secretName)"
    }
    return [pscustomobject]@{
      mode = "postgres"
      envVars = @("POSTGRES_DSN=secretref:$POSTGRES_APP_SECRET")
      secrets = @("$POSTGRES_APP_SECRET=$secretValue")
    }
  }
  if ($env:POSTGRES_DSN) {
    return [pscustomobject]@{
      mode = "postgres"
      envVars = @("POSTGRES_DSN=secretref:$POSTGRES_APP_SECRET")
      secrets = @("$POSTGRES_APP_SECRET=$($env:POSTGRES_DSN)")
    }
  }
  throw "POSTGRES_DSN is required after ADR-0014; Neo4j env-var rollback was removed in S118"
}

function Get-SharedServiceBusConnectionString {
  $conn = $env:AZURE_SERVICEBUS_CONNECTION_STRING
  if (-not $conn) { $conn = $env:SERVICEBUS_CONNECTION_STRING }
  return $conn
}

function Get-ServiceBusConnectionEnvName($target) {
  return "AZURE_SERVICEBUS_CONNECTION_STRING_" + $target.ToUpperInvariant().Replace("-", "_")
}

function Get-ServiceBusSecretName($target) {
  return "servicebus-connection-string-" + $target.ToLowerInvariant().Replace("_", "-")
}

function Get-ServiceBusBundleSecretName($target) {
  return "servicebus-connection-strings-" + $target.ToLowerInvariant().Replace("_", "-")
}

function Get-ServiceBusKeyVaultName {
  if ($env:SERVICEBUS_SAS_KEY_VAULT) { return $env:SERVICEBUS_SAS_KEY_VAULT }
  return Get-KeyVaultName
}

function Get-KeyVaultSecretValue($vault, $secretName) {
  if (-not $vault) { return "" }
  $value = az keyvault secret show --vault-name $vault --name $secretName `
    --query value -o tsv 2>$null
  if ($LASTEXITCODE -ne 0) { return "" }
  return $value.Trim()
}

function Get-TargetServiceBusConnectionString($target) {
  if ($UseSharedServiceBusDsn) { return Get-SharedServiceBusConnectionString }
  $envName = Get-ServiceBusConnectionEnvName $target
  $value = [Environment]::GetEnvironmentVariable($envName, "Process")
  if ($value) { return $value }
  return Get-KeyVaultSecretValue (Get-ServiceBusKeyVaultName) (Get-ServiceBusSecretName $target)
}

function Get-TargetServiceBusBundle($target) {
  if ($UseSharedServiceBusDsn) { return "" }
  return Get-KeyVaultSecretValue (Get-ServiceBusKeyVaultName) (Get-ServiceBusBundleSecretName $target)
}

function Get-ServiceBusConfig($target = "") {
  if ($target) {
    $conn = Get-TargetServiceBusConnectionString $target
    if (-not $conn) {
      $envName = Get-ServiceBusConnectionEnvName $target
      $secretName = Get-ServiceBusSecretName $target
      throw "per-target Service Bus SAS missing for $target ($envName or Key Vault $secretName)"
    }
    $envVars = @("AZURE_SERVICEBUS_CONNECTION_STRING=secretref:$SERVICEBUS_APP_SECRET")
    $secrets = @("$SERVICEBUS_APP_SECRET=$conn")
    $bundle = Get-TargetServiceBusBundle $target
    if ($bundle) {
      $envVars += @("AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON=secretref:$SERVICEBUS_BUNDLE_SECRET")
      $secrets += @("$SERVICEBUS_BUNDLE_SECRET=$bundle")
    }
    return [pscustomobject]@{ envVars = $envVars; secrets = $secrets }
  }
  $conn = Get-SharedServiceBusConnectionString
  if ($conn) {
    return [pscustomobject]@{
      envVars = @("AZURE_SERVICEBUS_CONNECTION_STRING=secretref:$SERVICEBUS_APP_SECRET")
      secrets = @("$SERVICEBUS_APP_SECRET=$conn")
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

# ── Operator tunables: the pack is the source of truth, not the cluster ───────
# A `containerapp create` against an existing app REPLACES its env set. Measured
# 2026-08-08: one `up` wiped SCANNER_CANDIDATE_CAP=25, MAX_POSITION_PCT=0.01
# (a silent 10x position size), MAX_POSITIONS=60 and reverted the weekday-only
# dispatcher cron — every one of them under a green [OK]. The values now live in
# the pack, and the guard below refuses to deploy over anything the pack forgot.
function Load-Tunables {
  $p = Join-Path $PSScriptRoot '..\orchestration\packs\trading_tunables.json'
  # Absence is a broken checkout, not an empty config: proceeding would deploy
  # code defaults over the operator's fleet, which is the defect itself.
  if (-not (Test-Path $p)) { throw "tunables pack missing: $p" }
  return Get-Content $p -Raw | ConvertFrom-Json
}

function Get-AppTunables($name) {
  $apps = (Load-Tunables).apps
  if (@($apps.PSObject.Properties.Name) -notcontains $name) { return @() }
  return @($apps.$name.PSObject.Properties | ForEach-Object { "$($_.Name)=$($_.Value)" })
}

function Resolve-DispatcherCron {
  # An explicit -DispatcherCron still wins; the script literal no longer exists,
  # because a literal default is what reverted `30 22 * * 1-5` to daily.
  if ($DispatcherCron) { return $DispatcherCron }
  return (Load-Tunables).dispatcher.cron
}

function Get-AgentEnv($name, $masterUrl, $pubB64) {
  $agentGraph = Get-GraphConfig $name
  $agentServiceBus = Get-ServiceBusConfig $name
  $envv = @("MASTER_URL=$masterUrl", "MASTER_PUBLIC_KEY_PEM_B64=$pubB64") +
  @($agentGraph.envVars) + @($agentServiceBus.envVars)
  if ($name.StartsWith("deliberator-")) {
    $envv += @(
      "DELIBERATOR_ROLE=$($name.Substring('deliberator-'.Length))",
      "DELIBERATOR_INSTANCE_NAME=$name"
    )
  }
  return $envv + (Get-AppTunables $name)
}

function Get-LiveEnvNames($name) {
  $raw = az containerapp show --name $name --resource-group $RG --subscription $SUB `
    --query "properties.template.containers[0].env[].name" -o tsv 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $raw) { return @() }
  return @($raw -split "`r?`n" | Where-Object { $_ })
}

function Get-LiveJobEnvNames($name) {
  $raw = az containerapp job show --name $name --resource-group $RG --subscription $SUB `
    --query "properties.template.containers[0].env[].name" -o tsv 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $raw) { return @() }
  return @($raw -split "`r?`n" | Where-Object { $_ })
}

function Assert-EnvPreserved($name, [string[]]$liveNames, [string[]]$plannedNames) {
  # GRAPH_VOCABULARY_B64 is set by its own narrow call after create (DL-85), so
  # it is planned even though it never appears in the create line.
  $planned = @($plannedNames) + @("GRAPH_VOCABULARY_B64")
  $dropped = @($liveNames | Where-Object { $planned -notcontains $_ -and $DropEnv -notcontains $_ })
  $label = "$name env preserved"
  if ($dropped.Count -gt 0) {
    $label = "$name would DROP: $($dropped -join ', ') — add to the tunables pack, or pass -DropEnv"
  }
  Check ($dropped.Count -eq 0) $label
  return $dropped.Count -eq 0
}

function Assert-FleetEnvPreserved {
  # Runs BEFORE the first create, so a refusal leaves the fleet untouched rather
  # than half-deployed. Master is not checked: its env is wholly deploy-built
  # (grants, secret map, Key Vault) and carries no operator tunable.
  Top "ENV PRESERVATION"
  $ok = $true
  foreach ($name in $AGENTS.Keys) {
    $planned = @(Get-AgentEnv $name "url" "pub" | ForEach-Object { ($_ -split "=", 2)[0] })
    $ok = (Assert-EnvPreserved $name (Get-LiveEnvNames $name) $planned) -and $ok
  }
  $dispatcherPlanned = @("POSTGRES_DSN") +
  @((Get-ServiceBusConfig "dispatcher").envVars | ForEach-Object { ($_ -split "=", 2)[0] })
  $ok = (Assert-EnvPreserved $DISPATCHER_JOB (Get-LiveJobEnvNames $DISPATCHER_JOB) $dispatcherPlanned) -and $ok
  Bot
  return $ok
}

function Get-FleetPostgresTargets {
  return @("master") + @($AGENTS.Keys) + @("dispatcher")
}

function Get-FleetServiceBusTargets {
  return @($AGENTS.Keys) + @("dispatcher")
}

function Deploy-DispatcherJob($ghcr, $graph, $serviceBus) {
  Top "DEPLOY DISPATCHER JOB"
  $cron = Resolve-DispatcherCron
  # Vocabulary is set separately below, never on this line (DL-85).
  $envv = @("POSTGRES_DSN=secretref:postgres-dsn") + @($serviceBus.envVars)
  $secrets = @($graph.secrets) + @($serviceBus.secrets)
  $image = "$REGISTRY/$OWNER/trading-agents-dispatcher:$Tag"
  $exists = az containerapp job show --name $DISPATCHER_JOB --resource-group $RG `
    --subscription $SUB --query name -o tsv 2>$null
  if ($exists) {
    $jobId = az containerapp job show --name $DISPATCHER_JOB --resource-group $RG `
      --subscription $SUB --query id -o tsv 2>$null
    az resource update --ids $jobId --set properties.configuration.triggerType=Schedule `
      properties.configuration.scheduleTriggerConfig.cronExpression="$cron" `
      2>$null | Out-Null
    az containerapp job secret set --name $DISPATCHER_JOB --resource-group $RG `
      --subscription $SUB --secrets $secrets -o none 2>$null | Out-Null
    $secretOk = $LASTEXITCODE -eq 0
    $state = az containerapp job update --name $DISPATCHER_JOB --resource-group $RG `
      --subscription $SUB --image $image --cron-expression $cron `
      --replica-timeout 1800 --replica-retry-limit 0 --parallelism 1 `
      --replica-completion-count 1 --set-env-vars $envv `
      --query properties.provisioningState -o tsv 2>$null
    $vocabOk = ($state -eq "Succeeded") -and (Set-JobVocabulary)
    Check ($secretOk -and $state -eq "Succeeded" -and $vocabOk) "$DISPATCHER_JOB updated ($cron UTC)"
  }
  else {
    $state = az containerapp job create --name $DISPATCHER_JOB --resource-group $RG `
      --environment $ENV_NAME --subscription $SUB --trigger-type Schedule `
      --cron-expression $cron --image $image `
      --registry-server $REGISTRY --registry-username $ghcr.username `
      --registry-password $ghcr.pat --replica-timeout 1800 `
      --replica-retry-limit 0 --parallelism 1 --replica-completion-count 1 `
      --cpu 0.5 --memory 1.0Gi --secrets $secrets --env-vars $envv `
      --query properties.provisioningState -o tsv 2>$null
    $vocabOk = ($state -eq "Succeeded") -and (Set-JobVocabulary)
    Check ($state -eq "Succeeded" -and $vocabOk) "$DISPATCHER_JOB created ($cron UTC)"
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
  Check ([bool]$graph) "schema graph config (Postgres required)"
  $ok = $ok -and [bool]$graph
  if ($graph -and $graph.mode -eq "postgres") {
    $pgOk = Test-PostgresDsn
    Check $pgOk "Postgres connect + SELECT 1"
    $ok = $ok -and $pgOk
  }

  $pgTargets = Get-FleetPostgresTargets
  $pgReady = 0
  foreach ($target in $pgTargets) {
    try {
      Get-GraphConfig $target | Out-Null
      $pgReady += 1
    } catch {}
  }
  $allPgReady = $pgReady -eq $pgTargets.Count
  Check $allPgReady "per-target Postgres DSNs: $pgReady/$($pgTargets.Count)"
  $ok = $ok -and $allPgReady

  try { $serviceBus = Get-ServiceBusConfig } catch { $serviceBus = $null }
  Check ([bool]$serviceBus) "Service Bus admin connection config"
  $ok = $ok -and [bool]$serviceBus

  $sbTargets = Get-FleetServiceBusTargets
  $sbReady = 0
  foreach ($target in $sbTargets) {
    try {
      Get-ServiceBusConfig $target | Out-Null
      $sbReady += 1
    } catch {}
  }
  $allSbReady = $sbReady -eq $sbTargets.Count
  Check $allSbReady "per-target Service Bus SAS strings: $sbReady/$($sbTargets.Count)"
  $ok = $ok -and $allSbReady

  if ($ghcr) {
    $imgs = @()
    try {
      $resp = Invoke-RestMethod -Uri "https://api.github.com/user/packages?package_type=container&per_page=100" `
        -Headers @{ Authorization = "Bearer $($ghcr.pat)"; "User-Agent" = "trading-agents" }
      $imgs = @($resp | Where-Object { $_.name -like "trading-agents-*" })
    } catch {}
    $have = $imgs.Count
    Check ($have -ge 15) "GHCR images present: $have/15"
    $ok = $ok -and ($have -ge 15)
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
function Get-VocabularyEnv {
  # The graph write-guard vocabulary is pack data, injected as base64 the same way
  # the master's grants and secret map are (S86 / DL-12, S144 / DL-68). None of the
  # 15 images copies orchestration/packs, so GRAPH_VOCABULARY_PATH can only ever
  # resolve in local dev — base64 is the only deployable form.
  $file = Join-Path $PSScriptRoot "..\orchestration\packs\trading_graph_vocabulary.json"
  return "GRAPH_VOCABULARY_B64=" + [Convert]::ToBase64String([IO.File]::ReadAllBytes($file))
}

# The pack must NOT ride on a create/update that also carries secrets, the GHCR
# PAT and the master key: `az` is az.cmd, so every invocation inherits cmd's
# command-line ceiling, and the base64 pack alone is >12,000 characters. Set it
# in its own narrow call — the same two-step Set-AppPostgresDsn already uses.
# Shrinking the pack is not an option: its completeness is what makes the guard
# trustworthy (S143/S144). See DL-85.
function Set-AppVocabulary($name) {
  $state = Invoke-Az @(
    "containerapp", "update", "--name", $name, "--resource-group", $RG,
    "--subscription", $SUB, "--set-env-vars", (Get-VocabularyEnv),
    "--query", "properties.provisioningState", "-o", "tsv"
  )
  # $null means the call itself failed (non-zero exit, stderr already printed).
  # Otherwise ask the resource, not the call that changed it.
  if ($null -eq $state) { return $false }
  return (Get-AppState $name) -eq "Succeeded"
}

function Set-JobVocabulary {
  $state = Invoke-Az @(
    "containerapp", "job", "update", "--name", $DISPATCHER_JOB,
    "--resource-group", $RG, "--subscription", $SUB,
    "--set-env-vars", (Get-VocabularyEnv),
    "--query", "properties.provisioningState", "-o", "tsv"
  )
  if ($null -eq $state) { return $false }
  return (Get-JobState $DISPATCHER_JOB) -eq "Succeeded"
}

function Up {
  if (-not (Preflight)) { Write-Host "`nPreflight failed — fix the [XX] items above." -ForegroundColor Red; return }
  # Refuse before the first create, not after the ninth: a deploy that discards
  # operator config must fail whole rather than leave a half-configured fleet.
  if (-not (Assert-FleetEnvPreserved)) {
    Write-Host "`nDeploy refused — it would discard live configuration listed above." -ForegroundColor Red
    Write-Host "Carry each key in orchestration/packs/trading_tunables.json, or pass -DropEnv to drop it deliberately." -ForegroundColor Red
    return
  }
  $ghcr = Load-Json "ghcr.local.json"

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
  )
  $masterGraph = Get-GraphConfig "master"
  $envv += @($masterGraph.envVars)
  $masterSecrets = @($masterGraph.secrets) + @("master-key-b64=$($kp.priv_b64)")
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
  $masterState = Invoke-Az $mArgs
  $vocabOk = Set-AppVocabulary "master"
  $fqdn = az containerapp show --name master --resource-group $RG --subscription $SUB --query "properties.configuration.ingress.fqdn" -o tsv 2>$null
  # The old check tested only [bool]$fqdn, which an already-existing app satisfies
  # whether or not this deploy did anything (DL-85). The state now comes from the
  # resource rather than from the deploying call's stream (row Q).
  $masterOk = ($null -ne $masterState) -and ((Get-AppState "master") -eq "Succeeded")
  Check ($masterOk -and $vocabOk -and [bool]$fqdn) "master @ https://$fqdn"
  Bot
  $masterUrl = "https://$fqdn"

  Top "DEPLOY AGENTS ($($AGENTS.Count))"
  foreach ($name in $AGENTS.Keys) {
    $img = "$REGISTRY/$OWNER/trading-agents-$($AGENTS[$name]):$Tag"
    $agentGraph = Get-GraphConfig $name
    $agentServiceBus = Get-ServiceBusConfig $name
    $agentEnv = Get-AgentEnv $name $masterUrl $kp.pub_b64
    $agentArgs = @(
      "containerapp", "create", "--name", $name, "--resource-group", $RG,
      "--environment", $ENV_NAME, "--subscription", $SUB,
      "--image", $img, "--registry-server", $REGISTRY, "--registry-username",
      $ghcr.username, "--registry-password", $ghcr.pat,
      "--secrets"
    ) + @($agentGraph.secrets) + @($agentServiceBus.secrets) + @(
      "--env-vars"
    ) + $agentEnv + @(
      "--query", "properties.provisioningState", "-o", "tsv"
    ) + (Get-CronScaleArgs "daily-agent-window" $AgentScaleStart)
    $state = Invoke-Az $agentArgs
    # State comes from the resource, not from the deploying call's stream (row Q).
    $appOk = ($null -ne $state) -and ((Get-AppState $name) -eq "Succeeded")
    # Image and pack are one unit: a target on new code with a stale vocabulary
    # raises VocabularyError fail-closed on its first write (the S148 stall).
    $vocabOk = $appOk -and (Set-AppVocabulary $name)
    Check ($appOk -and $vocabOk) $name
  }
  Bot
  Deploy-DispatcherJob $ghcr (Get-GraphConfig "dispatcher") (Get-ServiceBusConfig "dispatcher")

  if ($script:Failures.Count -gt 0) {
    Write-Host "`nDeploy FAILED for $($script:Failures.Count) target(s):" -ForegroundColor Red
    foreach ($f in $script:Failures) { Write-Host "  - $f" -ForegroundColor Red }
    Write-Host "The fleet may be partially updated. Re-run after fixing, or roll back to the previous tag." -ForegroundColor Red
    exit 1
  }
  Write-Host "`nFleet deployed with cron scale windows and dispatcher job. Watch:  pwsh infra/status.ps1 -Watch" -ForegroundColor Green
}

function Set-AppPostgresDsn($name) {
  $graph = Get-GraphConfig $name
  az containerapp secret set --name $name --resource-group $RG --subscription $SUB `
    --secrets $graph.secrets -o none 2>$null | Out-Null
  $secretOk = $LASTEXITCODE -eq 0
  $state = az containerapp update --name $name --resource-group $RG `
    --subscription $SUB --set-env-vars $graph.envVars `
    --query properties.provisioningState -o tsv 2>$null
  Check ($secretOk -and $state -eq "Succeeded") "$name POSTGRES_DSN secretref"
  return $secretOk -and $state -eq "Succeeded"
}

function Set-DispatcherPostgresDsn {
  $graph = Get-GraphConfig "dispatcher"
  az containerapp job secret set --name $DISPATCHER_JOB --resource-group $RG `
    --subscription $SUB --secrets $graph.secrets -o none 2>$null | Out-Null
  $secretOk = $LASTEXITCODE -eq 0
  $state = az containerapp job update --name $DISPATCHER_JOB --resource-group $RG `
    --subscription $SUB --set-env-vars $graph.envVars `
    --query properties.provisioningState -o tsv 2>$null
  Check ($secretOk -and $state -eq "Succeeded") "$DISPATCHER_JOB POSTGRES_DSN secretref"
  return $secretOk -and $state -eq "Succeeded"
}

function Flip-PostgresRoles {
  Top "POSTGRES ROLE FLIP"
  Load-DotEnv
  $ok = $true
  $ok = (Set-AppPostgresDsn "master") -and $ok
  foreach ($name in $AGENTS.Keys) {
    $ok = (Set-AppPostgresDsn $name) -and $ok
  }
  $ok = (Set-DispatcherPostgresDsn) -and $ok
  Bot
  if (-not $ok) { throw "Postgres role flip failed" }
}

function Set-AppServiceBusConfig($name) {
  $serviceBus = Get-ServiceBusConfig $name
  az containerapp secret set --name $name --resource-group $RG --subscription $SUB `
    --secrets $serviceBus.secrets -o none 2>$null | Out-Null
  $secretOk = $LASTEXITCODE -eq 0
  $state = az containerapp update --name $name --resource-group $RG `
    --subscription $SUB --set-env-vars $serviceBus.envVars `
    --query properties.provisioningState -o tsv 2>$null
  Check ($secretOk -and $state -eq "Succeeded") "$name Service Bus secretref"
  return $secretOk -and $state -eq "Succeeded"
}

function Set-DispatcherServiceBusConfig {
  $serviceBus = Get-ServiceBusConfig "dispatcher"
  az containerapp job secret set --name $DISPATCHER_JOB --resource-group $RG `
    --subscription $SUB --secrets $serviceBus.secrets -o none 2>$null | Out-Null
  $secretOk = $LASTEXITCODE -eq 0
  $state = az containerapp job update --name $DISPATCHER_JOB --resource-group $RG `
    --subscription $SUB --set-env-vars $serviceBus.envVars `
    --query properties.provisioningState -o tsv 2>$null
  Check ($secretOk -and $state -eq "Succeeded") "$DISPATCHER_JOB Service Bus secretref"
  return $secretOk -and $state -eq "Succeeded"
}

function Set-MasterServiceBusConfig {
  if ($UseSharedServiceBusDsn) {
    $serviceBus = Get-ServiceBusConfig
    az containerapp secret set --name "master" --resource-group $RG --subscription $SUB `
      --secrets $serviceBus.secrets -o none 2>$null | Out-Null
    $secretOk = $LASTEXITCODE -eq 0
    $state = az containerapp update --name "master" --resource-group $RG `
      --subscription $SUB --set-env-vars $serviceBus.envVars `
      --query properties.provisioningState -o tsv 2>$null
    Check ($secretOk -and $state -eq "Succeeded") "master shared Service Bus rollback"
    return $secretOk -and $state -eq "Succeeded"
  }
  $state = az containerapp update --name "master" --resource-group $RG `
    --subscription $SUB --remove-env-vars AZURE_SERVICEBUS_CONNECTION_STRING `
    AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON `
    --query properties.provisioningState -o tsv 2>$null
  Check ($state -eq "Succeeded") "master Service Bus env removed"
  return $state -eq "Succeeded"
}

function Flip-ServiceBusSas {
  Top "SERVICE BUS SAS FLIP"
  Load-DotEnv
  $ok = $true
  $ok = (Set-MasterServiceBusConfig) -and $ok
  foreach ($name in $AGENTS.Keys) {
    $ok = (Set-AppServiceBusConfig $name) -and $ok
  }
  $ok = (Set-DispatcherServiceBusConfig) -and $ok
  Bot
  if (-not $ok) { throw "Service Bus SAS flip failed" }
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
  'postgres-flip' { Flip-PostgresRoles }
  'servicebus-flip' { Flip-ServiceBusSas }
  'down' { Down }
}
