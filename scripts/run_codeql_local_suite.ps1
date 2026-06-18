param(
    [string[]]$Languages = @("python", "yaml", "actions"),
    [switch]$Rebuild,
    [switch]$UpdateBaseline,
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

if (-not $SkipSetup) {
    Write-Host "Step 1/2: Running local CodeQL setup and analysis..."
    $setupScript = Join-Path $repoRoot "scripts\setup_codeql_local.ps1"
    if ($Rebuild) {
        & $setupScript -Languages $Languages -Rebuild
    } else {
        & $setupScript -Languages $Languages
    }
}

Write-Host "Step 2/2: Generating aggregated triage + baseline/diff + owner reports..."
$reportScript = Join-Path $repoRoot "scripts\generate_codeql_reports.ps1"
if ($UpdateBaseline) {
    & $reportScript -UpdateBaseline
} else {
    & $reportScript
}

Write-Host "Done."
Write-Host "Local CodeQL DB cluster: $repoRoot\.codeql-db\all-languages"
Write-Host "SARIF: $repoRoot\.codeql-db\python-security-and-quality.sarif"
Write-Host "SARIF: $repoRoot\.codeql-db\actions-code-scanning.sarif"
Write-Host "YAML analysis skipped by default on CodeQL 2.25.6; no YAML SARIF is produced."
Write-Host "Reports: $repoRoot\.codeql-db\reports"
