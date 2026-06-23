# aura.ps1 — forwarding shim
#
# The canonical script lives at tools/scripts/aura.ps1.
# This shim sets -InfraDir to this directory so credential files are found
# correctly regardless of where the caller's working directory is.
#
# Usage (unchanged from before):
#   pwsh infra/aura.ps1 status
#   pwsh infra/aura.ps1 switch-to-free -WhatIf
#   pwsh infra/aura.ps1 pause -WhatIf
#
# See tools/scripts/aura.ps1 for full parameter and action documentation.

$canonical = Join-Path $PSScriptRoot ".." "tools" "scripts" "aura.ps1"
if (-not (Test-Path $canonical)) {
  throw "Canonical script not found at $canonical"
}

& $canonical -InfraDir $PSScriptRoot @args
