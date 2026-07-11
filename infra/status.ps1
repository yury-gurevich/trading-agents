# status.ps1 — One-command status board for the trading-agents fleet.
#
#   pwsh infra/status.ps1              # single snapshot (fast: 4 remote calls)
#   pwsh infra/status.ps1 -Watch       # refresh every 15s (Ctrl-C to stop)
#   pwsh infra/status.ps1 -Replicas    # also count live replicas (one az call per app)
#
# Verdict first: one GREEN/RED line, reasons under it, detail below.
# Read-only — never changes Azure state or your az subscription context.

param(
  [switch]$Watch,
  [switch]$Replicas,
  [ValidateRange(5, 3600)]
  [int]$IntervalSeconds = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'
$RG = "trading-agents"
$SUB = "5ef50a27-50a4-4d90-9695-da61b2309cf3"
$JobName = "dispatcher-cron"

function Get-Json([string[]]$Cmd) {
  $raw = & $Cmd[0] @($Cmd[1..($Cmd.Count - 1)]) 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
  try { return $raw | ConvertFrom-Json } catch { return $null }
}

function Get-NextFire([string]$Cron) {
  # Supports the simple "M H * * *" daily shape the dispatcher uses; else no ETA.
  $parts = ($Cron ?? '') -split '\s+'
  if ($parts.Count -lt 2 -or $parts[0] -notmatch '^\d+$' -or $parts[1] -notmatch '^\d+$') { return $null }
  $now = [DateTime]::UtcNow
  $next = [DateTime]::new($now.Year, $now.Month, $now.Day, [int]$parts[1], [int]$parts[0], 0, [System.DateTimeKind]::Utc)
  if ($next -le $now) { $next = $next.AddDays(1) }
  return $next
}

function Show-Board {
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

  # ── Gather (before clearing the screen, so -Watch never shows a blank board) ──
  $build = Get-Json @('gh', 'run', 'list', '--workflow', 'build-images.yml', '--limit', '1',
    '--json', 'status,conclusion,event,headBranch,createdAt')
  $apps = Get-Json @('az', 'containerapp', 'list', '-g', $RG, '--subscription', $SUB, '--query',
    '[].{name:name, state:properties.provisioningState, image:properties.template.containers[0].image}',
    '-o', 'json')
  $jobInfo = Get-Json @('az', 'containerapp', 'job', 'show', '-n', $JobName, '-g', $RG, '--subscription', $SUB,
    '--query', '{image:properties.template.containers[0].image, cron:properties.configuration.scheduleTriggerConfig.cronExpression}',
    '-o', 'json')
  $execs = Get-Json @('az', 'containerapp', 'job', 'execution', 'list', '-n', $JobName, '-g', $RG,
    '--subscription', $SUB, '--query',
    'reverse(sort_by([].{name:name, status:properties.status, start:properties.startTime}, &start)) | [:3]',
    '-o', 'json')
  if ($null -ne $execs -and $execs -isnot [array]) { $execs = @($execs) }

  $tag = { param($img) if ($img -match ':([^:]+)$') { $Matches[1] } else { '?' } }
  $tags = @(@($apps) + @($jobInfo) | Where-Object { $_ } | ForEach-Object { & $tag $_.image } | Sort-Object -Unique)
  $lastExec = if ($execs) { $execs[0] } else { $null }

  # ── Verdict ──────────────────────────────────────────────────────────────────
  $problems = [System.Collections.Generic.List[string]]::new()
  if ($null -eq $apps) { $problems.Add("Azure unreachable — az login / network") }
  elseif ($apps.Count -eq 0) { $problems.Add("no Container Apps deployed in $RG") }
  else {
    $bad = @($apps | Where-Object { $_.state -ne 'Succeeded' })
    foreach ($a in $bad) { $problems.Add("$($a.name) is $($a.state)") }
  }
  if ($null -eq $jobInfo) { $problems.Add("$JobName job missing — nothing schedules the nightly run") }
  if ($lastExec -and $lastExec.status -eq 'Failed') { $problems.Add("last $JobName execution failed") }
  if ($build -and $build.Count -ge 1 -and $build[0].conclusion -eq 'failure') { $problems.Add("latest image build failed") }
  $warnings = [System.Collections.Generic.List[string]]::new()
  if ($tags.Count -gt 1) { $warnings.Add("mixed image tags: $($tags -join ', ')") }

  try { if ($Watch) { Clear-Host } } catch { Write-Host "" }
  $light = if ($problems.Count) { 'RED' } else { 'GREEN' }
  $color = if ($problems.Count) { 'Red' } else { 'Green' }
  Write-Host ""
  Write-Host ("  ● {0}" -f $light) -ForegroundColor $color -NoNewline
  Write-Host ("   trading-agents fleet · {0}" -f $stamp) -ForegroundColor DarkGray
  foreach ($p in $problems) { Write-Host ("    ✗ {0}" -f $p) -ForegroundColor Red }
  foreach ($w in $warnings) { Write-Host ("    ⚠ {0}" -f $w) -ForegroundColor Yellow }

  # ── Nightly schedule ─────────────────────────────────────────────────────────
  Write-Host "`n  SCHEDULE" -ForegroundColor Yellow
  if ($jobInfo) {
    $next = Get-NextFire $jobInfo.cron
    $eta = if ($next) {
      $span = $next - [DateTime]::UtcNow
      ("next fire {0:HH:mm} local (in {1:d\d\ h\h\ m\m})" -f $next.ToLocalTime(), $span)
    } else { "cron '$($jobInfo.cron)'" }
    Write-Host ("    {0} · {1}" -f $JobName, $eta)
  } else { Write-Host "    (job unavailable)" -ForegroundColor DarkGray }
  foreach ($e in @($execs) | Where-Object { $_ }) {
    $c = switch ($e.status) { 'Succeeded' { 'Green' } 'Failed' { 'Red' } default { 'Yellow' } }
    Write-Host ("    {0,-11}" -f $e.status) -ForegroundColor $c -NoNewline
    Write-Host (" {0}" -f $e.start) -ForegroundColor DarkGray
  }

  # ── Build pipeline ───────────────────────────────────────────────────────────
  Write-Host "`n  BUILD (GitHub Actions)" -ForegroundColor Yellow
  if ($build -and $build.Count -ge 1) {
    $b = $build[0]
    $state = if ($b.status -ne 'completed') { $b.status } else { $b.conclusion }
    $c = switch ($state) { 'success' { 'Green' } 'failure' { 'Red' } default { 'Yellow' } }
    Write-Host ("    {0,-11}" -f $state) -ForegroundColor $c -NoNewline
    Write-Host (" {0} · {1} · {2}" -f $b.headBranch, $b.event, $b.createdAt) -ForegroundColor DarkGray
  } else { Write-Host "    (gh unavailable or no runs)" -ForegroundColor DarkGray }

  # ── Fleet ────────────────────────────────────────────────────────────────────
  $suffix = if ($Replicas) { '' } else { '   (run with -Replicas for live counts)' }
  Write-Host ("`n  CONTAINER APPS ({0} of expected 13){1}" -f @($apps).Count, $suffix) -ForegroundColor Yellow
  foreach ($a in @($apps) | Sort-Object name) {
    $c = if ($a.state -eq 'Succeeded') { 'Green' } else { 'Red' }
    Write-Host ("    {0,-19}" -f $a.name) -NoNewline
    Write-Host ("{0,-10}" -f $a.state) -ForegroundColor $c -NoNewline
    Write-Host (" :{0}" -f (& $tag $a.image)) -ForegroundColor DarkGray -NoNewline
    if ($Replicas) {
      $n = Get-Json @('az', 'containerapp', 'replica', 'list', '-n', $a.name, '-g', $RG,
        '--subscription', $SUB, '--query', 'length([])', '-o', 'json')
      Write-Host ("  replicas={0}" -f ($n ?? 0)) -ForegroundColor DarkGray -NoNewline
    }
    Write-Host ""
  }
  if ($jobInfo) { Write-Host ("    {0,-19}job        :{1}" -f $JobName, (& $tag $jobInfo.image)) -ForegroundColor DarkGray }
  Write-Host ""
  return $problems.Count
}

if ($Watch) {
  while ($true) { $null = Show-Board; Start-Sleep -Seconds $IntervalSeconds }
} else {
  # Exit code mirrors the verdict (0 = GREEN, 1 = RED) so the board is scriptable.
  exit ([int]((Show-Board) -gt 0))
}
