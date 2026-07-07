# status.ps1 — One-command dashboard for the trading-agents fleet.
#
#   pwsh infra/status.ps1            # single snapshot
#   pwsh infra/status.ps1 -Watch     # refresh every 5s (Ctrl-C to stop)
#
# Shows: latest GHCR build run and Container App replica states.

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
      Write-Host ("│   {0,-18} {1,-9} replicas={2}" -f $a.name, $a.replicas, $reps)
    }
  } else { Write-Host "│   (none deployed)" }
  Write-Host "└────────────────────────────────────────────────────────────" -ForegroundColor Cyan
}

az account set --subscription $SUB 2>$null
if ($Watch) {
  while ($true) { Show-Board; Start-Sleep -Seconds $IntervalSeconds }
} else {
  Show-Board
  Start-Sleep -Seconds 5   # hold so the board is readable before the prompt returns
}
