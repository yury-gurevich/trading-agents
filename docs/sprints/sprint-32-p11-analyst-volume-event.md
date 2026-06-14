<!-- Agent: planning | Role: sprint handover -->
# Sprint 32 — P11 analyst: volume + event signals (OBV / golden cross / RSI-2)

**Status:** planned · **Branch:** `sprint-32-p11-analyst-volume-event` · **Build phase:** P11 · **Effort: M**

## Goal

Add three more indicators to the analyst technical engine: **OBV** (on-balance volume vs its
signal line), the **golden cross** (SMA-50 over SMA-200), and **RSI-2 mean reversion** (a
short-period RSI oversold/overbought signal). Each is scored 0–100 and folded into the same
composite `technical_score`, taking the engine from 9 to 12 indicators. All use data the
`OHLCVBar` already carries (close + volume) — **no provider change, no contract change**.

This continues the Sprint 30/31 pattern exactly. The heavier **pattern** work (Nadaraya-Watson
kernel smoother, geometric chart patterns, the calendar "turnaround" signal) is **deferred to a
following sprint** — it is materially more complex and does not belong in this batch.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/sprints/sprint-31-p11-analyst-oscillators.md`
  (the immediately-prior slice — identical structure: new `indicators_*` + `technical_rules_*`
  companion modules folded into `score_technical`).
- **Shipped code you extend (read it):**
  - `agents/analyst/domain/technical_rules.py` — `score_technical(bars, settings)` already
    derives `closes`/`highs`/`lows` and concatenates `_momentum_scores(closes,…)` +
    `range_indicator_scores(highs,lows,closes,…)`. You add a **volumes** extraction and a third
    group `event_indicator_scores(closes, volumes, settings)`.
  - `agents/analyst/domain/technical_rules_range.py` — the exact companion pattern to mirror
    (named band constants; a `*_indicator_scores(...)` that computes each indicator, skips `None`,
    returns `(name, value, score)` triples).
  - `agents/analyst/domain/indicators.py` — has `rsi(closes, period)` (reuse it for RSI-2) and
    the `_mean`/`_sma` style helpers.
  - `agents/analyst/settings.py` (157L) — justified `tunable(...)` periods; reuse
    `sma_long_period` (200) for the golden cross's long average.
- **Pure Python only** (no pandas/numpy). **`OHLCVBar.volume`** is an `int ≥ 0` (present on every
  bar). Work over the ascending-sorted bars (the caller already sorts).
- **Graceful degradation unchanged:** each indicator returns `None` on insufficient history; the
  composite averages only the available sub-scores.

### Indicator formulas (implement exactly — self-contained)

Let `closes`, `volumes` be parallel lists over the ascending bars.

- **OBV(signal_period=20):** build the OBV series — `obv[0] = 0.0`; for `i ≥ 1`:
  `+volume[i]` if `close[i] > close[i-1]`, `-volume[i]` if `close[i] < close[i-1]`, else unchanged
  (carry `obv[i-1]`). `signal = mean(obv_series[-signal_period:])`. Return `(obv_series[-1],
  signal)`; **`None`** below `signal_period + 1` bars. (Values may be large — that is fine; the
  rule only compares OBV to its signal.)
- **Golden cross(short=50, long=200):** `is_golden = mean(closes[-short:]) > mean(closes[-long:])`.
  Return `bool`; **`None`** below `long` bars.
- **RSI-2(period=2):** reuse `indicators.rsi(closes, period)` — returns `float | None` (`None`
  below `period + 1` closes). No new indicator function needed.

### Scoring rules (0–100; implement exactly)

- **OBV:** `obv > signal → 70` (accumulation, bullish), `else → 35` (distribution). Strict `>`.
- **Golden cross:** `is_golden → 75`, `else → 25`.
- **RSI-2:** `< 10 → 80` (deep oversold, mean-reversion buy), `> 90 → 20` (overbought),
  `else → 50`. Strict `<` / `>` (so exactly 10 or 90 → 50), consistent with Sprint 30/31.

## Part A — Settings

`agents/analyst/settings.py` — add three justified, bounded `tunable(...)`:
`obv_signal_period=20` (ge=2, le=100), `golden_cross_short_period=50` (ge=2, le=200),
`rsi2_period=2` (ge=2, le=10). The golden cross's long window **reuses** the existing
`sma_long_period` (200) — do not add a second one. Keep `why` strings concise.

**Size watch:** `settings.py` is at 157L; +3 tunables lands it ≈ 170L (within the 150 warn band,
under the 200 cap — acceptable). If it would cross ~190L, flag it: a later sprint may split the
analyst settings, but **do not** undertake that refactor here.

## Part B — Event indicators

`agents/analyst/domain/indicators_event.py` — ≤ 70L.

```python
"""Pure-Python volume/event indicators (OBV, golden cross).

Agent: analyst
Role: compute OBV vs its signal and the SMA-50/200 golden cross; no I/O, no pandas.
External I/O: none.
"""
```

Provide `obv(closes, volumes, signal_period) -> tuple[float, float] | None` and
`golden_cross(closes, short, long) -> bool | None`. (RSI-2 needs no function here — call
`indicators.rsi` from the rules module.) Total functions; never raise — return `None`.

## Part C — Event scoring rules

`agents/analyst/domain/technical_rules_event.py` — ≤ 80L.

```python
"""Volume/event scoring rules and their composite contribution.

Agent: analyst
Role: map OBV / golden cross / RSI-2 to 0-100 sub-scores.
External I/O: none.
"""
```

- Named band constants (mirror `technical_rules_range.py`) + `score_obv(obv, signal)`,
  `score_golden_cross(is_golden: bool)`, `score_rsi2(value)`.
- `event_indicator_scores(closes, volumes, settings) -> list[tuple[str, float, float]]`:
  - OBV: `("obv", obv_value, score_obv(obv_value, signal))` when available.
  - Golden cross: `("golden_cross", 1.0 if is_golden else 0.0, score_golden_cross(is_golden))`
    when available (store the boolean as 1.0/0.0 so the metric value is a `float`).
  - RSI-2: `("rsi2", rsi2, score_rsi2(rsi2))` via `indicators.rsi(closes, settings.rsi2_period)`.
  - Skip any that returned `None`. Import both `indicators` and `indicators_event`.

## Part D — Fold into the composite

`agents/analyst/domain/technical_rules.py`:

- In `score_technical`, add `volumes = [bar.volume for bar in bars]` (alongside closes/highs/lows)
  — `volume` is `int`; cast to `float` if the indicator math wants floats, or keep int and let OBV
  accumulate (your call; keep mypy --strict happy).
- Concatenate a third group:
  `triples = _momentum_scores(...) + range_indicator_scores(...) + event_indicator_scores(closes,
  volumes, settings)`. Everything downstream (metrics, averaging, `indicators_available`) is
  unchanged.

`scoring.py` needs **no change** (it already passes the sorted bars). Confirm `technical_rules.py`
stays < 150L after the small addition (it is ~141L now).

## Part E — Tests

### E1. `agents/analyst/tests/test_indicators_event.py` — ≤ 90L

Golden, hand-verified values over fixtures with **volume variation** (flat/zero volume makes OBV
trivial — give the fixtures real volume and up/down closes):

- `obv`: a series of known up/down closes with distinct volumes → a pinned final OBV and signal;
  `< signal_period + 1` bars → `None`. Include an unchanged-close bar to cover the carry branch.
- `golden_cross`: a series whose SMA-50 > SMA-200 → `True`; the reverse → `False`; `< long` → `None`.
- (RSI-2 is exercised through the existing `rsi` tests + the rule test in E2.)

### E2. `agents/analyst/tests/test_technical_rules_event.py` — ≤ 80L

Boundary tests for each rule: OBV `signal+1 vs signal → 70`, `signal-1 → 35`, `obv == signal → 35`
(strict `>`); golden cross `True → 75`, `False → 25`; RSI-2 `9.9 → 80`, `10.0 → 50`, `90.0 → 50`,
`90.1 → 20`. Plus `event_indicator_scores` returning the right triples / skipping unavailable ones.

### E3. Update `test_technical_rules.py` + `test_analyst_domain.py` (re-pin the composite)

The engine is now up to 12 indicators. Re-pin the Sprint-31 composite cases by hand:

- The "all available" long case (a 220-bar series with real H/L **and volume**) → `indicators_
  available == 12` (5 momentum + 4 range + 3 event); recompute the mean across all twelve.
- The mid-length case (40 bars) → recount: OBV (needs 21 ✓) and RSI-2 (needs 3 ✓) now also
  available, golden cross (needs 200 ✗) not → `indicators_available == 9` (was 7); re-pin the
  composite and the derived confidence.
- Thin case unchanged → `(50.0, {"indicators_available": 0.0})`.

**Recompute and re-pin every changed expected value by hand — do not weaken assertions.** Make
sure the fixtures used for the "all available" case carry non-degenerate volume.

### E4. Confirm downstream pipeline tests still pass unchanged

The thin ~4-bar pipeline fixtures degrade all 12 indicators → neutral 0.5 → confidence 0.60,
which still clears the strict-`<` regime floor. Run the whole suite; re-pin (don't weaken) any
fixture-rich test that moved.

## Steps

1. Branch `sprint-32-p11-analyst-volume-event` off `main`.
2. **A** settings → **B** `indicators_event.py` (+ E1) → **C** `technical_rules_event.py` (+ E2).
3. **D** fold into `score_technical`. `make ci`.
4. **E3/E4** re-pin analyst/pipeline tests. `make ci` green.
5. `wc -l agents/analyst/domain/*.py agents/analyst/settings.py` — all < 200 (< 150 preferred).
6. Push; hand back.

## Acceptance criteria

- OBV, golden cross, RSI-2 compute hand-verified values and return `None` (never raise) on
  insufficient history.
- Each rule maps to the exact 0–100 bands; `score_technical` averages all available sub-scores
  across momentum + range + event groups; `indicators_available` reflects the true count.
- `score_candidate`/`ScoreBreakdown`/`decide` and the analyst contract are unchanged.
- All analyst + pipeline tests pass with **pinned** expected values; `make ci` green at/above the
  coverage floor (100.00).
- Import-linter 4/4 kept; every touched module < 200L.

## Out of scope (later P11 sprints)

- **Patterns & smoothing:** Nadaraya-Watson kernel, geometric chart patterns (swing points, double
  top/bottom, head-and-shoulders, triangles) — the next P11 analyst sprint.
- **Calendar "turnaround" signal** (day-of-week Monday/Friday logic) — defer with the patterns
  sprint; it adds calendar edge-cases that don't fit this batch.
- Fundamental + sentiment scoring and relative strength — **blocked on a provider data feed**
  (OHLCV + VIX only today); needs a provider extension sprint first.
- Signal-diversity selection, confidence buckets, scanner beta; PM/scanner/reporter gaps.
- Any change outside the analyst package and its tests.

## Handback report (paste into PR / reply)

- Confirm no contract change and no `scoring.py` change (only `technical_rules.py` gained the
  volumes extraction + event group).
- The exact `<`/`>` boundaries implemented (esp. OBV `obv == signal` and RSI-2 at 10/90).
- The re-pinned `indicators_available` counts and composites for the long (12) and mid (9) cases.
- Final line counts: `indicators_event.py`, `technical_rules_event.py`, `technical_rules.py`,
  `settings.py`.
- New coverage % and floor; total test count.

The planning agent reviews, merges to `main`, and plans the next P11 slice (patterns: Nadaraya-
Watson kernel + geometric chart patterns).
