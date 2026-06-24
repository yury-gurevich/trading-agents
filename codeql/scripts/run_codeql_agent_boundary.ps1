<#
.SYNOPSIS
    Run the CodeQL agent cross-import boundary query and produce a readable
    markdown report.

.DESCRIPTION
    1. (Optional) Rebuilds the CodeQL Python database from current source.
    2. Runs the AgentCrossImport.ql query against the local Python CodeQL
       database.
    3. Decodes the .bqrs results to CSV.
    4. Generates a human-readable markdown report with a summary table and a
       per-finding detail table.
    5. Generates a SARIF file for GitHub Security / VS Code SARIF Viewer.

    Report and SARIF files are timestamped: yyyy-MM-dd-HH.mm-<name>.
    The latest copy is also written without a timestamp for easy linking.

    Exits 0 when the production codebase is clean (no violations).
    Exits 1 when violations are found.

.PARAMETER Rebuild
    Rebuild the CodeQL database from current source before running the query.

.PARAMETER Database
    Path to the CodeQL database directory.
    Default: .codeql-db\python

.PARAMETER Query
    Path to the .ql query file.
    Default: codeql\python-security\AgentCrossImport.ql

.PARAMETER SearchPath
    Search path for CodeQL packs.
    Default: codeql\python-security

.PARAMETER OutputDir
    Directory for the generated report and SARIF.
    Default: codeql\python-security\reports\agent-cross-import

.EXAMPLE
    .\scripts\run_codeql_agent_boundary.ps1
    Runs the query and writes the report to codeql\python-security\reports\.

.EXAMPLE
    .\scripts\run_codeql_agent_boundary.ps1 -Database .codeql-db\python
    Uses a custom database path.
#>

