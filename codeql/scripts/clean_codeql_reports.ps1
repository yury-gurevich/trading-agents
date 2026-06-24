<#
.SYNOPSIS
    Delete CodeQL scan reports -- archived runs, latest results, or both.

.DESCRIPTION
    The reports folder is organised as:

        reports/
          <query-folder>/
            latest/              # overwritten every run
            archive/
              yyyy-MM-dd-HH.mm/  # one subfolder per run

    This script deletes archived runs (and optionally the latest results)
    with several filtering modes:

      - KeepNewest N   Keep the N most recent archive subfolders per query,
                       delete the rest.
      - OlderThanDays  Delete archive subfolders older than N days.
      - AllArchives    Delete every archive subfolder (keeps latest/).
      - Everything     Delete latest/ and archive/ contents (keeps INDEX.md).

    Dry-run mode (-WhatIf) shows what would be deleted without removing it.

.PARAMETER ReportsDir
    Root reports directory.
    Default: codeql\python-security\reports

.PARAMETER KeepNewest
    Keep only the N most recent archive subfolders per query folder.
    Older archives are deleted.  0 = delete all archives.

.PARAMETER OlderThanDays
    Delete archive subfolders whose timestamp is older than N days.

.PARAMETER AllArchives
    Delete all archive subfolders under every query folder.  latest/ is kept.

.PARAMETER Everything
    Delete all report and SARIF files (latest/ and archive/ contents).
    INDEX.md files are preserved.

.PARAMETER WhatIf
    Show what would be deleted without actually deleting anything.

.EXAMPLE
    .\scripts\clean_codeql_reports.ps1 -KeepNewest 10
    Keep the 10 most recent archives per query; delete the rest.

.EXAMPLE
    .\scripts\clean_codeql_reports.ps1 -OlderThanDays 30
    Delete archives older than 30 days.

.EXAMPLE
    .\scripts\clean_codeql_reports.ps1 -AllArchives -WhatIf
    Preview deleting all archives (keeps latest/).

.EXAMPLE
    .\scripts\clean_codeql_reports.ps1 -Everything
    Wipe all report files; keep only the INDEX.md files.
#>

