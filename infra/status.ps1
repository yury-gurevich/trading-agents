# status.ps1 — One-command dashboard for the trading-agents fleet.
#
#   pwsh infra/status.ps1            # single snapshot
#   pwsh infra/status.ps1 -Watch     # refresh every 5s (Ctrl-C to stop)
#
# Shows: latest GHCR build run, Container App replica states, Aura instance
# status + live registry node counts. Reads Aura creds from the gitignored
# infra/aura-api.local.json / aura-instance.local.json.

param(
  [switch]$Watch,
  [int]$IntervalSeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'
$RG = "trading-agents"
$SUB = "5ef50a27-50a4-4d90-9695-da61b2309cf3"

function Show-Board {
  try { Clear-Host } catch { Write-Host "`n" }
  Write-Host "┌─ TRADING-AGENTS FLEET ─────────────────────────────────────" -ForegroundColor Cyan
  Write-Host ("│  {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss")) -ForegroundColor DarkGray

  # ── 1. Latest image build ──────────────────────────────────────────────────
  Write-Host "│" ; Write-Host "│ BUILD (GitHub Actions)" -ForegroundColor Yellow
  $run = gh run list --workflow build-images.yml --limit 1 --json status,conclusion,createdAt `
    --jq '.[0] | "\(.status) \(.conclusion // "") \(.createdAt)"' 2>$null
  Write-Host ("│   build-images: {0}" -f ($run ?? "no runs"))

  # ── 2. Container Apps ──────────────────────────────────────────────────────
  Write-Host "│" ; Write-Host "│ CONTAINER APPS ($RG)" -ForegroundColor Yellow
  $apps = az containerapp list --resource-group $RG --subscription $SUB `
    --query "[].{name:name, replicas:properties.runningStatus, rev:properties.latestRevisionName}" -o json 2>$null | ConvertFrom-Json
  if ($apps) {
    foreach ($a in $apps) {
      $reps = (az containerapp replica list --name $a.name --resource-group $RG --subscription $SUB --query "[].name" -o tsv 2>$null | Measure-Object).Count
      Write-Host ("│   {0,-10} status={1,-9} replicas={2}" -f $a.name, $a.replicas, $reps)
    }
  } else { Write-Host "│   (none deployed)" }

  # ── 3. Aura + registry ─────────────────────────────────────────────────────
  Write-Host "│" ; Write-Host "│ NEO4J AURA (registry)" -ForegroundColor Yellow
  $c = Get-Content (Join-Path $PSScriptRoot "aura-api.local.json") -Raw | ConvertFrom-Json
  $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$($c.api_client_id):$($c.api_client_secret)"))
  $tok = (Invoke-RestMethod -Method Post -Uri "https://api.neo4j.io/oauth/token" -Headers @{ Authorization = "Basic $b64" } -Body @{ grant_type = "client_credentials" } -ContentType "application/x-www-form-urlencoded").access_token
  $aura = (Invoke-RestMethod -Uri "https://api.neo4j.io/v1/instances/$($c.instance_id)" -Headers @{ Authorization = "Bearer $tok" }).data
  Write-Host ("│   instance {0}: {1}" -f $c.instance_id, $aura.status)
  if ($aura.status -eq "running") {
    $py = Join-Path $PSScriptRoot "_status_query.local.py"
    @"
import json
from neo4j import GraphDatabase
i = json.load(open(r"$((Join-Path $PSScriptRoot 'aura-instance.local.json'))", encoding="utf-8"))
d = GraphDatabase.driver("$($c.connection_url)", auth=("$($c.username)", i["password"]))
with d.session(database="neo4j") as s:
    for r in s.run("MATCH (n) RETURN labels(n)[0] AS l, count(*) AS c ORDER BY l"):
        print(f"   {r['l']}: {r['c']}")
d.close()
"@ | Out-File $py -Encoding utf8
    uv run python $py 2>$null | ForEach-Object { Write-Host "│$_" }
    Remove-Item $py -Force -ErrorAction SilentlyContinue
  } else {
    Write-Host "│   (paused — resume with: pwsh infra/aura.ps1 resume)" -ForegroundColor DarkGray
  }
  Write-Host "└────────────────────────────────────────────────────────────" -ForegroundColor Cyan
}

az account set --subscription $SUB 2>$null
if ($Watch) {
  while ($true) { Show-Board; Start-Sleep -Seconds $IntervalSeconds }
} else {
  Show-Board
}
