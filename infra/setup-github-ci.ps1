# setup-github-ci.ps1 — Wire the GitHub repo secrets needed by the S76
# build/deploy pipeline (ADR-0011: GHCR container registry).
#
# Prerequisites:
#   gh CLI logged in (gh auth status) with 'repo' scope.
#
# Run from repo root:
#   pwsh infra/setup-github-ci.ps1 -GhcrPat <the-PAT>
#
# What it sets:
#   GHCR_PAT — a classic PAT with ONLY 'read:packages' scope, used by Azure
#              Container Apps to pull private images from ghcr.io. (Push from
#              CI uses the workflow GITHUB_TOKEN, not this secret.)
#
# Why the PAT cannot be created here: GitHub has no API/CLI to mint a personal
# access token (deliberate security measure). Create it once in the browser:
#   https://github.com/settings/tokens/new?scopes=read:packages&description=trading-agents-ghcr-pull
# then pass it to -GhcrPat.

param(
  [Parameter(Mandatory = $true)]
  [string]$GhcrPat,

  [string]$Repo = "yury-gurevich/trading-agents"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "→ Verifying gh auth" -ForegroundColor Cyan
gh auth status | Out-Null

Write-Host "→ Setting GHCR_PAT secret on ${Repo}" -ForegroundColor Cyan
$GhcrPat | gh secret set GHCR_PAT --repo $Repo

Write-Host "`n→ Current repo secrets:" -ForegroundColor Cyan
gh secret list --repo $Repo

Write-Host "`n✓ GitHub CI secrets wired." -ForegroundColor Green
Write-Host "  Build/push (build-images.yml) needs no secret — it uses GITHUB_TOKEN." -ForegroundColor Gray
Write-Host "  Deploy (deploy-agents.yml) Azure auth is set separately (az SP / OIDC)." -ForegroundColor Gray
