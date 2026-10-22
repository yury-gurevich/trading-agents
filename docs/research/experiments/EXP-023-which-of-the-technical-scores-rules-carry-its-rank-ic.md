# EXP-023 — Which of the technical score's rules carry its rank IC, and does the scanner's filter pick names that beat the ones it turns away?

**Status:** PRE-REGISTERED 2026-10-23 (`8afc707c`) | COMPLETE 2026-10-23 · **no component of the
technical score carries after Holm, and the scanner's selection does not carry; nothing changes.**
Sections 1–5 and Appendix P are as pre-registered.
**Decision / origin:** [DL-314](../../design-log.md) · work-queue **137** · the operator, 2026-10-23,
on EXP-015's reported reading of the technical score: *"yes it is"* (worth a follow-up for the edge
question) · **Cost:** $0 (no LLM, no vendor; local CPU only).

## 1. Why we needed this experiment

[EXP-015](EXP-015-price-only-ensemble-vs-technical-score.md) failed its bar, and it reported one
reading it was not built to test. Over 1,761 test sessions from 2018 to 2024, the analyst's
technical score has a mean rank IC of **−0.0099** against the 10-session forward excess return on
the scanner's survivors, and **−0.0070** on 2025-01-02 → 2026-09-25. In the price-only replay the
composite *is* the technical score (no fundamentals or news), so that score is what ranks the
replay's buys.

The score is not one rule. `score_candidate`'s `technical_score` is
`0.8 × (mean of the available rule sub-scores / 100) + 0.2 × (rs_score / 100)`, or the mean alone
when relative strength cannot compute. It averages **15 banded rules**: four that reward trend
(`sma_distance_pct`, `ema_spread_pct`, `macd_histogram`, `golden_cross`), five that reward weakness
(`rsi`, `rsi2`, `bollinger_position`, `stochastic_k`, `williams_r`) and six others (`atr_pct`,
`choppiness`, `obv`, `nw_deviation_pct`, `geometric_pattern`, `turnaround`). Relative strength
(`rs_score`) is the sixteenth component. If trend and weakness rules carry opposite signs, their
equal-weight mean cancels, and a zero says nothing about what its parts know.

**The decision that waits on the answer:**

- Should a re-specified technical score be pre-registered (a new experiment, on data no experiment
  has read)?
- Or does the price-only ranking have nothing to give, so that work stops there?

A second, cheaper question shares the data. Does the scanner's filter itself pick names that beat
the members it turns away? If the pipeline has an edge (EXP-014 will say, after the fidelity PASS),
that is where a price-only one could live.

**Nothing in the fleet changes on this result.** `agents/analyst/` and `agents/scanner/` are decision
paths of the fidelity count (`scripts/replay_fidelity_git.py`), so no change to either ships before
the fidelity PASS, whatever this reads.

## 2. Hypothesis

This is a descriptive decomposition with a family-wise test. It has no promotion bar.

- **Q1 — the components (16).** For each component *c*, its 0–100 score's mean per-session Spearman
  rank IC against the 10-session forward excess return over SPY, on the scanner's survivors, over the
  **scored window 2018-01-02 → 2024-12-31**. *c* **carries** when its bootstrap test rejects a zero
  mean after **Holm's step-down across all 16 at a family-wise 5 %**. A positive sign means the
  component's bullish reading earns; a negative sign means it points the wrong way. H0 for each *c*:
  mean IC 0.
- **Q2 — the scanner's selection.** Among offered members with at least 253 bars of their own: per
  session, the mean 10-session forward excess return of the survivors minus that of the
  non-survivors, averaged over the scored window. It **carries** when its bootstrap 95 % interval
  excludes 0. H0: the difference is 0.
- **Why this bar.** Holm, because 16 components are tested at once: at an unadjusted 5 %, about 0.8
  of them would carry by chance alone. The interval and the sessions are EXP-015's, so the two
  experiments read the same evidence the same way.

**Reported, not tested:**

- Each component's raw indicator value's IC, before banding: does the banding lose or invert what
  the indicator knows?
