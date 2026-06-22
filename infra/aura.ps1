# aura.ps1 — Manage the trading-agents Neo4j Aura instance via the Aura API.
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

param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('status', 'connection', 'pause', 'resume', 'list', 'delete', 'snapshot', 'snapshots', 'restore')]
  [string]$Action,
  [string]$SnapshotId  # required for 'restore'
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
    [pscustomobject]@{ id = $d.id; name = $d.name; status = $d.status; region = $d.region } | Format-List
  }
  'connection' {
    Write-Host "NEO4J_URI      = $($c.connection_url)"
    Write-Host "NEO4J_USER     = $($c.username)"
    Write-Host "NEO4J_DATABASE = neo4j   # Aura single-db is always 'neo4j'"
    Write-Host "NEO4J_PASSWORD = (see infra/aura-instance.local.json)"
  }
  'pause' { (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/pause" -Headers $hdr -Body "{}" -ContentType "application/json").data | Format-List }
  'resume' { (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/resume" -Headers $hdr -Body "{}" -ContentType "application/json").data | Format-List }
  'list' { (Invoke-RestMethod -Uri $base -Headers $hdr).data | Format-Table id, name, status }
  'delete' {
    Invoke-RestMethod -Method Delete -Uri "$base/$($c.instance_id)" -Headers $hdr | Out-Null
    Write-Host "Deleted instance $($c.instance_id)." -ForegroundColor Yellow
  }
  'snapshot' {
    $d = (Invoke-RestMethod -Method Post -Uri "$base/$($c.instance_id)/snapshots" `
        -Headers $hdr -Body "{}" -ContentType "application/json").data
    Write-Host "Snapshot triggered:" -ForegroundColor Green
    [pscustomobject]@{ snapshot_id = $d.snapshot_id; status = $d.status; timestamp = $d.timestamp } | Format-List
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
}
