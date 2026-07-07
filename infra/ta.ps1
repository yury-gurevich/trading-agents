# ta.ps1 — trading-agents operator CLI. One entry point for the fleet.
#
#   pwsh infra/ta.ps1 <area> <action> [options]
#
# Thin dispatcher over the focused scripts (status/deploy).
# Run `ta` with no args for the menu. Policy lives in ops/; this is the driver.

[CmdletBinding()]
param(
  [Parameter(Position = 0)] [string]$Area,
  [Parameter(Position = 1)] [string]$Action,
  [switch]$Watch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
function Sub($name) { Join-Path $here $name }

function Show-Help {
  Write-Host ""
  Write-Host "  ta — trading-agents operator CLI" -ForegroundColor Cyan
  Write-Host ""
  Write-Host "  status [-Watch]        fleet dashboard (build, apps)"
  Write-Host "  doctor                 run deploy preflight gates (read-only)"
  Write-Host "  deploy <preflight|up|down>   stand up / tear down the fleet"
  Write-Host ""
  Write-Host "  Policy + laws: ops/   |   Cost: 'up' spends; 'down' stops it." -ForegroundColor DarkGray
  Write-Host ""
}

switch ($Area) {
  '' { Show-Help }
  'help' { Show-Help }
  'status' { & (Sub 'status.ps1') -Watch:$Watch }
  'doctor' { & (Sub 'deploy-agents.ps1') preflight }
  'deploy' {
    if (-not $Action) { Write-Host "usage: ta deploy <preflight|up|down>" -ForegroundColor Yellow; break }
    & (Sub 'deploy-agents.ps1') $Action
  }
  default {
    Write-Host "unknown area: '$Area'" -ForegroundColor Red
    Show-Help
  }
}