- Horizons 5 and 20.
- Per-year means.
- Each component's coverage: the share of survivor rows where it computes.
- 2025-01-02 → 2026-09-25 apart, marked as already read in aggregate by EXP-015.

## 3. Data

- **The S235 cache:** OneDrive `trading-agents-data`, never the repo, licensed SIP bars. File
  checksums as EXP-015's `panel.json`: `sp500_bars` `198cffbb3542`, `sp500_benchmark`
  `f40b8b60506a`, `sp500_coverage` `0ba083a797d2`, `sp500_membership` `db971f1b3b95`,
  `sp500_sectors` `7a6801c55f21`, `sp500_sessions` `15ba1326e091`, `sp500_vix` `f80fa60b3ed9`.
- **EXP-015's panel:** OneDrive `trading-agents-data/experiments/EXP-015/panel.npz`, file SHA-256
  `c9cf472f…`, panel digest `aff1a727…`. It holds 1,209,946 rows (715,852 survivors), each row's
  session, line, survivor and 253-bar flags, the technical score, and the forward returns at 5, 10
  and 20 sessions with SPY's. Q2 reads it alone.
- **Q1's components** are recomputed by the analyst's own `score_candidate`, on the window the panel
  stage used, and aligned to the panel's rows.
- **Known defects:** EXP-015's: the four adjustment errors masked by DL-313, and today's sector
  labels. Q1 and Q2 read no sector.

## 4. Tools and setup

- **Machine:** i7-7660U (2 cores, 4 threads), Windows 10.
- **Software:** Python 3.13.2 and numpy 2.5.3, the main checkout's venv.
- **Code:** the repo at this file's commit: code identical to `1c91c21e`, EXP-015's, since only docs
  moved. It runs from a detached worktree.
- **The script:** a planner's read-only script, `exp023_components.py`, in OneDrive
  `trading-agents-data/exp023-2026-10-23/`. It reuses `scripts/exp015_*` for offering, IC and the
  interval. It goes verbatim into Appendix S, with its SHA-256 in Appendix R.
- **Seed and cap:** bootstrap seed 0. Cost cap $0.

## 5. How it was conducted

1. **Pilot, not scored:** the F1 pilot window (the first 40 lines, 2016-01-04 → 2017-12-29). It proves
   the alignment and the run time and reads nothing from 2018 on. The script may be fixed after the
   pilot. After the first scored run it is frozen.
2. **Q1's rows.** For every session, the panel stage's loop exactly: members, the visible window,
   `offer_lines`, `apply_filters` with the pack's settings. Then, for each survivor,
   `score_candidate(...).metrics`. From it the script keeps the 15 `{rule}_score` values and
   `rs_score`, and each raw value (`{rule}`, `relative_strength`); NaN where a component did not
   compute.
3. **Alignment, a stop condition.** Each survivor row is matched to the panel by session and line.
   Its `technical_score` must equal the panel's baseline, and the 0.8 / 0.2 blend rebuilt from its
   components must equal it too, within 1e-12. One mismatch stops the run as `STOPPED`, unscored.
4. **IC.** `exp015_ranks.session_ic` per component per session: at least 10 rows with both values,
   and a session where the component is flat (one band) has no IC.
5. **Interval and test.** `exp015_rule.interval`'s method, the same draws for both:
   - every 10th session;
   - stationary bootstrap, mean block 20, 10,000 resamples, seed 0;
   - percentile 95 % interval;
   - two-sided bootstrap p = min(1, 2 × (1 + resampled means on the far side of 0) / 10,001).

   Holm then runs over the 16 p-values.
6. **Q2** from `panel.npz`: among rows with the 253-bar flag, per session with at least 10 survivors
   and 10 non-survivors, the survivors' mean excess return minus the non-survivors'. The interval is
   the same.
7. **Outputs** go to OneDrive `trading-agents-data/experiments/EXP-023/`: a JSON record and a page.
   Nothing licensed goes in the repo.

## 6. Results

**MEASURED.** One scored run, 2026-10-22 15:26 → 16:56 UTC, `exp023.json` (Appendix R).

