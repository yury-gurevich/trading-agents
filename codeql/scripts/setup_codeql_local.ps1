param(
    [string]$CodeQLTag = "v2.25.6",
    [string[]]$Languages = @("python", "yaml", "actions"),
    [switch]$Rebuild,
    [switch]$SkipAnalyze
)

$ErrorActionPreference = "Stop"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Executable $($Arguments -join ' ')"
    }
}

function Ensure-CodeqlPackLock {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CodeqlExe,
        [Parameter(Mandatory = $true)]
        [string]$PackPath
    )

    $lockFile = Join-Path $PackPath "codeql-pack.lock.yml"
    if (Test-Path $lockFile) {
        return
    }

    Write-Host "Installing CodeQL pack dependencies: $PackPath"
    Push-Location $PackPath
    try {
        Invoke-NativeCommand -Executable $CodeqlExe -Arguments @("pack", "install")
    }
    finally {
        Pop-Location
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$analysisPlans = @(
    [PSCustomObject]@{
        Language = "python"
        Pack = "codeql/python-queries"
        Queries = "codeql/python-queries:codeql-suites/python-security-and-quality.qls"
        LocalPackPath = $null
        SkipAnalysisReason = $null
        SarifName = "python-security-and-quality.sarif"
    },
    [PSCustomObject]@{
        Language = "yaml"
        Pack = $null
        Queries = $null
        LocalPackPath = Join-Path $repoRoot "codeql\yaml-diagnostics"
        SkipAnalysisReason = "CodeQL 2.25.6 can create and resolve the YAML subdatabase, but local query execution fails because the finalized dataset is missing yaml.dbscheme.stats."
        SarifName = "yaml-code-scanning.sarif"
    },
    [PSCustomObject]@{
        Language = "actions"
        Pack = "codeql/actions-queries"
        Queries = "codeql/actions-queries"
        LocalPackPath = $null
        SkipAnalysisReason = $null
        SarifName = "actions-code-scanning.sarif"
    }
)

$requestedLanguages = [System.Collections.Generic.List[string]]::new()
foreach ($language in $Languages) {
    if ([string]::IsNullOrWhiteSpace($language)) {
        continue
    }

    $normalizedLanguage = $language.Trim().ToLowerInvariant()
    if (-not $requestedLanguages.Contains($normalizedLanguage)) {
        [void]$requestedLanguages.Add($normalizedLanguage)
    }
}

if ($requestedLanguages.Count -eq 0) {
    throw "At least one CodeQL language must be specified."
}

$requestedPlans = [System.Collections.Generic.List[object]]::new()
foreach ($requestedLanguage in $requestedLanguages) {
    $plan = $analysisPlans | Where-Object { $_.Language -eq $requestedLanguage } | Select-Object -First 1
    if (-not $plan) {
        $supportedLanguages = ($analysisPlans | Select-Object -ExpandProperty Language) -join ", "
        throw "Unsupported CodeQL language '$requestedLanguage'. Supported languages: $supportedLanguages"
    }

    [void]$requestedPlans.Add($plan)
}

$toolsDir = Join-Path $repoRoot ".tools"
$zipPath = Join-Path $toolsDir "codeql-win64.zip"
$codeqlDir = Join-Path $toolsDir "codeql"
$codeqlExe = Join-Path $codeqlDir "codeql.exe"
$dbRoot = Join-Path $repoRoot ".codeql-db"
$dbPath = Join-Path $dbRoot "all-languages"
$languageArg = ($requestedPlans | Select-Object -ExpandProperty Language) -join ","
$sarifPaths = @($requestedPlans | ForEach-Object { Join-Path $dbRoot $_.SarifName })

Write-Host "Repo root: $repoRoot"
Write-Host "Requested languages: $languageArg"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required but not installed or not on PATH."
}

if ($Rebuild -and (Test-Path $dbPath)) {
    Write-Host "Rebuild requested: removing existing database $dbPath"
    Remove-Item -Recurse -Force $dbPath
}

if ($Rebuild) {
    foreach ($sarifPath in $sarifPaths) {
        if (Test-Path $sarifPath) {
            Remove-Item -Force $sarifPath
        }
    }
}