[CmdletBinding()]
param(
    [switch]$Rebuild,
    [string]$Database = '.codeql-db\python',
    [string]$Query = 'codeql\python-security\AgentCrossImport.ql',
    [string]$SearchPath = 'codeql\python-security',
    [string]$OutputDir = 'codeql\python-security\reports\agent-cross-import'
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Resolve paths relative to the repo root (script lives in scripts/).
# ---------------------------------------------------------------------------

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repoRoot

$codeqlExe = Join-Path $repoRoot '.tools\codeql\codeql.exe'
if (-not (Test-Path $codeqlExe)) {
    throw "CodeQL CLI not found at: $codeqlExe"
}

$queryPath = (Resolve-Path $Query -ErrorAction Stop).Path
$searchPath = (Resolve-Path $SearchPath -ErrorAction Stop).Path

# ---------------------------------------------------------------------------
# Step 0: Rebuild the database if requested (or if it does not exist).
# ---------------------------------------------------------------------------

$dbPath = Join-Path $repoRoot ($Database -replace '/', '\')

if ($Rebuild -or -not (Test-Path $dbPath)) {
    Write-Host ''
    if ($Rebuild) {
        Write-Host '=== Step 0: Rebuilding CodeQL database ===' -ForegroundColor Cyan
    } else {
        Write-Host '=== Step 0: Creating CodeQL database (not found) ===' -ForegroundColor Cyan
    }
    Write-Host "  Database:   $dbPath"
    Write-Host "  Source root: $repoRoot"

    & $codeqlExe database create $dbPath `
        --language=python `
        --source-root=$repoRoot `
        --threads=0 `
        --overwrite

    if ($LASTEXITCODE -ne 0) {
        throw "CodeQL database creation failed (exit code $LASTEXITCODE)."
    }
} else {
    $dbPath = (Resolve-Path $Database -ErrorAction Stop).Path
}

# ---------------------------------------------------------------------------
# Resolve output paths: latest/ (overwritten) + archive/<timestamp>/ (kept).
# ---------------------------------------------------------------------------

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$queryResolved = (Resolve-Path $OutputDir).Path

$latestDir = Join-Path $queryResolved 'latest'
$archiveDir = Join-Path $queryResolved 'archive'
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null
New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

# Timestamp for archive subfolder: yyyy-MM-dd-HH.mm
$timestamp = Get-Date -Format 'yyyy-MM-dd-HH.mm'
$archiveRunDir = Join-Path $archiveDir $timestamp
New-Item -ItemType Directory -Force -Path $archiveRunDir | Out-Null

# Latest copies (overwritten every run, easy to link).
$reportPath = Join-Path $latestDir 'report.md'
$sarifPath = Join-Path $latestDir 'results.sarif'

# Archived copies (never overwritten).
$reportArchive = Join-Path $archiveRunDir 'report.md'
$sarifArchive = Join-Path $archiveRunDir 'results.sarif'

# ---------------------------------------------------------------------------
# Step 1: Run the query.
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '=== Step 1/3: Running CodeQL query ===' -ForegroundColor Cyan
Write-Host "  Database:   $dbPath"
Write-Host "  Query:      $queryPath"
Write-Host "  Pack:       $searchPath"

& $codeqlExe database run-queries $dbPath `
    --search-path=$searchPath `
    $queryPath

if ($LASTEXITCODE -ne 0) {
    throw "CodeQL query execution failed (exit code $LASTEXITCODE)."
}

# The .bqrs result file lives under the database results directory.
$bqrsPath = Join-Path $dbPath 'results\local\python-security\AgentCrossImport.bqrs'
if (-not (Test-Path $bqrsPath)) {
    throw "Expected result file not found: $bqrsPath"
}

# ---------------------------------------------------------------------------
# Step 2: Decode results and generate SARIF.
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '=== Step 2/3: Decoding results + generating SARIF ===' -ForegroundColor Cyan

# Decode to CSV.  The query selects (imp, message), so with
# --entities=url,string we get columns: "imp","URL for imp","col1".
$csvRaw = & $codeqlExe bqrs decode `
    --format=csv `
    --entities=url,string `
    $bqrsPath 2>&1

# Parse the CSV into finding objects.
$csvLines = $csvRaw -split "`r?`n" | Where-Object { $_ -and $_ -notmatch '^"imp"' }
$findings = @()

foreach ($line in $csvLines) {
    # Each CSV row: "Import","file://.../path:line:col:col","message text"
    $parts = $line -split '","'
    if ($parts.Count -lt 3) { continue }

    # Extract the file URL from the second column (strip leading quote).
    $urlPart = $parts[1] -replace '^"', ''
    # URL format from CodeQL: file://C:/Users/.../file.py:13:1:13:43
    # Strip the file:// prefix (note: two slashes, not three, on Windows).
    $urlPart = $urlPart -replace '^file://', ''
    # The path ends with :line:col:col (4 colon-separated numbers at the end).
    # Use regex to split path from the line:col:col suffix.
    if ($urlPart -match '^(.+):(\d+):\d+:\d+:\d+$') {
        $filePath = $Matches[1] -replace '/', '\'
        $lineNum = $Matches[2]
    } elseif ($urlPart -match '^(.+):(\d+):\d+:\d+$') {
        $filePath = $Matches[1] -replace '/', '\'
        $lineNum = $Matches[2]
    } else {
        $filePath = $urlPart -replace '/', '\'
        $lineNum = '?'
    }

    # Extract the message from the third column (strip trailing quote).
    $message = ($parts[2] -replace '"$', '') -replace '\\', '\'

    # Parse agent names from the message:
    # "Agent 'monitor' imports agent 'execution' - ..."
    if ($message -match "Agent '([^']+)' imports agent '([^']+)'") {
        $importingAgent = $Matches[1]
        $importedAgent = $Matches[2]
    } else {
        $importingAgent = '?'
        $importedAgent = '?'
    }

    $findings += [PSCustomObject]@{
        ImportingAgent = $importingAgent
        ImportedAgent  = $importedAgent
        File           = $filePath
        Line           = $lineNum
        Message        = $message
    }
}

# Generate SARIF.
& $codeqlExe database interpret-results $dbPath `
    --format=sarif-latest `
    --output=$sarifPath `
    --search-path=$searchPath `
    $queryPath

if ($LASTEXITCODE -ne 0) {
    Write-Warning "SARIF generation failed (exit code $LASTEXITCODE). Continuing with report."
}

# ---------------------------------------------------------------------------
# Step 3: Generate the markdown report.
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '=== Step 3/3: Generating markdown report ===' -ForegroundColor Cyan

$scanDate = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
$violationCount = $findings.Count

$lines = @()

$lines += '# CodeQL Report: Agent Cross-Import Boundary Check'
$lines += ''
$lines += '**Scan date:** ' + $scanDate
$lines += ''
$lines += '## Result'
$lines += ''
$lines += '| Metric | Count |'
$lines += '| --- | --- |'

if ($violationCount -eq 0) {
    $lines += '| **Violations in production code** | **0** PASS |'
} else {
    $lines += "| **Violations in production code** | **$violationCount** FAIL |"
}

$lines += ''

if ($violationCount -eq 0) {
    $lines += '**Verdict:** The production codebase is clean. No agent imports another agent.'
} else {
    $lines += '**Verdict:** Violations found -- see the table below.'
}

$lines += ''
$lines += '---'
$lines += ''
$lines += '## Scan details'
$lines += ''
$lines += "**Query:** ``local/py/agent-cross-import`` (``$Query``)"
$lines += "**Database:** ``$Database``"
$lines += '**Scope:** Production code only -- test files (``**/tests/**``) excluded'
$lines += ''
$lines += '## Rule'
$lines += ''
$lines += '> Agents must not import other agents. Each agent is an island, joined only'
$lines += '> by the shared ``contracts`` vocabulary and the plumbing ``kernel``. Agents'
$lines += '> talk only via typed messages on the bus.'
$lines += ''
$lines += 'The 12 independent agent packages (from ``.importlinter:contract:agents-are-islands``):'
$lines += ''
$lines += '```text'
$lines += 'provider  scanner  analyst  forecaster  portfolio_manager  execution'
$lines += 'monitor   reporter  researcher  curator  operator  supervisor'
$lines += '```'
$lines += ''
$lines += '---'
$lines += ''

if ($violationCount -gt 0) {
    $lines += '## Violations'
    $lines += ''
    $lines += '| # | Importing agent | Imported agent | File | Line |'
    $lines += '| --- | --- | --- | --- | --- |'

    $i = 1
    foreach ($f in $findings) {
        $lines += "| $i | $($f.ImportingAgent) | $($f.ImportedAgent) | $($f.File) | $($f.Line) |"
        $i++
    }
    $lines += ''
    $lines += '---'
    $lines += ''
}

$lines += '## Outputs'
$lines += ''
$lines += '| File | Format | Findings |'
$lines += '| --- | --- | --- |'
$lines += "| ``$bqrsPath`` | Binary | $violationCount |"

if (Test-Path $sarifPath) {
    $lines += "| ``$sarifPath`` | SARIF 2.1.0 | $violationCount |"
}

$lines += "| ``$reportPath`` | Markdown | $violationCount |"
$lines += ''
$lines += '---'
$lines += ''
$lines += '## How to reproduce'
$lines += ''
$lines += '```powershell'
$lines += '# Rebuild database from current source + run query + generate report:'
$lines += '.\scripts\run_codeql_agent_boundary.ps1 -Rebuild'
$lines += ''
$lines += '# Run against the existing database (no rebuild):'
$lines += '.\scripts\run_codeql_agent_boundary.ps1'
$lines += '```'

$reportContent = $lines -join "`n"
[System.IO.File]::WriteAllText($reportPath, $reportContent, (New-Object System.Text.UTF8Encoding $false))

# Write archived copies for history.
[System.IO.File]::WriteAllText($reportArchive, $reportContent, (New-Object System.Text.UTF8Encoding $false))
if (Test-Path $sarifPath) {
    Copy-Item -Path $sarifPath -Destination $sarifArchive -Force
}

# ---------------------------------------------------------------------------
# Update the per-query INDEX.md with a row for this run.
# ---------------------------------------------------------------------------

$indexPath = Join-Path $queryResolved 'INDEX.md'
$scanTimeShort = Get-Date -Format 'yyyy-MM-dd HH:mm'
$notes = if ($Rebuild) { 'Fresh database rebuild' } else { 'Existing database' }

$indexRow = "| [archive/$timestamp/](archive/$timestamp/) | $violationCount | $notes |"

if (Test-Path $indexPath) {
    # Insert the new row after the table header separator line in the
    # "Archived scans" section, keeping newest at the top.
    # Read as UTF-8 explicitly -- Get-Content -Raw uses Windows-1252 by default.
    $indexContent = [System.IO.File]::ReadAllText($indexPath, [System.Text.Encoding]::UTF8)
    if ($indexContent -match "(?s)(## Archived scans.*?\| --- \| --- \| --- \|`r?`n)(.*)") {
        $before = $Matches[1]
        $after = $Matches[2]
        $indexContent = $before + $indexRow + "`r`n" + $after
        [System.IO.File]::WriteAllText($indexPath, $indexContent, (New-Object System.Text.UTF8Encoding $false))
    }
}

# ---------------------------------------------------------------------------
# Print summary to console.
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  CodeQL Agent Cross-Import Boundary' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan

if ($violationCount -eq 0) {
    Write-Host "  Violations:  $violationCount" -ForegroundColor Green
} else {
    Write-Host "  Violations:  $violationCount" -ForegroundColor Red
}

Write-Host "  Latest report:  $reportPath"
Write-Host "  Latest SARIF:   $sarifPath"
Write-Host "  Archived:       $archiveRunDir"
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

if ($violationCount -gt 0) {
    Write-Host '  Findings:' -ForegroundColor Red
    foreach ($f in $findings) {
        Write-Host "    $($f.ImportingAgent) -> $($f.ImportedAgent)  $($f.File):$($f.Line)" -ForegroundColor Yellow
    }
    Write-Host ''
    exit 1
}

exit 0