- **Rows:** 715,852 survivor rows, every one of EXP-015's.
- **Alignment:** 0 mismatches, so every recomputed score and every rebuilt blend equals EXP-015's
  panel. 0 rows rejected for short history.
- **Cross-check:** the technical score's own IC reproduces EXP-015's: **−0.0099** over 1,761
  sessions, interval [−0.0175, +0.0119].

**Q1 — no component carries.** Holm across the 16 needs p ≤ 0.0031 for the first. The smallest p is
0.0172 (`bollinger_position`). Mean IC at 10 sessions, 2018–2024, 95 % interval:

| Group | Component | IC | 95 % interval | p | Raw indicator's IC | 2025 → |
| --- | --- | --- | --- | --- | --- | --- |
| Trend | `sma_distance_pct` | −0.0051 | [−0.0183, +0.0102] | 0.645 | −0.0084 | −0.0077 |
| Trend | `ema_spread_pct` | −0.0084 | [−0.0238, +0.0031] | 0.149 | −0.0116 | −0.0032 |
| Trend | `macd_histogram` | −0.0111 | [−0.0223, +0.0070] | 0.310 | −0.0106 | −0.0054 |
| Trend | `golden_cross` | +0.0004 | [−0.0120, +0.0133] | 0.872 | +0.0004 | −0.0195 |
| Trend | `rs` (relative strength) | −0.0128 | [−0.0208, +0.0081] | 0.354 | −0.0134 | +0.0011 |
| Weakness | `rsi` | +0.0066 | [−0.0053, +0.0280] | 0.191 | −0.0083 | −0.0020 |
| Weakness | `rsi2` | +0.0079 | [−0.0116, +0.0236] | 0.504 | −0.0091 | +0.0009 |
| Weakness | `bollinger_position` | +0.0094 | [+0.0028, +0.0331] | 0.017 | −0.0107 | +0.0007 |
| Weakness | `stochastic_k` | +0.0099 | [−0.0014, +0.0233] | 0.079 | −0.0097 | −0.0028 |
| Weakness | `williams_r` | +0.0103 | [+0.0026, +0.0282] | 0.019 | −0.0097 | −0.0013 |
| Other | `nw_deviation_pct` | +0.0116 | [+0.0008, +0.0327] | 0.040 | −0.0155 | +0.0029 |
| Other | `obv` | −0.0088 | [−0.0201, +0.0044] | 0.233 | +0.0126 | +0.0033 |
| Other | `atr_pct` | −0.0041 | [−0.0194, +0.0162] | 0.864 | +0.0028 | −0.0484 |
| Other | `choppiness` | −0.0019 | [−0.0270, +0.0141] | 0.503 | +0.0022 | +0.0173 |
| Other | `geometric_pattern` (59 % of rows) | −0.0151 | [−0.0181, +0.0096] | 0.571 | +0.0012 | +0.0098 |
| Other | `turnaround` (317 sessions not flat) | −0.0006 | [−0.0051, +0.0383] | 0.118 | −0.0006 | +0.0133 |

- **Reported, not tested: a sign pattern below the bar.** The five weakness rules and the kernel
  deviation lean positive (+0.007 to +0.012). Three of them have unadjusted intervals clear of
  zero: `bollinger_position`, `williams_r` and `nw_deviation_pct`. The trend rules and relative
  strength lean negative (−0.005 to −0.013). The 5- and 20-session readings keep each sign.
- **Raw values.** Each weakness rule's raw indicator has the opposite sign to its score, as its
  banding intends: a low reading scores high. For those rules the banding keeps the information
  and does not invert it. (`obv`'s raw value is the level, while its score compares the level with
  its signal line, so those two signs are not comparable.)
- **Q2 — the scanner's selection does not carry.** Survivors minus non-survivors over 10 sessions:
  **+0.06 %**, interval [−0.13 %, +0.31 %], p 0.43. At 5 sessions +0.02 %, at 20 +0.10 %, neither
  clear of zero; 2025 → +0.20 %.

## 7. Conclusions

