param(
    [Parameter(Mandatory = $true)]
    [string]$SourceFile,
    [string]$Language = "python",
    [string]$OutputDir = ".codeql-db\ast"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "scripts\run_codeql_ast.ps1"

if (-not (Test-Path $scriptPath)) {
    throw "Expected AST helper at $scriptPath"
}

& $scriptPath @PSBoundParameters