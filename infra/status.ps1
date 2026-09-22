# status.ps1 — One-command status board for the trading-agents fleet.
#
#   pwsh infra/status.ps1              # single snapshot (fast: 4 remote calls)
#   pwsh infra/status.ps1 -Watch       # refresh every 15s (Ctrl-C to stop)
#   pwsh infra/status.ps1 -Replicas    # also count live replicas (one az call per app)
#
# Verdict first: one GREEN/RED line, reasons under it, detail below.
# Read-only — never changes Azure state or your az subscription context.
#
# ── Times are Melbourne, not UTC ──────────────────────────────────────────────
# Azure, KEDA and cron are all UTC underneath. The operator is not. Every clock
# value on this board is converted once, through Convert-Display, so there is a
# single place to be wrong rather than one per call site. The AEST/AEDT label is
# derived from the actual offset at that instant, never hardcoded — Melbourne is
# +10 for part of the year and +11 for the rest, and a board that prints "AEST"
# in January is lying about an hour.
#
# ── Two columns were removed 2026-09-22, because they carried no information ──
# DEPLOY read `Succeeded` on all 17 rows; an app that is NOT Succeeded is already
# named in the verdict block above, which is where a problem belongs. IMAGE
# repeated one 40-character tag 17 times, and grew that wide the moment the fleet
# moved to commit-SHA tags. Sameness is the thing worth knowing, so it is now one
# line; the per-app breakout returns only when tags actually differ, which is the
# only case where a per-row value says anything.

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

# Windows and IANA spellings of the same zone; whichever the host knows.
$script:Tz = $null
foreach ($id in @('AUS Eastern Standard Time', 'Australia/Melbourne')) {
  try { $script:Tz = [TimeZoneInfo]::FindSystemTimeZoneById($id); break } catch { }
}

function Convert-Display([DateTime]$Moment) {
  # UTC instant -> Melbourne wall clock. Falls back to the host's local time only
  # if the zone database has neither spelling, which beats showing UTC.
  if ($Moment.Kind -eq [DateTimeKind]::Unspecified) {
    $Moment = [DateTime]::SpecifyKind($Moment, [DateTimeKind]::Utc)
  }
  if ($null -eq $script:Tz) { return $Moment.ToLocalTime() }
  return [TimeZoneInfo]::ConvertTimeFromUtc($Moment.ToUniversalTime(), $script:Tz)
}

function Get-TzLabel([DateTime]$Moment) {
  # Derived from the real offset, so it says AEDT through daylight saving.
  if ($null -eq $script:Tz) { return 'local' }
  if ($script:Tz.GetUtcOffset($Moment.ToUniversalTime()).TotalHours -ge 11) { return 'AEDT' }
  return 'AEST'
}

function Format-Clock([DateTime]$Moment) { (Get-Date $Moment -Format 'h:mm tt').ToLower() }
function Format-Day([DateTime]$Moment) { Get-Date $Moment -Format 'ddd d MMM' }

function Format-Span([TimeSpan]$Span) {
  # Floor, never [int]. PowerShell's [int] cast ROUNDS, so a 1h54m span became
  # "2h 54m" — the rounded-up hour printed beside the leftover minutes, an hour
  # wrong in roughly half of all values. Measured 2026-09-22 against a build
  # 1h54m old. A clock that is confidently wrong is worse than one showing UTC.
  if ($Span.TotalMinutes -lt 1) { return 'now' }
  if ($Span.TotalHours -lt 1) { return ("{0}m" -f [Math]::Floor($Span.TotalMinutes)) }
  if ($Span.TotalDays -lt 1) { return ("{0}h {1}m" -f [Math]::Floor($Span.TotalHours), $Span.Minutes) }
  return ("{0}d {1}h" -f [Math]::Floor($Span.TotalDays), $Span.Hours)
}

function Format-Ago([DateTime]$Moment) {
  $span = [DateTime]::UtcNow - $Moment.ToUniversalTime()
  if ($span.Ticks -lt 0) { return 'just now' }
  return ((Format-Span $span) + ' ago')
}

function Get-Json([string[]]$Cmd) {
  $raw = & $Cmd[0] @($Cmd[1..($Cmd.Count - 1)]) 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
  try { return $raw | ConvertFrom-Json } catch { return $null }
}

function Get-ReplicaCount([string]$App) {
  # Count in PowerShell, never with a JMESPath `length(...)`: az is a .cmd shim here, so
  # PowerShell strips the quotes and cmd chokes on the parentheses (exit 255). That failure
  # used to render as a flat `replicas=0` — a broken call looking exactly like a real zero.
  # Returns $null when the call fails, so the board can say "?" instead of lying.
  $raw = az containerapp replica list -n $App -g $RG --subscription $SUB -o json 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
  try { return @($raw | ConvertFrom-Json).Count } catch { return $null }
}