[CmdletBinding(SupportsShouldProcess, DefaultParameterSetName = 'Help')]
param(
    [Parameter(ParameterSetName = 'Help')]
    [switch]$Help,

    [string]$ReportsDir = 'codeql\python-security\reports',

    [Parameter(ParameterSetName = 'KeepNewest')]
    [int]$KeepNewest,

    [Parameter(ParameterSetName = 'OlderThanDays')]
    [int]$OlderThanDays,

    [Parameter(ParameterSetName = 'AllArchives')]
    [switch]$AllArchives,

    [Parameter(ParameterSetName = 'Everything')]
    [switch]$Everything
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Resolve paths relative to the repo root (script lives in scripts/).
# ---------------------------------------------------------------------------

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repoRoot

if (-not (Test-Path $ReportsDir)) {
    Write-Host "Reports directory not found: $ReportsDir" -ForegroundColor Yellow
    Write-Host 'Nothing to clean.'
    exit 0
}

$reportsResolved = (Resolve-Path $ReportsDir).Path

# Validate parameter set -- exactly one mode is required.
$paramSet = $PSCmdlet.ParameterSetName

if ($paramSet -eq 'Help') {
    Write-Host 'clean_codeql_reports.ps1 -- delete CodeQL scan reports' -ForegroundColor Cyan
    Write-Host ''
    Write-Host 'Usage:'
    Write-Host '  .\scripts\clean_codeql_reports.ps1 -KeepNewest <N>     Keep N most recent archives per query'
    Write-Host '  .\scripts\clean_codeql_reports.ps1 -OlderThanDays <N>  Delete archives older than N days'
    Write-Host '  .\scripts\clean_codeql_reports.ps1 -AllArchives        Delete all archives (keep latest/)'
    Write-Host '  .\scripts\clean_codeql_reports.ps1 -Everything         Delete all report files (keep INDEX.md)'
    Write-Host ''
    Write-Host 'Add -WhatIf to preview without deleting.'
    exit 0
}

# ---------------------------------------------------------------------------
# Enumerate query folders (subdirectories with an archive/ subfolder).
# ---------------------------------------------------------------------------

$queryFolders = Get-ChildItem $reportsResolved -Directory | Where-Object {
    Test-Path (Join-Path $_.FullName 'archive')
}

if ($queryFolders.Count -eq 0) {
    Write-Host "No query folders found under: $reportsResolved" -ForegroundColor Yellow
    exit 0
}

$deletedCount = 0
$keptCount = 0
$isDryRun = -not $PSCmdlet.ShouldProcess('', '')
$action = if ($isDryRun) { 'Would delete' } else { 'Delete' }

# ---------------------------------------------------------------------------
# Helper: delete a directory with WhatIf support.
# ---------------------------------------------------------------------------

function Remove-ReportDir {
    param([string]$Path)

    if ($PSCmdlet.ShouldProcess($Path, 'Remove directory')) {
        Remove-Item -Path $Path -Recurse -Force
    }
    Write-Host "  $action`: $Path" -ForegroundColor $(if ($isDryRun) { 'Yellow' } else { 'Red' })
}

# ---------------------------------------------------------------------------
# Mode: Everything -- wipe latest/ and archive/ contents, keep INDEX.md.
# ---------------------------------------------------------------------------

if ($Everything) {
    Write-Host ''
    Write-Host '=== Deleting ALL report files (keeping INDEX.md) ===' -ForegroundColor Cyan
    Write-Host ''

    foreach ($qf in $queryFolders) {
        Write-Host "Query: $($qf.Name)"

        $latestDir = Join-Path $qf.FullName 'latest'
        $archiveDir = Join-Path $qf.FullName 'archive'

        if (Test-Path $latestDir) {
            $files = Get-ChildItem $latestDir -File -ErrorAction SilentlyContinue
            foreach ($f in $files) {
                if ($PSCmdlet.ShouldProcess($f.FullName, 'Remove file')) {
                    Remove-Item $f.FullName -Force
                }
                Write-Host "  $action`: $($f.FullName)" -ForegroundColor $(if ($isDryRun) { 'Yellow' } else { 'Red' })
                $deletedCount++
            }
        }

        if (Test-Path $archiveDir) {
            $runs = Get-ChildItem $archiveDir -Directory -ErrorAction SilentlyContinue
            foreach ($run in $runs) {
                Remove-ReportDir $run.FullName
                $deletedCount++
            }
        }
        Write-Host ''
    }
}

# ---------------------------------------------------------------------------
# Mode: AllArchives -- delete every archive subfolder, keep latest/.
# ---------------------------------------------------------------------------

if ($AllArchives) {
    Write-Host ''
    Write-Host '=== Deleting ALL archives (keeping latest/) ===' -ForegroundColor Cyan
    Write-Host ''

    foreach ($qf in $queryFolders) {
        Write-Host "Query: $($qf.Name)"

        $archiveDir = Join-Path $qf.FullName 'archive'
        if (-not (Test-Path $archiveDir)) {
            Write-Host '  No archive folder.'
            Write-Host ''
            continue
        }

        $runs = Get-ChildItem $archiveDir -Directory -ErrorAction SilentlyContinue | Sort-Object Name
        if ($runs.Count -eq 0) {
            Write-Host '  Archive is empty.'
            Write-Host ''
            continue
        }

        foreach ($run in $runs) {
            Remove-ReportDir $run.FullName
            $deletedCount++
        }
        Write-Host ''
    }
}

# ---------------------------------------------------------------------------
# Mode: OlderThanDays -- delete archive subfolders older than N days.
# ---------------------------------------------------------------------------

if ($PSBoundParameters.ContainsKey('OlderThanDays')) {
    if ($OlderThanDays -lt 0) {
        throw '-OlderThanDays must be 0 or positive.'
    }

    $cutoff = (Get-Date).AddDays(-$OlderThanDays)

    Write-Host ''
    Write-Host "=== Deleting archives older than $OlderThanDays day(s) (before $($cutoff.ToString('yyyy-MM-dd HH:mm'))) ===" -ForegroundColor Cyan
    Write-Host ''

    foreach ($qf in $queryFolders) {
        Write-Host "Query: $($qf.Name)"

        $archiveDir = Join-Path $qf.FullName 'archive'
        if (-not (Test-Path $archiveDir)) {
            Write-Host '  No archive folder.'
            Write-Host ''
            continue
        }

        $runs = Get-ChildItem $archiveDir -Directory -ErrorAction SilentlyContinue
        $deleted = $false

        foreach ($run in $runs) {
            # Folder name is yyyy-MM-dd-HH.mm
            if ($run.Name -match '^(\d{4})-(\d{2})-(\d{2})-(\d{2})\.(\d{2})$') {
                $runDate = [datetime]::ParseExact($run.Name, 'yyyy-MM-dd-HH.mm', $null)
            } else {
                # Fallback: use folder last-write time.
                $runDate = $run.LastWriteTime
            }

            if ($runDate -lt $cutoff) {
                Remove-ReportDir $run.FullName
                $deletedCount++
                $deleted = $true
            } else {
                $keptCount++
            }
        }

        if (-not $deleted) {
            Write-Host '  Nothing to delete (all archives are within the age window).'
        }
        Write-Host ''
    }
}

# ---------------------------------------------------------------------------
# Mode: KeepNewest -- keep N most recent archives per query, delete the rest.
# ---------------------------------------------------------------------------

if ($PSBoundParameters.ContainsKey('KeepNewest')) {
    if ($KeepNewest -lt 0) {
        throw '-KeepNewest must be 0 or positive.'
    }

    Write-Host ''
    Write-Host "=== Keeping $KeepNewest most recent archive(s) per query ===" -ForegroundColor Cyan
    Write-Host ''

    foreach ($qf in $queryFolders) {
        Write-Host "Query: $($qf.Name)"

        $archiveDir = Join-Path $qf.FullName 'archive'
        if (-not (Test-Path $archiveDir)) {
            Write-Host '  No archive folder.'
            Write-Host ''
            continue
        }

        $runs = Get-ChildItem $archiveDir -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending

        if ($runs.Count -eq 0) {
            Write-Host '  Archive is empty.'
            Write-Host ''
            continue
        }

        $toDelete = if ($KeepNewest -eq 0) { $runs } else { $runs | Select-Object -Skip $KeepNewest }

        if ($toDelete.Count -eq 0) {
            Write-Host "  Nothing to delete (only $($runs.Count) archive(s), keeping $KeepNewest)."
        } else {
            foreach ($run in $toDelete) {
                Remove-ReportDir $run.FullName
                $deletedCount++
            }
        }

        $kept = if ($KeepNewest -eq 0) { 0 } else { [Math]::Min($KeepNewest, $runs.Count) }
        Write-Host "  Kept: $kept    Deleted: $($toDelete.Count)"
        $keptCount += $kept
        Write-Host ''
    }
}

# ---------------------------------------------------------------------------
# Summary.
# ---------------------------------------------------------------------------

Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Cleanup summary' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host "  Deleted: $deletedCount" -ForegroundColor $(if ($deletedCount -gt 0) { 'Red' } else { 'Gray' })
if ($keptCount -gt 0) {
    Write-Host "  Kept:   $keptCount" -ForegroundColor Green
}
if ($isDryRun) {
    Write-Host '  (dry run -- nothing was actually deleted)' -ForegroundColor Yellow
}
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

exit 0
