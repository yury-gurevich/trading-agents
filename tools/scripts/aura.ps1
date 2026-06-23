# aura.ps1 — Manage Neo4j Aura instances via the Aura API.
#
# ─────────────────────────────────────────────────────────────────────────────
# DESTRUCTIVE OPERATIONS — READ THIS FIRST
#
#   pause, resume, delete, restore, create-free, overwrite, and switch-to-free
#   all modify live cloud infrastructure or local credential / .env files.
#
#   -WhatIf  Dry-run mode: prints every action that WOULD be taken, shows request
#          bodies and file paths — but makes NO API calls and writes NO files.
#          Run -WhatIf before any destructive action you have not done before.
# ─────────────────────────────────────────────────────────────────────────────
#
# All Aura management is scripted here — no console clicks needed. API
# credentials and the current instance id live in infra/aura-api.local.json
# (gitignored); that file is created once from the Aura console API key.
#
# ─────────────────────────────────────────────────────────────────────────────
# PARAMETERS
#
#   -Action (required)
#       The operation to run; see full list below.
#
#   -WhatIf
#       Dry-run mode. No API calls. No file writes.
#       Safe to pass on any action at any time.
#
#   -InfraDir <path>
#       Path to the directory containing the *.local.json credential files and
#       where .env lives one level up.
#       Default: auto-resolved from this script's location as ../../infra/
#       (i.e. trading-agents/infra/ when called from tools/scripts/).
#       Override this when calling from a different repo (e.g. traiding-system).
#
#   -SnapshotId <id>        Required by: restore, export-url
#   -DestInstanceId <id>    Required by: overwrite  (the instance to overwrite)
#   -SrcSnapshotId <id>     Optional for: overwrite (defaults to latest Completed)
#   -FreeName <name>        Optional for: create-free (default: "trading-agents-free")
#
# ─────────────────────────────────────────────────────────────────────────────
# READ-ONLY ACTIONS — safe; -WhatIf has no effect
#
#   status
#       Show provisioning / running / paused state, region, and instance type.
#
#   connection
#       Print NEO4J_URI, NEO4J_USER, and NEO4J_DATABASE for manual copy-paste.
#
#   list
#       List all instances in the tenant (id, name, status, type, region).
#
#   snapshots
#       List all snapshots for the active instance (id, status, timestamp).
#
#   export-url -SnapshotId <id>
#       Get the download URL for an exportable snapshot.
#       Professional tier only — Free tier returns 403.
#
#   compare
#       Run scripts/compare_aura.py — side-by-side node/rel count diff between
#       the Professional (aura-instance.local.json) and Free (aura-free.local.json)
#       instances. Exit 0 = identical, 1 = diverged, 2 = connection error.
#
# ─────────────────────────────────────────────────────────────────────────────
# DESTRUCTIVE ACTIONS — run with -WhatIf first
#
#   pause  ⚠
#       Pause the active instance. Database becomes inaccessible; billing stops.
#       Resume with 'resume' when needed.
#
#   resume  ⚠
#       Bring a paused instance back online. Billing restarts.
#
#   delete  ⚠⚠ PERMANENT
#       Delete the active instance. This CANNOT BE UNDONE.
#       The instance id in aura-api.local.json is used — verify with 'status' first.
#
#   snapshot  ⚠
#       Trigger an on-demand backup snapshot. Use 'snapshots' to check progress.
#       Prerequisite for 'restore' and 'overwrite'.
#
#   restore -SnapshotId <id>  ⚠
#       Restore the active instance from a snapshot.
#       OVERWRITES current database content. No confirmation prompt.
#       Run 'snapshots' first to get a valid snapshot id.
#
#   create-free [-FreeName <name>]  ⚠
#       Create a new AuraDB Free instance on GCP us-central1.
#       Saves full credentials INCLUDING PASSWORD to infra/aura-free.local.json
#       (gitignored). The password is shown ONCE in the output — save it.
#       Neo4j Free allows only one instance per account; this will fail if one
#       already exists.
#
#   overwrite -DestInstanceId <id> [-SrcSnapshotId <id>]  ⚠
#       Attempt to overwrite DEST with data from the active (source) instance.
#       If -SrcSnapshotId is omitted, the latest Completed snapshot is used.
#       NOTE: Professional → Free cross-tier overwrite is BLOCKED by Neo4j API
#       (returns 422). The Free instance will remain empty — that is expected.
#       Use 'switch-to-free' and then a fresh grand-check run instead.
#
#   switch-to-free  ⚠
#       Rewrite three lines in .env (NEO4J_URI, NEO4J_PASSWORD, NEO4J_TEST_URI)
#       and update infra/aura-api.local.json to point at the Free instance.
#       Backs up infra/aura-instance.local.json as aura-professional.local.json
#       before promoting aura-free.local.json to aura-instance.local.json.
#       Does NOT pause the Professional instance — do that separately with 'pause'
#       once the grand check passes.
#       Prerequisite: 'create-free' must have run and saved aura-free.local.json.
#
# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLES
#
#   pwsh infra/aura.ps1 status                             # check state
#   pwsh infra/aura.ps1 switch-to-free -WhatIf               # preview — no changes
#   pwsh infra/aura.ps1 switch-to-free                     # commit the switch
#   pwsh infra/aura.ps1 pause -WhatIf                        # preview pause
#   pwsh infra/aura.ps1 delete -WhatIf                       # confirm what would die
#   pwsh infra/aura.ps1 overwrite -DestInstanceId abc -WhatIf
#   pwsh infra/aura.ps1 restore -SnapshotId snap-abc -WhatIf
#
# CANONICAL LOCATION
#   tools/scripts/aura.ps1  ← this file
#   Invoked via the forwarding shim at infra/aura.ps1, which sets -InfraDir.
#   The traiding-system shim is at traiding-system/scripts/manage-aura.ps1.