function Test-CronField([string]$Field, [int]$Value) {
  # One cron field against one value. Handles *, */N, A-B, A-B/N, A,B,C and literals —
  # everything the dispatcher's `*/10 22-23 * * 1-5` needs, and the wake windows' `M H * * *`.
  foreach ($part in ($Field -split ',')) {
    $spec = $part; $step = 1
    if ($part -match '^(.*)/(\d+)$') { $spec = $Matches[1]; $step = [int]$Matches[2] }
    if ($step -le 0) { continue }
    if ($spec -eq '*') { if (($Value % $step) -eq 0) { return $true }; continue }
    if ($spec -match '^(\d+)-(\d+)$') {
      $lo = [int]$Matches[1]; $hi = [int]$Matches[2]
      if ($Value -ge $lo -and $Value -le $hi -and ((($Value - $lo) % $step) -eq 0)) { return $true }
      continue
    }
    if ($spec -match '^\d+$' -and $Value -eq [int]$spec) { return $true }
  }
  return $false
}

function Get-NextFire([string]$Cron, [DateTime]$FromUtc) {
  # Walks forward a minute at a time for 8 days — enough for any weekly cron, and cheap
  # enough not to matter. The old version understood only "M H * * *", so the dispatcher's
  # real `*/10 22-23 * * 1-5` printed the raw cron string and no ETA: the single most
  # useful fact on the board was the one it could not compute.
  $p = @(($Cron ?? '') -split '\s+' | Where-Object { $_ })
  if ($p.Count -lt 5) { return $null }
  $t = $FromUtc.AddSeconds(-$FromUtc.Second).AddMilliseconds(-$FromUtc.Millisecond).AddMinutes(1)
  $domRestricted = $p[2] -ne '*'
  $dowRestricted = $p[4] -ne '*'
  for ($i = 0; $i -lt 11520; $i++) {
    if ((Test-CronField $p[0] $t.Minute) -and (Test-CronField $p[1] $t.Hour) -and
        (Test-CronField $p[3] $t.Month)) {
      $dow = [int]$t.DayOfWeek
      $domOk = Test-CronField $p[2] $t.Day
      $dowOk = (Test-CronField $p[4] $dow) -or ($dow -eq 0 -and (Test-CronField $p[4] 7))
      # cron ORs day-of-month against day-of-week when both are restricted, ANDs otherwise.
      $dayOk = $true
      if ($domRestricted -and $dowRestricted) { $dayOk = ($domOk -or $dowOk) }
      elseif ($domRestricted) { $dayOk = $domOk }
      elseif ($dowRestricted) { $dayOk = $dowOk }
      if ($dayOk) { return $t }
    }
    $t = $t.AddMinutes(1)
  }
  return $null
}

function Test-InWindow([string]$Start, [string]$End) {
  # KEDA cron window "M H * * *" -> is UTC now inside it? Wraps past midnight.
  $s = @(($Start ?? '') -split '\s+'); $e = @(($End ?? '') -split '\s+')
  if ($s.Count -lt 2 -or $e.Count -lt 2) { return $null }
  if ($s[0] -notmatch '^\d+$' -or $s[1] -notmatch '^\d+$') { return $null }
  if ($e[0] -notmatch '^\d+$' -or $e[1] -notmatch '^\d+$') { return $null }
  $now = [DateTime]::UtcNow; $mins = $now.Hour * 60 + $now.Minute
  $from = [int]$s[1] * 60 + [int]$s[0]; $to = [int]$e[1] * 60 + [int]$e[0]
  if ($from -le $to) { return ($mins -ge $from -and $mins -lt $to) }
  return ($mins -ge $from -or $mins -lt $to)   # window crosses midnight
}

function Format-WindowClock([string]$CronLike) {
  # "30 22 * * *" (UTC) -> "8:30 am" in Melbourne. Anchored on today's date so the
  # conversion uses the offset actually in force now, not a fixed +10.
  $p = @(($CronLike ?? '') -split '\s+')
  if ($p.Count -lt 2 -or $p[0] -notmatch '^\d+$' -or $p[1] -notmatch '^\d+$') { return $null }
  $n = [DateTime]::UtcNow
  $utc = [DateTime]::new($n.Year, $n.Month, $n.Day, [int]$p[1], [int]$p[0], 0, [DateTimeKind]::Utc)
  return (Format-Clock (Convert-Display $utc))
}

