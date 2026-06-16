#!/usr/bin/env pwsh
# Smoke-test every external API key defined in .env
# Usage:  pwsh scripts/test-api-keys.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

# ── Load .env ─────────────────────────────────────────────────────────────────
$envPath = Join-Path $PSScriptRoot '..' '.env'
if (Test-Path $envPath) {
    foreach ($line in Get-Content $envPath) {
        if ($line -match '^\s*([^#=][^=]*)=(.*)$') {
            $val = $Matches[2].Trim() -replace '\s+#.*$', ''
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $val)
        }
    }
} else {
    Write-Host '.env not found — run from repo root' -ForegroundColor Red
    exit 1
}

# ── Helper ────────────────────────────────────────────────────────────────────
function Test-Endpoint {
    param(
        [string]   $Label,
        [string]   $Url,
        [hashtable]$Headers = @{},
        [string]   $Method  = 'GET'
    )
    try {
        $r    = Invoke-WebRequest -Uri $Url -Method $Method -Headers $Headers `
                    -TimeoutSec 10 -UseBasicParsing
        Write-Host ("  OK  {0,-36} HTTP {1}" -f $Label, $r.StatusCode) -ForegroundColor Green
    } catch {
        $code  = $_.Exception.Response.StatusCode.value__
        $msg   = if ($code) { "HTTP $code" } else { $_.Exception.Message -replace "`n", ' ' }
        $color = if ($code -in 401, 403) { 'Red' } else { 'Yellow' }
        Write-Host ("  --  {0,-36} {1}" -f $Label, $msg) -ForegroundColor $color
    }
}

Write-Host ("`nAPI key smoke tests  {0}`n" -f (Get-Date -Format 'yyyy-MM-dd HH:mm')) -ForegroundColor Cyan

# ── LLM ───────────────────────────────────────────────────────────────────────
Test-Endpoint 'Anthropic — list models' `
    'https://api.anthropic.com/v1/models' `
    @{ 'x-api-key' = $env:ANTHROPIC_API_KEY; 'anthropic-version' = '2023-06-01' }

Test-Endpoint 'OpenAI — list models' `
    'https://api.openai.com/v1/models' `
    @{ 'Authorization' = "Bearer $env:OPENAI_API_KEY" }

# ── Market data ───────────────────────────────────────────────────────────────
Test-Endpoint 'Finnhub — AAPL quote' `
    "https://finnhub.io/api/v1/quote?symbol=AAPL&token=$env:PROVIDER_FINNHUB_API_KEY"

Test-Endpoint 'FRED — GDP series' `
    "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=$env:PROVIDER_FRED_API_KEY&file_type=json"

Test-Endpoint 'FMP — AAPL symbol search' `
    "https://financialmodelingprep.com/stable/search-symbol?query=AAPL&apikey=$env:FNP_API_KEY"

Test-Endpoint 'Tiingo — API test' `
    'https://api.tiingo.com/api/test' `
    @{ 'Authorization' = "Token $env:TIINGO_API_KEY" }

# https://console.massiveapi.com — verify base URL if endpoint changes
Test-Endpoint 'Massive — account' `
    'https://api.massiveapi.com/v1/account' `
    @{ 'Authorization' = "Bearer $env:MASSIVE_API_KEY" }

# ── ML / training ─────────────────────────────────────────────────────────────
Test-Endpoint 'HuggingFace — whoami' `
    'https://huggingface.co/api/whoami-v2' `
    @{ 'Authorization' = "Bearer $env:HF_TOKEN" }

# ── Neo4j Aura ────────────────────────────────────────────────────────────────
$neo4jHost = $env:NEO4J_URI -replace '^neo4j\+s?://', ''
$neo4jCred = [Convert]::ToBase64String(
    [Text.Encoding]::ASCII.GetBytes("$($env:NEO4J_USER):$($env:NEO4J_PASSWORD)")
)
Test-Endpoint 'Neo4j Aura — discovery' `
    "https://$neo4jHost" `
    @{ 'Authorization' = "Basic $neo4jCred" }

# ── PostgreSQL — no HTTP endpoint, just validate string is present ────────────
if ($env:DATABASE_URL) {
    Write-Host ("  OK  {0,-36} connection string present" -f 'PostgreSQL') -ForegroundColor Green
} else {
    Write-Host ("  --  {0,-36} DATABASE_URL not set" -f 'PostgreSQL') -ForegroundColor Yellow
}

# ── Azure observability ───────────────────────────────────────────────────────
# The ingestion endpoint requires a bearer token via client-credentials flow;
# a 200 on the base URL confirms network reachability.
Test-Endpoint 'Azure ingestion endpoint' `
    $env:AZURE_LOGS_INGESTION_ENDPOINT

# ── Alpaca (broker) ───────────────────────────────────────────────────────────
$alpacaEndpoint = if ($env:ALPACA_ENDPOINT) { $env:ALPACA_ENDPOINT } else { 'https://paper-api.alpaca.markets/v2' }
Test-Endpoint 'Alpaca — account' `
    "$alpacaEndpoint/account" `
    @{ 'APCA-API-KEY-ID' = $env:ALPACA_API_KEY; 'APCA-API-SECRET-KEY' = $env:ALPACA_API_SECRET }

Write-Host ''
