param(
    [string[]]$SarifPath,
    [string]$OutputDir,
    [string]$BaselinePath,
    [switch]$UpdateBaseline
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$defaultSarifPaths = @(
    (Join-Path $repoRoot ".codeql-db\python-security-and-quality.sarif"),
    (Join-Path $repoRoot ".codeql-db\yaml-code-scanning.sarif"),
    (Join-Path $repoRoot ".codeql-db\actions-code-scanning.sarif")
)

if (-not $SarifPath -or $SarifPath.Count -eq 0) {
    $SarifPath = @($defaultSarifPaths | Where-Object { Test-Path $_ })
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot ".codeql-db\reports"
}
if (-not $BaselinePath) {
    $BaselinePath = Join-Path $OutputDir "baseline-findings.json"
}

if (-not $SarifPath -or $SarifPath.Count -eq 0) {
    throw "No SARIF files were found. Expected one or more of: $($defaultSarifPaths -join ', ')"
}

$resolvedSarifPaths = @()
foreach ($path in $SarifPath) {
    if (-not (Test-Path $path)) {
        throw "SARIF file not found: $path"
    }

    $resolvedSarifPaths += (Resolve-Path $path).Path
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$rulesById = @{}
$resultEntries = @()

function Get-RunLanguage {
    param(
        [Parameter(Mandatory = $true)]
        $Run,
        [Parameter(Mandatory = $true)]
        [string]$SourceSarifPath
    )

    if ($Run.automationDetails -and $Run.automationDetails.id) {
        return ([string]$Run.automationDetails.id).TrimEnd('/')
    }

    $sarifName = [System.IO.Path]::GetFileNameWithoutExtension($SourceSarifPath)
    if ($sarifName -match '^(python|yaml|actions)') {
        return $Matches[1]
    }

    return "unknown"
}

function Get-PathClass([string]$path) {
    if ($path -like ".tools/*") { return "tooling" }
    if ($path -like "tests/*" -or $path -like "*/tests/*") { return "tests" }
    return "production"
}

function Get-SeverityBucket($result) {
    $sec = $null
    if ($result.properties -and $result.properties.'security-severity') {
        $sec = [double]$result.properties.'security-severity'
    }
    if ($null -ne $sec) {
        if ($sec -ge 9.0) { return "critical" }
        if ($sec -ge 7.0) { return "high" }
        if ($sec -ge 4.0) { return "medium" }
        return "low"
    }
    if ($result.level) { return [string]$result.level }
    return "unknown"
}

function Get-FindingRecord($result) {
    $loc = $null
    if ($result.locations -and $result.locations.Count -gt 0) {
        $loc = $result.locations[0].physicalLocation
    }

    $path = if ($loc -and $loc.artifactLocation -and $loc.artifactLocation.uri) {
        [string]$loc.artifactLocation.uri
    } else {
        "(no location)"
    }
    $line = if ($loc -and $loc.region -and $loc.region.startLine) { [int]$loc.region.startLine } else { 1 }
    $msg = if ($result.message -and $result.message.text) { [string]$result.message.text } else { "" }
    $ruleId = [string]$result.ruleId
    $short = if ($rulesById.ContainsKey($ruleId) -and $rulesById[$ruleId].shortDescription -and $rulesById[$ruleId].shortDescription.text) {
        [string]$rulesById[$ruleId].shortDescription.text
    } else {
        $ruleId
    }

    $language = if ($result.PSObject.Properties.Match("_language").Count -gt 0) {
        [string]$result._language
    } else {
        "unknown"
    }

    $sourceSarif = if ($result.PSObject.Properties.Match("_source_sarif").Count -gt 0) {
        [string]$result._source_sarif
    } else {
        "unknown"
    }

    [PSCustomObject]@{
        key = ("{0}|{1}|{2}|{3}|{4}" -f $language, $ruleId, $path, $line, $msg)
        rule_id = $ruleId
        rule_name = $short
        language = $language
        source_sarif = $sourceSarif
        path = $path
        line = $line
        message = ($msg -replace "`r|`n", " ")
        class = Get-PathClass $path
        severity = Get-SeverityBucket $result
    }
}

foreach ($resolvedSarifPath in $resolvedSarifPaths) {
    $sarif = Get-Content $resolvedSarifPath -Raw | ConvertFrom-Json
    if (-not $sarif.runs -or $sarif.runs.Count -eq 0) {
        throw "No runs found in SARIF: $resolvedSarifPath"
    }

    foreach ($run in @($sarif.runs)) {
        foreach ($rule in @($run.tool.driver.rules)) {
            if (-not $rulesById.ContainsKey($rule.id)) {
                $rulesById[$rule.id] = $rule
            }
        }

        $runLanguage = Get-RunLanguage -Run $run -SourceSarifPath $resolvedSarifPath
        foreach ($result in @($run.results)) {
            $result | Add-Member -NotePropertyName _language -NotePropertyValue $runLanguage -Force
            $result | Add-Member -NotePropertyName _source_sarif -NotePropertyValue ([System.IO.Path]::GetFileName($resolvedSarifPath)) -Force
            $resultEntries += $result
        }
    }
}

$findings = @($resultEntries | ForEach-Object { Get-FindingRecord $_ })
$now = Get-Date -Format "yyyy-MM-dd HH:mm"

$totalAll = $findings.Count
$totalNoTools = (@($findings | Where-Object { $_.class -ne "tooling" })).Count
$totalProdOnly = (@($findings | Where-Object { $_.class -eq "production" })).Count

$severityCounts = @($findings | Group-Object severity | Sort-Object Count -Descending)
$languageCounts = @($findings | Group-Object language | Sort-Object Count -Descending)
$topRulesNoTools = @($findings | Where-Object { $_.class -ne "tooling" } | Group-Object rule_id | Sort-Object Count -Descending | Select-Object -First 12)
$topProdFindings = @($findings | Where-Object { $_.class -eq "production" } | Select-Object -First 20)

$currentReportPath = Join-Path $OutputDir "codeql-current-report.md"
$ownerReportPath = Join-Path $OutputDir "codeql-owner-report.md"
$diffReportPath = Join-Path $OutputDir "codeql-diff-report.md"
$snapshotPath = Join-Path $OutputDir "codeql-snapshot.json"

$currentLines = @()
$currentLines += "# CodeQL Local Scan Triage Report"
$currentLines += ""
$currentLines += "Generated: $now"
$currentLines += "Source SARIF count: $($resolvedSarifPaths.Count)"
$currentLines += "Source SARIFs:"
foreach ($resolvedSarifPath in $resolvedSarifPaths) {
    $currentLines += "- $resolvedSarifPath"
}
$currentLines += ""
$currentLines += "## Executive Summary"
$currentLines += "1. Total findings in SARIF: $totalAll"
$currentLines += "2. Findings excluding tooling paths: $totalNoTools"
$currentLines += "3. Findings in production paths only: $totalProdOnly"
$currentLines += "4. Languages represented in findings: $($languageCounts.Count)"
$currentLines += ""
$currentLines += "## Language Distribution"
foreach ($bucket in $languageCounts) {
    $currentLines += "- $($bucket.Name): $($bucket.Count)"
}
$currentLines += ""
$currentLines += "## Severity Distribution"
foreach ($bucket in $severityCounts) {
    $currentLines += "- $($bucket.Name): $($bucket.Count)"
}
$currentLines += ""
$currentLines += "## Top Rules (Excluding Tooling Paths)"
foreach ($entry in $topRulesNoTools) {
    $rid = [string]$entry.Name
    $ruleName = if ($rulesById.ContainsKey($rid) -and $rulesById[$rid].shortDescription -and $rulesById[$rid].shortDescription.text) {
        [string]$rulesById[$rid].shortDescription.text
    } else {
        $rid
    }
    $currentLines += "- $($entry.Count): $rid - $ruleName"
}
$currentLines += ""
$currentLines += "## Top Production Findings (First 20)"
$i = 1
foreach ($f in $topProdFindings) {
    $currentLines += "- $i. [$($f.language)] $($f.rule_id) | $($f.path):$($f.line) | $($f.message)"
    $i++
}

Set-Content -Path $currentReportPath -Value ($currentLines -join "`n") -Encoding UTF8

$ownerGroups = @($findings | Where-Object { $_.class -eq "production" } | Group-Object { ($_.path -split '/')[0] } | Sort-Object Count -Descending)
$ownerLines = @()
$ownerLines += "# CodeQL Owner Grouping Report"
$ownerLines += ""
$ownerLines += "Generated: $now"
$ownerLines += ""
$ownerLines += "## Findings by Top-Level Folder"
foreach ($group in $ownerGroups) {
    $ownerLines += "- $($group.Name): $($group.Count)"
}
$ownerLines += ""
$ownerLines += "## Top Rules per Folder"
foreach ($group in $ownerGroups) {
    $ownerLines += ""
    $ownerLines += "### $($group.Name)"
    $topByFolder = @($group.Group | Group-Object rule_id | Sort-Object Count -Descending | Select-Object -First 5)
    foreach ($t in $topByFolder) {
        $ownerLines += "- $($t.Count): $($t.Name)"
    }
}
Set-Content -Path $ownerReportPath -Value ($ownerLines -join "`n") -Encoding UTF8

$oldBaseline = @()
if (Test-Path $BaselinePath) {
    $oldBaseline = @(Get-Content $BaselinePath -Raw | ConvertFrom-Json)
}

$oldKeys = [System.Collections.Generic.HashSet[string]]::new()
foreach ($item in $oldBaseline) { [void]$oldKeys.Add([string]$item.key) }
$newKeys = [System.Collections.Generic.HashSet[string]]::new()
foreach ($item in $findings) { [void]$newKeys.Add([string]$item.key) }

$added = @($findings | Where-Object { -not $oldKeys.Contains($_.key) })
$resolved = @($oldBaseline | Where-Object { -not $newKeys.Contains([string]$_.key) })
$unchanged = $totalAll - $added.Count

$diffLines = @()
$diffLines += "# CodeQL Baseline Diff Report"
$diffLines += ""
$diffLines += "Generated: $now"
$diffLines += "Baseline file: $BaselinePath"
$diffLines += ""
$diffLines += "## Delta Summary"
$diffLines += "1. Current findings: $totalAll"
$diffLines += "2. Added since baseline: $($added.Count)"
$diffLines += "3. Resolved since baseline: $($resolved.Count)"
$diffLines += "4. Unchanged: $unchanged"
$diffLines += ""
$diffLines += "## Added Findings (First 20)"
$i = 1
foreach ($a in ($added | Select-Object -First 20)) {
    $diffLines += "- $i. [$($a.language)] $($a.rule_id) | $($a.path):$($a.line)"
    $i++
}
$diffLines += ""
$diffLines += "## Resolved Findings (First 20)"
$i = 1
foreach ($r in ($resolved | Select-Object -First 20)) {
    $diffLines += "- $i. [$($r.language)] $($r.rule_id) | $($r.path):$($r.line)"
    $i++
}
Set-Content -Path $diffReportPath -Value ($diffLines -join "`n") -Encoding UTF8

$findings | ConvertTo-Json -Depth 6 | Set-Content -Path $snapshotPath -Encoding UTF8
if ($UpdateBaseline -or -not (Test-Path $BaselinePath)) {
    Copy-Item -Path $snapshotPath -Destination $BaselinePath -Force
}

Write-Host "Reports generated:"
Write-Host "- $currentReportPath"
Write-Host "- $ownerReportPath"
Write-Host "- $diffReportPath"
Write-Host "Snapshot: $snapshotPath"
Write-Host "Baseline: $BaselinePath"