function Show-Board {
  $nowUtc = [DateTime]::UtcNow
  $nowLocal = Convert-Display $nowUtc
  $tz = Get-TzLabel $nowUtc

  # ── Gather (before clearing the screen, so -Watch never shows a blank board) ──
  $build = Get-Json @('gh', 'run', 'list', '--workflow', 'build-images.yml', '--limit', '1',
    '--json', 'status,conclusion,event,headBranch,createdAt')
  $apps = Get-Json @('az', 'containerapp', 'list', '-g', $RG, '--subscription', $SUB, '--query',
    '[].{name:name, state:properties.provisioningState, image:properties.template.containers[0].image, winStart:properties.template.scale.rules[0].custom.metadata.start, winEnd:properties.template.scale.rules[0].custom.metadata.end}',
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
  $short = { param($t) if ($t -match '^[0-9a-f]{40}$') { $t.Substring(0, 7) } else { $t } }
  $jobPresent = @(@($jobInfo) | Where-Object { $_ }).Count
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
  $mixed = $tags.Count -gt 1
  if ($mixed) { $warnings.Add("fleet is on more than one image — see the IMAGE column below") }

  try { if ($Watch) { Clear-Host } } catch { Write-Host "" }
  $light = if ($problems.Count) { 'RED' } else { 'GREEN' }
  $color = if ($problems.Count) { 'Red' } else { 'Green' }
  Write-Host ""
  Write-Host ("  ● {0}" -f $light) -ForegroundColor $color -NoNewline
  Write-Host "   trading-agents fleet" -ForegroundColor White -NoNewline
  Write-Host ("   ·   {0}, {1} {2}" -f (Format-Day $nowLocal), (Format-Clock $nowLocal), $tz) -ForegroundColor DarkGray
  foreach ($p in $problems) { Write-Host ("    ✗ {0}" -f $p) -ForegroundColor Red }
  foreach ($w in $warnings) { Write-Host ("    ⚠ {0}" -f $w) -ForegroundColor Yellow }

  # ── What is deployed ─────────────────────────────────────────────────────────
  # One line when every target agrees, which is the healthy case and the common one.
  Write-Host ""
  Write-Host "  IMAGE      " -ForegroundColor Yellow -NoNewline
  if ($tags.Count -eq 0) {
    Write-Host "(nothing deployed)" -ForegroundColor Red
  } elseif (-not $mixed) {
    Write-Host ("{0}" -f (& $short $tags[0])) -ForegroundColor Cyan -NoNewline
    Write-Host ("   all {0} targets on the same image" -f (@($apps).Count + $jobPresent)) -ForegroundColor DarkGray
  } else {
    Write-Host ("{0} different tags across the fleet" -f $tags.Count) -ForegroundColor Yellow
  }
  if ($build -and $build.Count -ge 1) {
    $b = $build[0]
    $state = if ($b.status -ne 'completed') { $b.status } else { $b.conclusion }
    $c = switch ($state) { 'success' { 'Green' } 'failure' { 'Red' } default { 'Yellow' } }
    Write-Host "  BUILD      " -ForegroundColor Yellow -NoNewline
    Write-Host ("{0}" -f $state) -ForegroundColor $c -NoNewline
    Write-Host ("   {0} · {1} · {2}" -f $b.headBranch, $b.event, (Format-Ago ([DateTime]$b.createdAt))) -ForegroundColor DarkGray
  }

  # ── Nightly schedule ─────────────────────────────────────────────────────────
  Write-Host ""
  if ($jobInfo) {
    $next = Get-NextFire $jobInfo.cron $nowUtc
    Write-Host "  NEXT RUN   " -ForegroundColor Yellow -NoNewline
    if ($next) {
      $nl = Convert-Display $next
      Write-Host ("{0}, {1} {2}" -f (Format-Day $nl), (Format-Clock $nl), (Get-TzLabel $next)) -ForegroundColor Cyan -NoNewline
      Write-Host ("   in {0}" -f (Format-Span ($next - $nowUtc))) -ForegroundColor DarkGray
    } else {
      Write-Host ("cron '{0}'" -f $jobInfo.cron) -ForegroundColor DarkGray
    }
  }
  $rows = @(@($execs) | Where-Object { $_ })
  if ($rows.Count) {
    Write-Host "  LAST RUNS  " -ForegroundColor Yellow -NoNewline
    foreach ($e in $rows) {
      $mark = switch ($e.status) { 'Succeeded' { '✓' } 'Failed' { '✗' } default { '·' } }
      $c = switch ($e.status) { 'Succeeded' { 'Green' } 'Failed' { 'Red' } default { 'Yellow' } }
      $el = Convert-Display ([DateTime]$e.start)
      Write-Host ("{0} " -f $mark) -ForegroundColor $c -NoNewline
      Write-Host ("{0} {1}   " -f (Format-Day $el), (Format-Clock $el)) -ForegroundColor DarkGray -NoNewline
    }
    Write-Host ""
  }

  # ── Fleet ────────────────────────────────────────────────────────────────────
  # 17 deploy targets, not 16: the dispatcher-cron job is retagged with the apps and is
  # just as able to be left behind on an old image, so it is counted here too (DL-46).
  $targets = @($apps).Count + $jobPresent
  $countColor = if ($targets -eq 17) { 'DarkGray' } else { 'Red' }
  $suffix = if ($Replicas) { '' } else { '   (-Replicas adds live pod counts)' }
  Write-Host ""
  Write-Host "  FLEET      " -ForegroundColor Yellow -NoNewline
  Write-Host ("{0} of 17 targets = 16 apps + 1 job{1}" -f $targets, $suffix) -ForegroundColor $countColor
  # Width comes from the data, never a literal: S153's `deliberator-proponent` is 21
  # characters and silently ran into the next column under the old hardcoded 19.
  # Adding an agent must not be able to break the board again.
  $nameLengths = @(@($apps).name) + @($JobName) |
    Where-Object { $_ } | ForEach-Object { "$_".Length }
  $appW = [Math]::Max(19, (($nameLengths | Measure-Object -Maximum).Maximum + 2))
  # Same rule for the image column, and for the same reason: a literal width is a guess
  # about data that changes. `v0.90.02` is 8 characters and ran into the next column
  # under the old hardcoded 7, rendering `v0.90.020` — a tag and a replica count fused
  # into one unreadable token (2026-08-12). It only appears when tags differ.
  $imgW = 0
  if ($mixed) {
    $tagLengths = @($tags | ForEach-Object { (& $short $_).Length })
    $imgW = [Math]::Max(9, (($tagLengths | Measure-Object -Maximum).Maximum + 2))
  }
  $podHead = if ($Replicas) { "{0,-6}" -f 'PODS' } else { '' }
  $header = "    {0,-$appW}" -f 'APP'
  if ($mixed) { $header += ("{0,-$imgW}" -f 'IMAGE') }
  $header += ("{0}{1,-9}{2}" -f $podHead, 'POWER', "WAKE ($tz)")
  Write-Host $header -ForegroundColor DarkGray
  foreach ($a in @($apps) | Sort-Object name) {
    # A non-Succeeded app is named in the verdict block, so the name itself carries the
    # colour here rather than a column that reads `Succeeded` on every row.
    $nc = if ($a.state -eq 'Succeeded') { 'White' } else { 'Red' }
    Write-Host ("    {0,-$appW}" -f $a.name) -ForegroundColor $nc -NoNewline
    if ($mixed) {
      Write-Host ("{0,-$imgW}" -f (& $short (& $tag $a.image))) -ForegroundColor Yellow -NoNewline
    }
    $inWin = Test-InWindow $a.winStart $a.winEnd
    if ($Replicas) {
      $n = Get-ReplicaCount $a.name
      if ($null -eq $n) {
        # Never print 0 for a call that failed — that is how a broken probe passes for a fact.
        Write-Host ("{0,-6}" -f '?') -ForegroundColor Magenta -NoNewline
      } else {
        # 0 pods inside the wake window is the only combination that is actually wrong.
        $rc = if ($n -gt 0) { 'Green' } elseif ($inWin -eq $true) { 'Red' } else { 'DarkGray' }
        Write-Host ("{0,-6}" -f $n) -ForegroundColor $rc -NoNewline
      }
    }
    $label = switch ($inWin) { $true { 'awake' } $false { 'asleep' } default { '?' } }
    $wc = if ($inWin -eq $true) { 'Cyan' } else { 'DarkGray' }
    Write-Host ("{0,-9}" -f $label) -ForegroundColor $wc -NoNewline
    $from = Format-WindowClock $a.winStart
    $to = Format-WindowClock $a.winEnd
    $win = if ($from -and $to) { "{0} - {1}" -f $from, $to } else { '-' }
    Write-Host $win -ForegroundColor DarkGray
  }
  if ($jobInfo) {
    Write-Host ("    {0,-$appW}" -f $JobName) -ForegroundColor White -NoNewline
    if ($mixed) { Write-Host ("{0,-$imgW}" -f (& $short (& $tag $jobInfo.image))) -ForegroundColor Yellow -NoNewline }
    if ($Replicas) { Write-Host ("{0,-6}" -f '-') -ForegroundColor DarkGray -NoNewline }
    Write-Host ("{0,-9}" -f 'on cron') -ForegroundColor DarkGray -NoNewline
    Write-Host "fires every 10 min inside the window" -ForegroundColor DarkGray
  }
  Write-Host ""
  return $problems.Count
}

if ($Watch) {
  while ($true) { $null = Show-Board; Start-Sleep -Seconds $IntervalSeconds }
} else {
  # Exit code mirrors the verdict (0 = GREEN, 1 = RED) so the board is scriptable.
  exit ([int]((Show-Board) -gt 0))
}