if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
}

if (-not (Test-Path $codeqlExe)) {
    Write-Host "Downloading CodeQL CLI $CodeQLTag..."
    Invoke-NativeCommand -Executable "gh" -Arguments @("release", "download", $CodeQLTag, "-R", "github/codeql-cli-binaries", "-p", "codeql-win64.zip", "-D", $toolsDir)
    Write-Host "Extracting CodeQL CLI..."
    Expand-Archive -LiteralPath $zipPath -DestinationPath $toolsDir -Force
}

if (-not (Test-Path $codeqlExe)) {
    throw "CodeQL executable was not found at $codeqlExe after extraction."
}

Write-Host "Using CodeQL executable: $codeqlExe"
Invoke-NativeCommand -Executable $codeqlExe -Arguments @("version")

if (-not (Test-Path $dbRoot)) {
    New-Item -ItemType Directory -Force -Path $dbRoot | Out-Null
}

if (-not (Test-Path $dbPath)) {
    Write-Host "Creating CodeQL database at $dbPath"
    Invoke-NativeCommand -Executable $codeqlExe -Arguments @("database", "create", $dbPath, "--db-cluster", "--language=$languageArg", "--source-root=$repoRoot", "--threads=0", "--overwrite")
} else {
    $missingDatabases = @(
        $requestedPlans |
            Where-Object { -not (Test-Path (Join-Path $dbPath $_.Language)) } |
            Select-Object -ExpandProperty Language
    )

    if ($missingDatabases.Count -gt 0) {
        throw "Database cluster $dbPath is missing languages: $($missingDatabases -join ', '). Re-run with -Rebuild."
    }

    Write-Host "Database cluster already exists: $dbPath"
}

foreach ($pack in ($requestedPlans | Select-Object -ExpandProperty Pack -Unique)) {
    if (-not $pack) {
        continue
    }

    Write-Host "Ensuring query pack is available: $pack"
    Invoke-NativeCommand -Executable $codeqlExe -Arguments @("pack", "download", $pack)
}

foreach ($localPackPath in ($requestedPlans | Where-Object { $_.Queries -and $_.LocalPackPath } | Select-Object -ExpandProperty LocalPackPath -Unique)) {
    if (-not $localPackPath) {
        continue
    }

    Ensure-CodeqlPackLock -CodeqlExe $codeqlExe -PackPath $localPackPath
}

if (-not $SkipAnalyze) {
    foreach ($plan in $requestedPlans) {
        if (-not $plan.Queries) {
            Write-Host "Skipping $($plan.Language) analysis: $($plan.SkipAnalysisReason)"
            continue
        }

        $languageDbPath = Join-Path $dbPath $plan.Language
        $sarifPath = Join-Path $dbRoot $plan.SarifName

        Write-Host "Running $($plan.Language) analysis..."
        Invoke-NativeCommand -Executable $codeqlExe -Arguments @("database", "analyze", $languageDbPath, $plan.Queries, "--format=sarifv2.1.0", "--output=$sarifPath", "--download", "--threads=0", "--sarif-category=$($plan.Language)")

        if (-not (Test-Path $sarifPath)) {
            throw "SARIF output was not created: $sarifPath"
        }

        $sarif = Get-Item $sarifPath
        Write-Host "$($plan.Language) SARIF ready: $($sarif.FullName)"
        Write-Host "$($plan.Language) SARIF size: $($sarif.Length) bytes"
    }
} else {
    Write-Host "SkipAnalyze set: database created, analysis skipped."
}

Write-Host "Done."
Write-Host "Database cluster: $dbPath"
if (-not $SkipAnalyze) {
    foreach ($plan in $requestedPlans) {
        if ($plan.Queries) {
            Write-Host "SARIF ($($plan.Language)): $(Join-Path $dbRoot $plan.SarifName)"
        } else {
            Write-Host "Analysis skipped ($($plan.Language)): $($plan.SkipAnalysisReason)"
        }
    }
}
Write-Host "To re-run from repo root:"
Write-Host "  powershell -ExecutionPolicy Bypass -File codeql/scripts/setup_codeql_local.ps1 -Rebuild"