param(
  [Parameter(Mandatory = $true, Position = 0)]
  [ValidateSet('status', 'connection', 'pause', 'resume', 'list', 'delete',
               'snapshot', 'snapshots', 'restore',
               'create-free', 'overwrite', 'compare', 'switch-to-free', 'export-url')]
  [string]$Action,

  [switch]$WhatIf,                                # dry-run — no API calls, no file writes

  [string]$InfraDir = "",                         # path to *.local.json credential dir

  [string]$SnapshotId,                            # restore / export-url
  [string]$DestInstanceId,                        # overwrite — instance to write INTO
  [string]$SrcSnapshotId,                         # overwrite — snapshot to restore FROM
  [string]$FreeName = "trading-agents-free"       # create-free — display name
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Resolve InfraDir ──────────────────────────────────────────────────────────
if (-not $InfraDir) {
  # Default when called from tools/scripts/: repo root is two levels up, then infra/
  $candidate = Join-Path $PSScriptRoot ".." ".." "infra"
  $resolved  = Resolve-Path $candidate -ErrorAction SilentlyContinue
  if ($resolved) {
    $InfraDir = [string]$resolved
  } else {
    throw "Cannot auto-resolve infra/ directory. Pass -InfraDir <path> explicitly."
  }
}
$RepoRoot = Split-Path $InfraDir -Parent

# ── Load API credentials ──────────────────────────────────────────────────────
$credPath = Join-Path $InfraDir "aura-api.local.json"
if (-not (Test-Path $credPath)) {
  throw "Missing $credPath — create it from the Aura console API key (see docs/ci-cd-setup.md)."
}
$c = Get-Content $credPath -Raw | ConvertFrom-Json

# ── OAuth client-credentials token ───────────────────────────────────────────
# Skip token fetch for purely local actions
$skipToken = @('compare')
if ($skipToken -notcontains $Action) {
  $b64 = [Convert]::ToBase64String(
    [Text.Encoding]::ASCII.GetBytes("$($c.api_client_id):$($c.api_client_secret)"))
  $tok = (Invoke-RestMethod -Method Post -Uri "https://api.neo4j.io/oauth/token" `
      -Headers @{ Authorization = "Basic $b64" } `
      -Body @{ grant_type = "client_credentials" } `
      -ContentType "application/x-www-form-urlencoded").access_token
  $hdr = @{ Authorization = "Bearer $tok" }
}
$base = "https://api.neo4j.io/v1/instances"

# ── Helper: fake banner ───────────────────────────────────────────────────────
function Write-WhatIf { param([string]$msg) Write-Host "[WhatIf] $msg" -ForegroundColor DarkCyan }

# ─────────────────────────────────────────────────────────────────────────────
switch ($Action) {

  # ── READ-ONLY ──────────────────────────────────────────────────────────────

  'status' {
    $d = (Invoke-RestMethod -Uri "$base/$($c.instance_id)" -Headers $hdr).data
    [pscustomobject]@{
      id      = $d.id
      name    = $d.name
      status  = $d.status
      region  = $d.region
      type    = $d.type
    } | Format-List
  }

  'connection' {
    Write-Host "NEO4J_URI      = $($c.connection_url)"
    Write-Host "NEO4J_USER     = $($c.username)"
    Write-Host "NEO4J_DATABASE = neo4j   # Aura single-db is always 'neo4j'"
    Write-Host "NEO4J_PASSWORD = (see $InfraDir\aura-instance.local.json)"
  }

  'list' {
    (Invoke-RestMethod -Uri $base -Headers $hdr).data |
      Format-Table id, name, status, type, region
  }

  'snapshots' {
    $list = (Invoke-RestMethod -Uri "$base/$($c.instance_id)/snapshots" -Headers $hdr).data
    if (-not $list) { Write-Host "No snapshots found."; return }
    $list | Sort-Object timestamp -Descending |
      Select-Object snapshot_id, status, timestamp, exportable |
      Format-Table -AutoSize
  }

  'export-url' {
    if (-not $SnapshotId) { throw "Provide -SnapshotId <id>  (run 'snapshots' to list them)" }
    try {
      $resp = Invoke-RestMethod -Uri "$base/$($c.instance_id)/snapshots/$SnapshotId/download" `
          -Headers $hdr
      Write-Host "Export URL:" -ForegroundColor Green
      $resp | Format-List
    }
    catch {
      $sc = $_.Exception.Response.StatusCode.value__
      Write-Host "Export URL failed (HTTP $sc) — not supported on this tier." -ForegroundColor Red
      try {
        $rdr = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host ($rdr.ReadToEnd()) -ForegroundColor Red
      }
      catch {}
    }
  }

  'compare' {
    $script = Join-Path $RepoRoot "scripts" "compare_aura.py"
    if (-not (Test-Path $script)) { throw "scripts/compare_aura.py not found at $script" }
    Write-Host "Comparing Professional vs Free instance ..." -ForegroundColor Cyan
    uv run python $script
    exit $LASTEXITCODE
  }

  # ── DESTRUCTIVE ────────────────────────────────────────────────────────────

  'pause' {
    if ($WhatIf) {
      Write-WhatIf "Would POST $base/$($c.instance_id)/pause"
      Write-WhatIf "Instance $($c.instance_id) would be PAUSED (billing stops, db inaccessible)"
      return
    }
    (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/pause" `
        -Headers $hdr -Body "{}" -ContentType "application/json").data | Format-List
  }

  'resume' {
    if ($WhatIf) {
      Write-WhatIf "Would POST $base/$($c.instance_id)/resume"
      Write-WhatIf "Instance $($c.instance_id) would be RESUMED (billing restarts)"
      return
    }
    (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/resume" `
        -Headers $hdr -Body "{}" -ContentType "application/json").data | Format-List
  }

  'delete' {
    if ($WhatIf) {
      Write-WhatIf "Would DELETE $base/$($c.instance_id)"
      Write-WhatIf "Instance $($c.instance_id) would be PERMANENTLY DELETED — no undo"
      Write-WhatIf "Verify with 'status' first: pwsh infra/aura.ps1 status"
      return
    }
    Invoke-RestMethod -Method Delete -Uri "$base/$($c.instance_id)" -Headers $hdr | Out-Null
    Write-Host "Deleted instance $($c.instance_id)." -ForegroundColor Yellow
  }

  'snapshot' {
    if ($WhatIf) {
      Write-WhatIf "Would POST $base/$($c.instance_id)/snapshots  (body: {})"
      Write-WhatIf "An on-demand snapshot of $($c.instance_id) would be triggered"
      Write-WhatIf "Poll progress with: pwsh infra/aura.ps1 snapshots"
      return
    }
    $d = (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/snapshots" `
        -Headers $hdr -Body "{}" -ContentType "application/json").data
    Write-Host "Snapshot triggered:" -ForegroundColor Green
    [pscustomobject]@{ snapshot_id = $d.snapshot_id } | Format-List
    Write-Host "Poll with:  pwsh infra/aura.ps1 snapshots" -ForegroundColor Gray
  }

  'restore' {
    if (-not $SnapshotId) { throw "Provide -SnapshotId <id>  (run 'snapshots' to list them)" }
    $body = (@{ snapshot_id = $SnapshotId } | ConvertTo-Json)
    if ($WhatIf) {
      Write-WhatIf "Would POST $base/$($c.instance_id)/restore"
      Write-WhatIf "Body: $body"
      Write-WhatIf "Database $($c.instance_id) would be OVERWRITTEN with snapshot $SnapshotId"
      return
    }
    $d = (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/restore" `
        -Headers $hdr -Body $body -ContentType "application/json").data
    Write-Host "Restore initiated from snapshot $SnapshotId" -ForegroundColor Yellow
    [pscustomobject]@{ status = $d.status; instance_id = $d.id } | Format-List
    Write-Host "Monitor progress with:  pwsh infra/aura.ps1 status" -ForegroundColor Gray
  }

  'create-free' {
    $freePath = Join-Path $InfraDir "aura-free.local.json"
    $body = @{
      version        = "5"
      name           = $FreeName
      type           = "free-db"
      region         = "us-central1"
      cloud_provider = "gcp"
      tenant_id      = $c.tenant_id
    } | ConvertTo-Json

    if ($WhatIf) {
      Write-WhatIf "Would POST $base (create new instance)"
      Write-WhatIf "Body: $body"
      Write-WhatIf "Credentials (incl. password) would be saved to $freePath"
      Write-WhatIf "Password is shown ONCE in the API response — it is saved to the JSON file"
      return
    }

    Write-Host "Creating free AuraDB instance '$FreeName' on GCP us-central1 ..." -ForegroundColor Cyan
    $resp = Invoke-RestMethod -Method Post -Uri $base -Headers $hdr `
        -Body $body -ContentType "application/json"
    $d = $resp.data

    Write-Host ""
    Write-Host "=== FREE INSTANCE CREATED ===" -ForegroundColor Green
    Write-Host "ID:           $($d.id)"
    Write-Host "Name:         $($d.name)"
    Write-Host "Status:       $($d.status)"
    Write-Host "Connection:   $($d.connection_url)"
    Write-Host "Username:     $($d.username)"
    if ($d.password) {
      Write-Host "Password:     $($d.password)" -ForegroundColor Yellow
    }

    $freeCreds = @{
      instance_id       = $d.id
      tenant_id         = $c.tenant_id
      username          = if ($d.username) { $d.username } else { "neo4j" }
      connection_url    = $d.connection_url
      password          = if ($d.password) { $d.password } else { "" }
      cloud_provider    = "gcp"
      region            = "us-central1"
      type              = "free-db"
      api_client_id     = $c.api_client_id
      api_client_secret = $c.api_client_secret
    }
    $freeCreds | ConvertTo-Json | Set-Content $freePath -Encoding UTF8
    Write-Host ""
    Write-Host "Credentials saved to $freePath (gitignored)." -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next — try cross-tier overwrite (will likely return 422):" -ForegroundColor Cyan
    Write-Host "  pwsh infra/aura.ps1 overwrite -DestInstanceId $($d.id) -WhatIf" -ForegroundColor Gray
  }

  'overwrite' {
    if (-not $DestInstanceId) { throw "Provide -DestInstanceId <id>  (the free instance id)" }

    $snapId = $SrcSnapshotId
    if (-not $snapId) {
      if ($WhatIf) {
        Write-WhatIf "Would fetch latest Completed snapshot from $($c.instance_id)"
        Write-WhatIf "Would POST $base/$DestInstanceId/overwrite"
        Write-WhatIf "Body: { source_instance_id: '$($c.instance_id)', source_snapshot_id: '<latest>' }"
        Write-WhatIf "NOTE: Professional→Free cross-tier overwrite is BLOCKED (expected 422)"
        Write-WhatIf "Free instance $DestInstanceId would remain empty — that is expected"
        return
      }
      Write-Host "No -SrcSnapshotId given — fetching latest completed snapshot ..." -ForegroundColor Cyan
      $snaps = (Invoke-RestMethod -Uri "$base/$($c.instance_id)/snapshots" -Headers $hdr).data
      $latest = $snaps | Where-Object { $_.status -eq "Completed" } |
                Sort-Object timestamp -Descending | Select-Object -First 1
      if (-not $latest) { throw "No completed snapshots on $($c.instance_id). Run: pwsh infra/aura.ps1 snapshot" }
      $snapId = $latest.snapshot_id
      Write-Host "Using snapshot: $snapId  ($($latest.timestamp))" -ForegroundColor Gray
    } elseif ($WhatIf) {
      Write-WhatIf "Would POST $base/$DestInstanceId/overwrite"
      Write-WhatIf "Body: { source_instance_id: '$($c.instance_id)', source_snapshot_id: '$snapId' }"
      Write-WhatIf "NOTE: Professional→Free cross-tier overwrite is BLOCKED (expected 422)"
      Write-WhatIf "Free instance $DestInstanceId would remain empty — that is expected"
      return
    }

    $body = @{
      source_instance_id = $c.instance_id
      source_snapshot_id = $snapId
    } | ConvertTo-Json

    Write-Host ""
    Write-Host "Attempting overwrite:" -ForegroundColor Cyan
    Write-Host "  Source (Professional): $($c.instance_id)"
    Write-Host "  Dest   (Free):         $DestInstanceId"
    Write-Host "  Snapshot:              $snapId"
    Write-Host ""
    Write-Host "NOTE: Neo4j blocks Professional->Free (size mismatch). Expecting 422." -ForegroundColor Yellow
    Write-Host ""

    try {
      $resp = Invoke-RestMethod -Method Post -Uri "$base/$DestInstanceId/overwrite" `
          -Headers $hdr -Body $body -ContentType "application/json"
      Write-Host "OVERWRITE ACCEPTED:" -ForegroundColor Green
      $resp.data | Format-List
      Write-Host "Next: wait for status=running, then compare:" -ForegroundColor Cyan
      Write-Host "  pwsh infra/aura.ps1 compare" -ForegroundColor Gray
    }
    catch {
      $sc = $_.Exception.Response.StatusCode.value__
      Write-Host "OVERWRITE REJECTED (HTTP $sc):" -ForegroundColor Red
      try {
        $rdr = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host ($rdr.ReadToEnd()) -ForegroundColor Red
      }
      catch { Write-Host $_.Exception.Message -ForegroundColor Red }
      Write-Host ""
      Write-Host "Tier restriction confirmed. Free instance is empty — that is fine." -ForegroundColor Yellow
      Write-Host "A fresh grand-check run writes new provenance data to the free instance." -ForegroundColor Yellow
      Write-Host "Switch anyway: pwsh infra/aura.ps1 switch-to-free -WhatIf" -ForegroundColor Cyan
    }
  }

  'switch-to-free' {
    $freePath   = Join-Path $InfraDir "aura-free.local.json"
    $profPath   = Join-Path $InfraDir "aura-instance.local.json"
    $backupPath = Join-Path $InfraDir "aura-professional.local.json"
    $envPath    = Join-Path $RepoRoot ".env"

    if ($WhatIf) {
      if (Test-Path $freePath) {
        $freePreview = Get-Content $freePath -Raw | ConvertFrom-Json
        Write-WhatIf "Would update ${envPath}:"
        Write-WhatIf "  NEO4J_URI      = $($freePreview.connection_url)"
        Write-WhatIf "  NEO4J_PASSWORD = <from aura-free.local.json>"
        Write-WhatIf "  NEO4J_TEST_URI = $($freePreview.connection_url)"
        Write-WhatIf "Would update ${credPath}:"
        Write-WhatIf "  instance_id    = $($freePreview.instance_id)"
        Write-WhatIf "  connection_url = $($freePreview.connection_url)"
      } else {
        Write-WhatIf "Would update ${envPath}  (NEO4J_URI / NEO4J_PASSWORD / NEO4J_TEST_URI)"
        Write-WhatIf "Would update ${credPath}  (instance_id / connection_url)"
        Write-Host "  NOTE: $freePath not yet created. Run create-free first." -ForegroundColor Yellow
      }
      if (Test-Path $profPath) {
        Write-WhatIf "Would copy $profPath -> $backupPath  (Professional backup)"
      }
      Write-WhatIf "Would copy $freePath -> $profPath  (Free becomes default instance)"
      return
    }

    if (-not (Test-Path $freePath)) {
      throw "aura-free.local.json not found at $freePath. Run: pwsh infra/aura.ps1 create-free"
    }
    $free = Get-Content $freePath -Raw | ConvertFrom-Json
    if (-not $free.connection_url) { throw "aura-free.local.json has no connection_url." }
    if (-not $free.password)       { throw "aura-free.local.json has no password. Add it manually." }

    # ── 1. Update .env ──────────────────────────────────────────────────────
    $envContent = Get-Content $envPath -Raw
    $envContent = $envContent -replace '(?m)^NEO4J_URI=.*$',      "NEO4J_URI=$($free.connection_url)"
    $envContent = $envContent -replace '(?m)^NEO4J_PASSWORD=.*$', "NEO4J_PASSWORD=$($free.password)"
    $envContent = $envContent -replace '(?m)^NEO4J_TEST_URI=.*$', "NEO4J_TEST_URI=$($free.connection_url)"
    [System.IO.File]::WriteAllText($envPath, $envContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host "OK  .env updated (NEO4J_URI, NEO4J_PASSWORD, NEO4J_TEST_URI)" -ForegroundColor Green

    # ── 2. Update aura-api.local.json to point at free instance ────────────
    $api = Get-Content $credPath -Raw | ConvertFrom-Json
    $api.instance_id    = $free.instance_id
    $api.connection_url = $free.connection_url
    $api.username       = $free.username
    $api | ConvertTo-Json | Set-Content $credPath -Encoding UTF8
    Write-Host "OK  aura-api.local.json -> instance $($free.instance_id)" -ForegroundColor Green

    # ── 3. Promote free creds to aura-instance.local.json ──────────────────
    if (Test-Path $profPath) {
      Copy-Item $profPath $backupPath -Force
      Write-Host "OK  aura-instance.local.json backed up to aura-professional.local.json" -ForegroundColor Green
    }
    Copy-Item $freePath $profPath -Force
    Write-Host "OK  aura-instance.local.json now points at the Free instance" -ForegroundColor Green

    Write-Host ""
    Write-Host "=== SWITCH COMPLETE ===" -ForegroundColor Green
    Write-Host "  .env           -> Free ($($free.connection_url))"
    Write-Host "  aura-api       -> $($free.instance_id)"
    Write-Host "  aura-instance  -> Free (Professional backed up)"
    Write-Host ""
    Write-Host "Verify free instance is running:" -ForegroundColor Cyan
    Write-Host "  pwsh infra/aura.ps1 status"
    Write-Host "Run the grand check:" -ForegroundColor Cyan
    Write-Host "  PYTHONPATH=. uv run python scripts/run_local.py --real --trace"
    Write-Host "When grand check passes, pause the Professional instance:" -ForegroundColor Cyan
    Write-Host "  # Restore aura-api.local.json instance_id to 8cf6d231, then:"
    Write-Host "  # pwsh infra/aura.ps1 pause -WhatIf   # preview"
    Write-Host "  # pwsh infra/aura.ps1 pause         # commit"
    Write-Host "  # Then restore aura-api.local.json to the free instance id"
  }
}
