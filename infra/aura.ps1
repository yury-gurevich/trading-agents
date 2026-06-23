# aura.ps1 — Manage Neo4j Aura instances via the Aura API.
#
# All Aura management is scripted here — no console clicks needed. API
# credentials and the instance id live in infra/aura-api.local.json (gitignored);
# that file is created once from the Aura console API key.
#
# Usage:
#   pwsh infra/aura.ps1 status        # provisioning/running/paused + health
#   pwsh infra/aura.ps1 connection    # print connection URL + username
#   pwsh infra/aura.ps1 pause         # stop billing while idle
#   pwsh infra/aura.ps1 resume        # bring it back
#   pwsh infra/aura.ps1 list          # all instances in the tenant
#   pwsh infra/aura.ps1 delete        # tear it down (asks nothing — scripted)
#   pwsh infra/aura.ps1 snapshot      # trigger an on-demand backup snapshot
#   pwsh infra/aura.ps1 snapshots     # list all snapshots (id, status, timestamp)
#   pwsh infra/aura.ps1 restore -SnapshotId <id>  # restore instance from snapshot
#
#   # ── multi-instance / migration operations ───────────────────────────────
#   pwsh infra/aura.ps1 create-free [-FreeName <name>]
#       Create a new AuraDB Free instance (GCP us-central1).
#       Saves full connection details (including password) to
#       infra/aura-free.local.json (gitignored). Password is shown and saved.
#
#   pwsh infra/aura.ps1 overwrite -DestInstanceId <id> [-SrcSnapshotId <id>]
#       Attempt to overwrite DEST with the Professional source instance data.
#       Neo4j blocks Professional→Free (size mismatch) — expected 422.
#
#   pwsh infra/aura.ps1 compare
#       Run scripts/compare_aura.py — side-by-side node/rel counts for both
#       instances; prints IDENTICAL or DIVERGED with a diff table.
#
#   pwsh infra/aura.ps1 switch-to-free
#       Rewrite .env and infra/aura-api.local.json to point at the Free instance.
#       Backs up infra/aura-instance.local.json as aura-professional.local.json.
#       Does NOT pause the Professional instance — do that separately with 'pause'
#       once you have confirmed the grand check passes.
#
#   pwsh infra/aura.ps1 export-url -SnapshotId <id>
#       Get the download URL for an exportable snapshot (if supported by tier).

param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('status', 'connection', 'pause', 'resume', 'list', 'delete',
               'snapshot', 'snapshots', 'restore',
               'create-free', 'overwrite', 'compare', 'switch-to-free', 'export-url')]
  [string]$Action,
  [string]$SnapshotId,       # restore / export-url
  [string]$DestInstanceId,   # overwrite — destination (the free instance)
  [string]$SrcSnapshotId,    # overwrite — snapshot from the source (optional; latest if omitted)
  [string]$FreeName = "trading-agents-free"  # create-free — display name
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$credPath = Join-Path $PSScriptRoot "aura-api.local.json"
if (-not (Test-Path $credPath)) {
  throw "Missing $credPath — create it from the Aura console API key (see docs/ci-cd-setup.md)."
}
$c = Get-Content $credPath -Raw | ConvertFrom-Json

