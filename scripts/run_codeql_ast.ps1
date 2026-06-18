param(
    [Parameter(Mandatory = $true)]
    [string]$SourceFile,
    [string]$Language = "python",
    [string]$OutputDir = ".codeql-db\ast"
)

$ErrorActionPreference = "Stop"

function Convert-ToCodeqlSourceArchivePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AbsolutePath
    )

    $encoded = $AbsolutePath.Replace("\", "/").Replace(":", "_")
    while ($encoded.Contains("//")) {
        $encoded = $encoded.Replace("//", "/")
    }

    return "/" + $encoded.TrimStart("/")
}

function Get-AncestorDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [int]$Levels
    )

    $current = Get-Item $Path
    for ($level = 0; $level -lt $Levels; $level++) {
        if (-not $current.Parent) {
            throw "Cannot walk $Levels levels above $Path."
        }
        $current = $current.Parent
    }

    return $current.FullName
}

function Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BasePath,
        [Parameter(Mandatory = $true)]
        [string]$TargetPath
    )

    $resolvedBase = (Resolve-Path $BasePath).Path.TrimEnd("\\")
    $resolvedTarget = (Resolve-Path $TargetPath).Path

    if (-not $resolvedTarget.StartsWith($resolvedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Target path must be inside base path.`nBase: $resolvedBase`nTarget: $resolvedTarget"
    }

    return $resolvedTarget.Substring($resolvedBase.Length).TrimStart("\\")
}

function Get-CodeqlDatabasePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,
        [Parameter(Mandatory = $true)]
        [string]$Language
    )

    $candidatePaths = @(
        (Join-Path $RepoRoot ".codeql-db\all-languages\$Language"),
        (Join-Path $RepoRoot ".codeql-db\$Language")
    )

    foreach ($candidatePath in $candidatePaths) {
        if (Test-Path $candidatePath) {
            return $candidatePath
        }
    }

    throw "CodeQL database was not found for language '$Language'. Checked: $($candidatePaths -join '; '). Run scripts/setup_codeql_local.ps1 first."
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$codeqlExe = Join-Path $repoRoot ".tools\codeql\codeql.exe"
$dbPath = Get-CodeqlDatabasePath -RepoRoot $repoRoot -Language $Language
$outputRoot = Join-Path $repoRoot $OutputDir

if (-not (Test-Path $codeqlExe)) {
    throw "CodeQL executable was not found at $codeqlExe. Run scripts/setup_codeql_local.ps1 first."
}

$sourceFilePath = (Resolve-Path $SourceFile).Path
if (-not $sourceFilePath.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Source file must be inside the repository root: $repoRoot"
}

Write-Host "Repo root: $repoRoot"
Write-Host "Source file: $sourceFilePath"
Write-Host "Database: $dbPath"

Write-Host "Ensuring Python query pack is available..."
& $codeqlExe pack download codeql/python-queries | Out-Null

$packageCache = Join-Path $HOME ".codeql\packages\codeql\python-queries"
$printAstFile = Get-ChildItem -Path $packageCache -Filter "printAst.ql" -Recurse |
    Where-Object { $_.FullName -like "*\codeql\python-all\*\printAst.ql" } |
    Sort-Object FullName -Descending |
    Select-Object -First 1

if (-not $printAstFile) {
    throw "Could not locate printAst.ql under $packageCache after downloading codeql/python-queries."
}

$pythonAllPackDir = $printAstFile.Directory.FullName
$pythonQueriesPackRoot = Get-AncestorDirectory -Path $pythonAllPackDir -Levels 5
$pythonAllLockFile = Join-Path $pythonAllPackDir "codeql-pack.lock.yml"
$queryPath = Get-RelativePath -BasePath $pythonQueriesPackRoot -TargetPath $printAstFile.FullName

if (-not (Test-Path $pythonAllLockFile)) {
    Write-Host "Installing missing python-all pack lock file..."
    Push-Location $pythonAllPackDir
    try {
        & $codeqlExe pack install
    }
    finally {
        Pop-Location
    }
}

$relativeSourceFile = Get-RelativePath -BasePath $repoRoot -TargetPath $sourceFilePath
$safeName = ($relativeSourceFile -replace "[\\/: ]", "__")
$artifactDir = Join-Path $outputRoot $safeName
$selectorPath = Join-Path $artifactDir "selectedSourceFile.csv"
$bqrsPath = Join-Path $artifactDir "printAst.bqrs"
$nodesPath = Join-Path $artifactDir "nodes.csv"
$edgesPath = Join-Path $artifactDir "edges.csv"
$graphPropertiesPath = Join-Path $artifactDir "graphProperties.csv"

New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

$sourceArchivePath = Convert-ToCodeqlSourceArchivePath -AbsolutePath $sourceFilePath
Set-Content -Path $selectorPath -Value $sourceArchivePath -NoNewline

Write-Host "Using source-archive selector: $sourceArchivePath"
Write-Host "Running printAst.ql from $pythonQueriesPackRoot"

Push-Location $pythonQueriesPackRoot
try {
    & $codeqlExe query run --database=$dbPath --output=$bqrsPath --external=selectedSourceFile=$selectorPath $queryPath
}
finally {
    Pop-Location
}

if (-not (Test-Path $bqrsPath)) {
    throw "CodeQL did not create the AST BQRS output at $bqrsPath"
}

& $codeqlExe bqrs decode --result-set=nodes --format=csv --output=$nodesPath $bqrsPath
& $codeqlExe bqrs decode --result-set=edges --format=csv --output=$edgesPath $bqrsPath
& $codeqlExe bqrs decode --result-set=graphProperties --format=csv --output=$graphPropertiesPath $bqrsPath

$infoText = (& $codeqlExe bqrs info $bqrsPath | Out-String)
$nodeMatch = [regex]::Match($infoText, "nodes has (\d+) rows")
$edgeMatch = [regex]::Match($infoText, "edges has (\d+) rows")

if (-not $nodeMatch.Success -or -not $edgeMatch.Success) {
    throw "Could not parse node/edge counts from CodeQL output:`n$infoText"
}

$nodeCount = [int]$nodeMatch.Groups[1].Value
$edgeCount = [int]$edgeMatch.Groups[1].Value

if ($nodeCount -eq 0 -or $edgeCount -eq 0) {
    throw "AST query completed but returned an empty graph. Check that the file belongs to the selected database and source archive."
}

Write-Host "AST graph ready."
Write-Host "  nodes: $nodeCount"
Write-Host "  edges: $edgeCount"
Write-Host "  BQRS: $bqrsPath"
Write-Host "  Nodes CSV: $nodesPath"
Write-Host "  Edges CSV: $edgesPath"
Write-Host "  Graph properties CSV: $graphPropertiesPath"