**None carries.** On the reading fixed before the run, the price-only technical pillar shows no
information at these horizons that survives testing 16 components at once. The scanner's filter
picks names no better than the members it turns away. Whether the technical score keeps ranking is
the operator's call, after EXP-014 scores (work-queue 82).

**What it does not say:**

- It does not show cancellation. The pattern is consistent with it: the weakness rules lean
  positive, the trend rules negative, and the equal-weight mean lands below zero. But no component
  clears Holm, and the three weakness rules clear of zero unadjusted read close cousins of one
  thing: price near the bottom of its recent range.
- It says nothing about the live composite, where fundamentals and sentiment join the technical
  pillar.

**What it rules out:** building a re-weighted technical score from this data. A short-term
reversal score (the weakness rules alone) is the one shape worth a new pre-registration. It could only be
proven on sessions after 2026-09-25, which no experiment has read.

The reading fixed before the run:

- **Components carry with opposite signs:** cancellation explains the zero. A re-specified score is
  a new pre-registered experiment on sessions after 2026-09-25, which no experiment has read.
- **None carries:** the price-only technical pillar shows no information at these horizons. Whether
  it keeps ranking is the operator's call, after EXP-014 scores.
- **Q2 carries:** the scanner's filter is where price-only information lives.

## 8. Recommended code changes, and how to implement them

**None.** Nothing carries, and `agents/analyst/` and `agents/scanner/` cannot change before the
fidelity PASS in any case. After EXP-014 scores, the operator decides whether the price-only ranking
is kept, replaced or pre-registered anew as a reversal score on unseen sessions.

## Appendix P — Pre-registration (frozen)

Frozen at the commit that adds this file (`git log --diff-filter=A` on this path). Never edited.

- **Components (16):** `rsi`, `macd_histogram`, `bollinger_position`, `sma_distance_pct`,
  `ema_spread_pct`, `atr_pct`, `stochastic_k`, `williams_r`, `choppiness`, `obv`, `golden_cross`,
  `rsi2`, `nw_deviation_pct`, `geometric_pattern`, `turnaround` (each `{name}_score`), and `rs_score`.
- **Universe:** the scanner's survivors per session, as EXP-015's panel stage offers them.
- **Target:** the 10-session forward excess return over SPY, next open to the tenth close (EXP-015's
  `returns − spy` at horizon 10).
- **Scored window:** 2018-01-02 → 2024-12-31. 2025-01-02 → 2026-09-25 is reported apart.
- **Statistic:** the mean of per-session Spearman ICs (`session_ic`, at least 10 rows, flat sessions
  excluded).
- **Interval and test:** every 10th session; stationary bootstrap, mean block 20, 10,000 resamples,
  seed 0; percentile 95 %; two-sided p = min(1, 2 × (1 + far-side count) / 10,001); Holm across the
  16 at 0.05.
- **Q2:** survivors' minus non-survivors' mean 10-session excess return, among rows with at least 253
  bars, per session with at least 10 of each; same window and interval; carries when the interval
  excludes 0.
- **Stop:** any survivor row whose recomputed `technical_score`, or the blend rebuilt from its
  components, differs from the panel's baseline by more than 1e-12.
- **Pilot:** the first 40 lines, 2016-01-04 → 2017-12-29, not scored.

## Appendix R — Run record

- **Code:** `8afc707c`, the pre-registration's commit, clean, from a detached worktree
  (`../ta-exp023`). The code is identical to `1c91c21e`: `git diff 1c91c21e 8afc707c` touches no file
  under `scripts/`, `agents/`, `contracts/` or `kernel/`.
- **Environment:** the main venv's Python 3.13.2, numpy 2.5.3; i7-7660U.
- **Script:** `exp023_components.py` SHA-256
  `b43015cfdf5ca09b28d26bb19bc95ce772ec3635e91088e22a335bbaaa71c866`, frozen after the pilot.