# ── OAuth client-credentials token ────────────────────────────────────────────
$b64 = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes("$($c.api_client_id):$($c.api_client_secret)"))
$tok = (Invoke-RestMethod -Method Post -Uri "https://api.neo4j.io/oauth/token" `
    -Headers @{ Authorization = "Basic $b64" } `
    -Body @{ grant_type = "client_credentials" } `
    -ContentType "application/x-www-form-urlencoded").access_token
$hdr = @{ Authorization = "Bearer $tok" }
$base = "https://api.neo4j.io/v1/instances"

switch ($Action) {
  'status' {
    $d = (Invoke-RestMethod -Uri "$base/$($c.instance_id)" -Headers $hdr).data
    [pscustomobject]@{ id = $d.id; name = $d.name; status = $d.status; region = $d.region; type = $d.type } | Format-List
  }
  'connection' {
    Write-Host "NEO4J_URI      = $($c.connection_url)"
    Write-Host "NEO4J_USER     = $($c.username)"
    Write-Host "NEO4J_DATABASE = neo4j   # Aura single-db is always 'neo4j'"
    Write-Host "NEO4J_PASSWORD = (see infra/aura-instance.local.json)"
  }
  'pause'   { (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/pause"  -Headers $hdr -Body "{}" -ContentType "application/json").data | Format-List }
  'resume'  { (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/resume" -Headers $hdr -Body "{}" -ContentType "application/json").data | Format-List }
  'list'    { (Invoke-RestMethod -Uri $base -Headers $hdr).data | Format-Table id, name, status, type, region }
  'delete'  {
    Invoke-RestMethod -Method Delete -Uri "$base/$($c.instance_id)" -Headers $hdr | Out-Null
    Write-Host "Deleted instance $($c.instance_id)." -ForegroundColor Yellow
  }
  'snapshot' {
    $d = (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/snapshots" `
        -Headers $hdr -Body "{}" -ContentType "application/json").data
    Write-Host "Snapshot triggered:" -ForegroundColor Green
    [pscustomobject]@{ snapshot_id = $d.snapshot_id } | Format-List
    Write-Host "Poll with:  pwsh infra/aura.ps1 snapshots" -ForegroundColor Gray
  }
  'snapshots' {
    $list = (Invoke-RestMethod -Uri "$base/$($c.instance_id)/snapshots" -Headers $hdr).data
    if (-not $list) { Write-Host "No snapshots found."; return }
    $list | Sort-Object timestamp -Descending |
      Select-Object snapshot_id, status, timestamp, exportable |
      Format-Table -AutoSize
  }
  'restore' {
    if (-not $SnapshotId) { throw "Provide -SnapshotId <id>  (run 'snapshots' to list them)" }
    $body = (@{ snapshot_id = $SnapshotId } | ConvertTo-Json)
    $d = (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/restore" `
        -Headers $hdr -Body $body -ContentType "application/json").data
    Write-Host "Restore initiated from snapshot $SnapshotId" -ForegroundColor Yellow
    [pscustomobject]@{ status = $d.status; instance_id = $d.id } | Format-List
    Write-Host "Monitor progress with:  pwsh infra/aura.ps1 status" -ForegroundColor Gray
  }

  # ── multi-instance operations ──────────────────────────────────────────────

  'create-free' {
    $body = @{
      version        = "5"
      name           = $FreeName
      type           = "free-db"
      region         = "us-central1"
      cloud_provider = "gcp"
      tenant_id      = $c.tenant_id
    } | ConvertTo-Json

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

    # Save full details (including password) to aura-free.local.json.
    $freeCreds = @{
      instance_id    = $d.id
      tenant_id      = $c.tenant_id
      username       = if ($d.username) { $d.username } else { "neo4j" }
      connection_url = $d.connection_url
      password       = if ($d.password) { $d.password } else { "" }
      cloud_provider = "gcp"
      region         = "us-central1"
      type           = "free-db"
      api_client_id  = $c.api_client_id
      api_client_secret = $c.api_client_secret
    }
    $freePath = Join-Path $PSScriptRoot "aura-free.local.json"
    $freeCreds | ConvertTo-Json | Set-Content $freePath -Encoding UTF8
    Write-Host ""
    Write-Host "Credentials saved to infra/aura-free.local.json (gitignored)." -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next — try cross-tier overwrite (will likely return 422):" -ForegroundColor Cyan
    Write-Host "  pwsh infra/aura.ps1 overwrite -DestInstanceId $($d.id)" -ForegroundColor Gray
  }

  'overwrite' {
    if (-not $DestInstanceId) { throw "Provide -DestInstanceId <id>  (the free instance id)" }

    $snapId = $SrcSnapshotId
    if (-not $snapId) {
      Write-Host "No -SrcSnapshotId given — fetching latest completed snapshot ..." -ForegroundColor Cyan
      $snaps = (Invoke-RestMethod -Uri "$base/$($c.instance_id)/snapshots" -Headers $hdr).data
      $latest = $snaps | Where-Object { $_.status -eq "Completed" } |
                Sort-Object timestamp -Descending | Select-Object -First 1
      if (-not $latest) { throw "No completed snapshots on $($c.instance_id). Run: pwsh infra/aura.ps1 snapshot" }
      $snapId = $latest.snapshot_id
      Write-Host "Using snapshot: $snapId  ($($latest.timestamp))" -ForegroundColor Gray
    }

    $body = @{
      source_instance_id  = $c.instance_id
      source_snapshot_id  = $snapId
    } | ConvertTo-Json

    Write-Host ""
    Write-Host "Attempting overwrite:" -ForegroundColor Cyan
    Write-Host "  Source (Professional): $($c.instance_id)"
    Write-Host "  Dest   (Free):         $DestInstanceId"
    Write-Host "  Snapshot:              $snapId"
    Write-Host ""
    Write-Host "NOTE: Neo4j blocks Professional→Free (size mismatch). Expecting 422." -ForegroundColor Yellow
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
      $statusCode = $_.Exception.Response.StatusCode.value__
      Write-Host "OVERWRITE REJECTED (HTTP $statusCode):" -ForegroundColor Red
      try {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host ($reader.ReadToEnd()) -ForegroundColor Red
      }
      catch { Write-Host $_.Exception.Message -ForegroundColor Red }
      Write-Host ""
      Write-Host "Tier restriction confirmed. Free instance is empty — that is fine." -ForegroundColor Yellow
      Write-Host "A fresh grand-check run writes new provenance data to the free instance." -ForegroundColor Yellow
      Write-Host "Switch anyway: pwsh infra/aura.ps1 switch-to-free" -ForegroundColor Cyan
    }
  }

  'compare' {
    $script = Join-Path $PSScriptRoot ".." "scripts" "compare_aura.py"
    if (-not (Test-Path $script)) { throw "scripts/compare_aura.py not found." }
    Write-Host "Comparing Professional vs Free instance ..." -ForegroundColor Cyan
    uv run python $script
    # Exit code propagates: 0 = identical, 1 = diverged, 2 = error
    exit $LASTEXITCODE
  }

  'switch-to-free' {
    $freePath = Join-Path $PSScriptRoot "aura-free.local.json"
    if (-not (Test-Path $freePath)) {
      throw "aura-free.local.json not found. Run: pwsh infra/aura.ps1 create-free"
    }
    $free = Get-Content $freePath -Raw | ConvertFrom-Json
    if (-not $free.connection_url) { throw "aura-free.local.json has no connection_url." }
    if (-not $free.password)       { throw "aura-free.local.json has no password. Add it manually." }

    $profPath = Join-Path $PSScriptRoot "aura-instance.local.json"
    $backupPath = Join-Path $PSScriptRoot "aura-professional.local.json"

    # ── 1. Update .env ──────────────────────────────────────────────────────
    $envPath = Join-Path $PSScriptRoot ".." ".env"
    $env = Get-Content $envPath -Raw

    # Replace the three Neo4j lines (value only, preserves inline comments)
    $env = $env -replace '(?m)^NEO4J_URI=.*$',      "NEO4J_URI=$($free.connection_url)"
    $env = $env -replace '(?m)^NEO4J_PASSWORD=.*$', "NEO4J_PASSWORD=$($free.password)"
    $env = $env -replace '(?m)^NEO4J_TEST_URI=.*$', "NEO4J_TEST_URI=$($free.connection_url)"
    # Update the comment block to reflect the switch
    $env = $env -replace '# ── Neo4j \(graph store.*\n.*NEW DEFAULT.*', `
      "# ── Neo4j (graph store, ADR-0001) — SWITCHED TO FREE 2026-06-23 ──────────────"

    [System.IO.File]::WriteAllText($envPath, $env, [System.Text.UTF8Encoding]::new($false))
    Write-Host "✓  .env updated (NEO4J_URI, NEO4J_PASSWORD, NEO4J_TEST_URI)" -ForegroundColor Green

    # ── 2. Update aura-api.local.json to point at free instance ────────────
    $api = Get-Content $credPath -Raw | ConvertFrom-Json
    $api.instance_id    = $free.instance_id
    $api.connection_url = $free.connection_url
    $api.username       = $free.username
    $api | ConvertTo-Json | Set-Content $credPath -Encoding UTF8
    Write-Host "✓  aura-api.local.json → instance $($free.instance_id)" -ForegroundColor Green

    # ── 3. Promote free creds to aura-instance.local.json ──────────────────
    if (Test-Path $profPath) {
      Copy-Item $profPath $backupPath -Force
      Write-Host "✓  aura-instance.local.json backed up to aura-professional.local.json" -ForegroundColor Green
    }
    Copy-Item $freePath $profPath -Force
    Write-Host "✓  aura-instance.local.json now points at the Free instance" -ForegroundColor Green

    Write-Host ""
    Write-Host "=== SWITCH COMPLETE ===" -ForegroundColor Green
    Write-Host "  .env              → Free ($($free.connection_url))"
    Write-Host "  aura-api.local    → $($free.instance_id)"
    Write-Host "  aura-instance     → Free (Professional backed up)"
    Write-Host ""
    Write-Host "Verify free instance is running:" -ForegroundColor Cyan
    Write-Host "  pwsh infra/aura.ps1 status"
    Write-Host "Then run the grand check:" -ForegroundColor Cyan
    Write-Host "  PYTHONPATH=. uv run python scripts/run_local.py --real --trace"
    Write-Host "When grand check passes, pause the Professional instance:" -ForegroundColor Cyan
    Write-Host "  # (restore aura-api.local.json instance_id to 8cf6d231 first, then:)"
    Write-Host "  # pwsh infra/aura.ps1 pause"
    Write-Host "  # then restore aura-api.local.json to the free instance again"
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
      $statusCode = $_.Exception.Response.StatusCode.value__
      Write-Host "Export URL failed (HTTP $statusCode) — not supported on this tier." -ForegroundColor Red
      try {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host ($reader.ReadToEnd()) -ForegroundColor Red
      }
      catch {}
    }
  }
}