- **Pilot:** 2026-10-22, first 40 lines, 2016-01-04 → 2017-12-29, against a panel built in the
  script. 6,928 survivor rows (F1's count), 0 mismatches, 0 rejected, 87 s; every component present
  (`geometric_pattern` on 63 % of rows). Nothing from 2018 on was read. Output `pilot/pilot.json` in
  the kit.
- **Scored run:** `run_exp023.ps1` launched detached, 15:26:41 → 16:56:32 UTC. The worker ran at Normal
  priority for its first eight minutes (only the venv's launcher took BelowNormal), then was lowered
  by hand; the results are unaffected. EXP-015's panel digest was checked first (`aff1a727…`).
  715,852 rows, 0 mismatches, 0 rejected; verdict `COMPLETE`.
- **Output:** OneDrive `trading-agents-data/experiments/EXP-023/exp023.json`, SHA-256
  `d06854a3e1967bd19a9b59799d4a7ffba254e1e35baffb66d1580a65865c754c`. Kit:
  `trading-agents-data/exp023-2026-10-23/` (script, runner, log, stderr, pilot).
- **Clarification, not a change:** Appendix P's stop names *"the blend rebuilt from its components"*.
  A row the scorer rejects for short history would carry no components; the script compares only its
  score. None occurred (0 rejected).

## Appendix S — Scripts

`exp023_components.py`, run as `<main venv python> -B exp023_components.py <tree> <cache> <EXP-015 out> <out> [--pilot]`.
Verbatim except one comment: `# pragma: allowlist secret` is appended to the `PANEL_SHA` line here
only, because the repo's secrets scan reads that checksum as a secret. The SHA-256 in Appendix R is
of the kit's file, which has no such comment.

```python
"""EXP-023: the technical score's 16 components' rank IC, and the scanner's selection (DL-314).

A planner's read-only script. Main venv python, the tree (a clean worktree) first on sys.path:

  python -B exp023_components.py <tree> <cache> <exp015_out> <out_dir> [--pilot]

--pilot: the first 40 lines, 2016-01-04 .. 2017-12-29, aligned to a panel built here; not scored.
Otherwise: every cached session, aligned to EXP-015's saved panel (its digest checked first).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(TREE))

import numpy as np  # noqa: E402

from agents.analyst.domain.scoring import score_candidate  # noqa: E402
from agents.scanner.domain.filters import apply_filters  # noqa: E402
from contracts.scanner import Candidate  # noqa: E402
from scripts.exp015_panel import build_panel  # noqa: E402
from scripts.exp015_ranks import session_ic  # noqa: E402
from scripts.exp015_spec import BLOCK, HORIZONS, RESAMPLES, SEED, STEP_SESSIONS  # noqa: E402
from scripts.exp015_store import load_panel, panel_digest  # noqa: E402
from scripts.replay_cache import load_replay_cache  # noqa: E402
from scripts.replay_history import offer_lines, visible_window  # noqa: E402
from scripts.replay_series import bars_by_line, benchmark_window, contract_bars, members_on  # noqa: E402
from scripts.replay_settings import build_effective_settings  # noqa: E402
from scripts.replay_verdict_stats import percentile_interval, seeded, stationary_draws  # noqa: E402
from scripts.sp500_guards import load_known_moves  # noqa: E402

RULES = (  # score_technical's order: momentum, range, event, pattern
    "rsi", "macd_histogram", "bollinger_position", "sma_distance_pct", "ema_spread_pct",
    "atr_pct", "stochastic_k", "williams_r", "choppiness", "obv", "golden_cross", "rsi2",
    "nw_deviation_pct", "geometric_pattern", "turnaround",
)  # fmt: skip
COMPONENTS = (*RULES, "rs")
SCORE_KEY = {**{r: f"{r}_score" for r in RULES}, "rs": "rs_score"}
RAW_KEY = {**{r: r for r in RULES}, "rs": "relative_strength"}
PANEL_SHA = "aff1a727b1c0e9d1e9ccef3577d0aa2143150e7396702da3023693bccee52b52"  # pragma: allowlist secret
WINDOW, LATER = ("2018-01-02", "2024-12-31"), ("2025-01-02", "2026-09-25")
TOL, ALPHA, MIN_GROUP = 1e-12, 0.05, 10


def collect(context, settings, line_bars, sessions, lines):
    """Per survivor row: (session, line, technical_score, rejected, scores[16], raws[16])."""
    dates = {k: {r.date for r in v} for k, v in line_bars.items() if lines is None or k in lines}
    keys, tech, rejected, scores, raws = [], [], [], [], []
    for n, session in enumerate(sessions):
        members = tuple(m for m in members_on(context.universe, session) if m in dates)
        window = visible_window(settings, line_bars, members, session)
        offered = offer_lines(settings, members, window, ())
        contract = contract_bars(offered.bars)
        bench = benchmark_window(context.benchmark, session, offered.bars)
        survivors, _ = apply_filters(
            offered.members, contract, bench, {}, session, settings.scanner,
            earnings_horizon_days=None,
        )  # fmt: skip
        primary = {s.ticker for s in survivors}
        by_line: dict[str, list] = {}
        for bar in contract:
            by_line.setdefault(bar.ticker, []).append(bar)
        for line in offered.members:
            if line not in primary or session not in dates[line]:
                continue
            candidate = Candidate(ticker=line, rank=1, score=0.0, survived_filters=())
            b = score_candidate(candidate, tuple(by_line[line]), {}, bench, (), settings.analyst)
            keys.append((session.isoformat(), line))
            tech.append(b.technical_score)
            rejected.append(b.rejection_reason is not None)
            scores.append([b.metrics.get(SCORE_KEY[c], np.nan) for c in COMPONENTS])
            raws.append([b.metrics.get(RAW_KEY[c], np.nan) for c in COMPONENTS])
        if (n + 1) % 100 == 0 or n + 1 == len(sessions):
            print(f"exp023 {session} {n + 1}/{len(sessions)} rows={len(keys)}", file=sys.stderr, flush=True)
    return keys, np.array(tech), np.array(rejected), np.array(scores, float), np.array(raws, float)


def blend(scores: np.ndarray, weight: float) -> float:
    """score_candidate's technical_score rebuilt: 0.8 x rule mean + 0.2 x RS, bounded."""
    rule = [float(x) for x in scores[: len(RULES)] if np.isfinite(x)]
    technical = max(0.0, min(1.0, (sum(rule) / len(rule) if rule else 50.0) / 100.0))
    rs = float(scores[-1])
    if not np.isfinite(rs):
        return technical
    return max(0.0, min(1.0, (1.0 - weight) * technical + weight * max(0.0, min(1.0, rs / 100.0))))


def align(keys, tech, rejected, scores, panel, weight):
    """Panel row per recorded row; every mismatch, with up to five examples."""
    where = {k: i for i, k in enumerate(zip(panel.sessions.tolist(), panel.lines.tolist(), strict=True))}
    index, bad = np.full(len(keys), -1), []
    for k, key in enumerate(keys):
        i = where.get(key)
        if i is None or not panel.primary[i]:
            bad.append((key, "not a survivor row in the panel"))
            continue
        index[k] = i
        base = float(panel.baseline[i])
        rebuilt = base if rejected[k] else blend(scores[k], weight)
        if abs(tech[k] - base) > TOL or abs(rebuilt - base) > TOL:
            bad.append((key, f"technical {tech[k]!r} rebuilt {rebuilt!r} panel {base!r}"))
    covered = set(panel.sessions[index[index >= 0]].tolist()) if len(keys) else set()
    expected = int(sum(1 for s, p in zip(panel.sessions.tolist(), panel.primary, strict=True) if p and s in covered))
    if expected != len(keys):
        bad.append((("*", "*"), f"panel has {expected} survivor rows on these sessions, recorded {len(keys)}"))
    return index, bad


def reading(values: dict[str, float]) -> dict[str, object]:
    """Mean over all sessions; every 10th session's stationary bootstrap: interval and two-sided p."""
    if not values:
        return {"sessions": 0, "mean": None, "step_sessions": 0, "step_mean": None, "low": None, "high": None, "p": 1.0}
    series = list(values.values())[::STEP_SESSIONS]
    rng = seeded(SEED)
    means = [sum(series[i] for i in stationary_draws(len(series), BLOCK, rng)) / len(series) for _ in range(RESAMPLES)]
    low, high = percentile_interval(means)
    step_mean = sum(series) / len(series)
    far = sum(1 for m in means if (m <= 0.0 if step_mean > 0.0 else m >= 0.0))
    return {
        "sessions": len(values), "mean": sum(values.values()) / len(values),
        "step_sessions": len(series), "step_mean": step_mean, "low": low, "high": high,
        "p": min(1.0, 2.0 * (1 + far) / (RESAMPLES + 1)),
    }  # fmt: skip


def holm(ps: dict[str, float]) -> dict[str, bool]:
    order, out = sorted(ps, key=lambda c: ps[c]), dict.fromkeys(ps, False)
    for k, c in enumerate(order):
        if ps[c] > ALPHA / (len(order) - k):
            break
        out[c] = True
    return out


def within(values: dict[str, float], span: tuple[str, str]) -> dict[str, float]:
    return {k: v for k, v in values.items() if span[0] <= k <= span[1]}


def by_year(values: dict[str, float]) -> dict[str, float]:
    years: dict[str, list[float]] = {}
    for k, v in values.items():
        years.setdefault(k[:4], []).append(v)
    return {y: sum(v) / len(v) for y, v in sorted(years.items())}


def selection(panel, h: int) -> dict[str, float]:
    """Per session: survivors' minus non-survivors' mean excess return, 253-bar rows, 10 of each."""
    target = panel.excess[:, h]
    rows = panel.secondary & np.isfinite(target)
    out: dict[str, float] = {}
    days, codes = np.unique(panel.sessions[rows], return_inverse=True)
    t, p = target[rows], panel.primary[rows]
    for k, day in enumerate(days):
        mask = codes == k
        s, n = t[mask & p], t[mask & ~p]
        if len(s) >= MIN_GROUP and len(n) >= MIN_GROUP:
            out[str(day)] = float(s.mean() - n.mean())
    return out


def main(argv: list[str]) -> int:
    cache, exp015_out, out_dir = (Path(a) for a in argv[2:5])
    pilot = "--pilot" in argv
    out_dir.mkdir(parents=True, exist_ok=True)
    context = load_replay_cache(cache)
    settings = build_effective_settings(())
    line_bars = bars_by_line(context.universe.bars)
    if pilot:
        lines = set(sorted(line_bars)[:40])
        days = tuple(d for d in context.universe.sessions if d <= date(2017, 12, 29))
        errors: dict[str, tuple[date, ...]] = {}
        for move in load_known_moves():
            if move.kind == "adjustment-error":
                errors[move.line] = (*errors.get(move.line, ()), move.date)
        panel, _ = build_panel(context, settings, line_bars, errors, days, lines)
    else:
        lines, days = None, context.universe.sessions
        panel = load_panel(exp015_out)
        if panel_digest(panel) != PANEL_SHA:
            print("STOPPED: EXP-015's panel digest differs", file=sys.stderr)
            return 3
    keys, tech, rejected, scores, raws = collect(context, settings, line_bars, days, lines)
    index, bad = align(keys, tech, rejected, scores, panel, settings.analyst.relative_strength_weight)
    record: dict[str, object] = {
        "experiment": "EXP-023", "pilot": pilot, "rows": len(keys), "rejected_rows": int(rejected.sum()),
        "mismatches": len(bad), "mismatch_examples": [[list(k), why] for k, why in bad[:5]],
    }  # fmt: skip
    if bad:
        record["verdict"] = "STOPPED"
        (out_dir / ("pilot.json" if pilot else "exp023.json")).write_text(json.dumps(record, indent=2) + "\n", "utf-8")
        print(json.dumps(record, indent=2))
        return 2
    sessions = np.array([k[0] for k in keys])
    targets = {h: panel.excess[index, j] for j, h in enumerate(HORIZONS)}
    span = (keys[0][0], keys[-1][0]) if pilot else WINDOW
    in_span = (sessions >= span[0]) & (sessions <= span[1])
    comps: dict[str, dict[str, object]] = {}
    for c, name in enumerate(COMPONENTS):
        ic = {h: session_ic(scores[:, c], targets[h], sessions) for h in HORIZONS}
        raw_ic = session_ic(raws[:, c], targets[10], sessions)
        comps[name] = {
            "coverage": float(np.isfinite(scores[in_span, c]).mean()) if in_span.any() else None,
            "ic10": reading(within(ic[10], span)),
            "ic5_mean": reading(within(ic[5], span))["mean"],
            "ic20_mean": reading(within(ic[20], span))["mean"],
            "raw_ic10": reading(within(raw_ic, span)),
            "per_year": by_year(within(ic[10], span)),
            "later_ic10_mean": None if pilot else reading(within(ic[10], LATER))["mean"],
        }
    carries = holm({name: float(comps[name]["ic10"]["p"]) for name in COMPONENTS})
    for name in COMPONENTS:
        comps[name]["carries"] = carries[name]
    technical_ic = session_ic(tech, targets[10], sessions)
    record |= {
        "window": list(span), "components": comps,
        "technical_score_ic10": reading(within(technical_ic, span)),
        "selection": {h: reading(within(selection(panel, j), span)) for j, h in enumerate(HORIZONS)},
        "selection_later_mean": None if pilot else reading(within(selection(panel, 1), LATER))["mean"],
        "verdict": "PILOT" if pilot else "COMPLETE",
    }  # fmt: skip
    name = "pilot.json" if pilot else "exp023.json"
    (out_dir / name).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", "utf-8")
    print(f"{record['verdict']} rows={len(keys)} rejected={record['rejected_rows']} carries={[c for c in COMPONENTS if carries[c]]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

`run_exp023.ps1`, run as `pwsh -NoProfile -File run_exp023.ps1` (launched detached through
`Win32_Process.Create`):

```powershell
# EXP-023's one scored run (DL-314): the frozen exp023_components.py over every cached session.
#   pwsh -NoProfile -File run_exp023.ps1
param(
    [string]$Tree = 'C:\Users\yury_\Downloads\project\ta-exp023',
    [string]$Python = 'C:\Users\yury_\Downloads\project\trading-agents\.venv\Scripts\python.exe',
    [string]$Cache = 'C:\Users\yury_\OneDrive\trading-agents-data',
    [string]$Exp015 = 'C:\Users\yury_\OneDrive\trading-agents-data\experiments\EXP-015',
    [string]$Out = 'C:\Users\yury_\OneDrive\trading-agents-data\experiments\EXP-023',
    [string]$Kit = 'C:\Users\yury_\OneDrive\trading-agents-data\exp023-2026-10-23'
)
$ErrorActionPreference = 'Stop'
$log = Join-Path $Kit 'exp023_run.log'
function Say([string]$text) { "$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')) $text" | Add-Content -Path $log -Encoding utf8 }

Add-Type -Namespace Win -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint flags);'
[void][Win.Power]::SetThreadExecutionState([uint32]2147483649)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
try {
    $script = Join-Path $Kit 'exp023_components.py'
    Say "commit $(git -C $Tree rev-parse HEAD) dirty_lines $((git -C $Tree status --porcelain --untracked-files=no | Measure-Object).Count) script_sha256 $((Get-FileHash $script -Algorithm SHA256).Hash.ToLower())"
    Say 'START scored'
    $stdout = Join-Path $Kit 'exp023_stdout.txt'
    $stderr = Join-Path $Kit 'exp023_stderr.txt'
    $p = Start-Process -FilePath $Python -ArgumentList @('-B', $script, $Tree, $Cache, $Exp015, $Out) `
        -WorkingDirectory $Tree -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru
    $null = $p.Handle  # cache the handle, or ExitCode reads empty after the exit
    $p.PriorityClass = 'BelowNormal'
    $p.WaitForExit()
    Say "END scored exit=$($p.ExitCode) $((Get-Content $stdout -Raw).Trim())"
    if ($p.ExitCode -eq 0) { Say 'DONE' } else { Say 'ERROR' }
} catch {
    Say "ERROR $($_.Exception.Message)"
} finally {
    [void][Win.Power]::SetThreadExecutionState([uint32]2147483648)
}
```
