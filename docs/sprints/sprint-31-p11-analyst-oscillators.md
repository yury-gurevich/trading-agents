<!-- Agent: planning | Role: sprint handover -->
# Sprint 31 — P11 analyst: oscillators + volatility (ATR/Stochastic/Williams %R/Choppiness)

**Status:** planned · **Branch:** `sprint-31-p11-analyst-oscillators` · **Build phase:** P11 · **Effort: M**

## Goal

Extend the analyst technical engine (shipped Sprint 30) with four **range-based** indicators —
ATR (volatility), Stochastic oscillator, Williams %R, and the Choppiness Index — each scored on
0–100 bands and folded into the same composite `technical_score`. These need high/low/close,
which the existing `OHLCVBar` already carries, so **no provider change**. Same architecture and
graceful-degradation contract as Sprint 30: each indicator returns `None` on short history; the
composite averages only the available sub-scores.

**No contract change.** This only deepens how `technical_score` is computed.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/sprints/sprint-30-p11-analyst-technical-core.md`
  (the engine you extend — same conventions, formulas-as-spec, pinned-test discipline).
- **Shipped code you build on (read it):**
  - `agents/analyst/domain/indicators.py` (107L) — pure-Python momentum/trend calcs returning
    `float | None`; helpers `_mean`, `_sma`, `_pstdev`, `_ema`, `_ema_series`. The new range
    indicators go in a **new** `indicators_range.py` (keep `indicators.py` untouched; it is near
    the warn band).
  - `agents/analyst/domain/technical_rules.py` (127L) — `score_*` band rules + `score_technical`
    + `_indicator_scores`. **`score_technical` currently takes `closes: list[float]`** and
    `scoring.py` passes `closes`. You will change it to take the **sorted bars** (it needs
    high/low now) and derive `closes`/`highs`/`lows` once. The four new band rules go in a **new**
    `technical_rules_range.py` to keep both rule modules < 150L.
  - `agents/analyst/domain/scoring.py` (65L) — `score_candidate` already sorts `rows`; change its
    one call from `score_technical(closes, settings)` to `score_technical(rows, settings)` and drop
    the now-unneeded local `closes`.
  - `agents/analyst/settings.py` (122L) — indicator periods are justified `tunable(...)`; band
    cut-points are fixed module constants in the rule files (keep this split). Add the new periods
    here.
- **Pure Python only** (no pandas/numpy). Reuse the `_mean`/`_sma` style; you may import the
  shared helpers from `indicators.py` or re-declare tiny ones — do not add a dependency.
- **Bar fields:** `OHLCVBar` has `high`, `low`, `close` (all present). Work over the
  bars sorted ascending by `bar_date` (as `score_candidate` already does).

### Indicator formulas (implement exactly — self-contained)

Let `bars` be sorted ascending; `highs`, `lows`, `closes` the parallel lists. "True range" at
index `i ≥ 1`: `TR_i = max(high_i - low_i, |high_i - close_{i-1}|, |low_i - close_{i-1}|)`.

- **ATR(period=14):** mean of the **last `period`** TR values. Needs `≥ period + 1` bars (TR
  needs a previous close). Returns ATR in price units (`float`), else `None`.
- **Stochastic(%K period=14, %D period=3):** over the last `k` bars `hh = max(highs[-k:])`,
  `ll = min(lows[-k:])`; `%K = (close - ll)/(hh - ll) * 100`, and `%K = 50.0` when `hh == ll`.
  `%D = mean of the last d %K values` (compute %K at each of the last `d` bar positions, each over
  its own trailing `k` window). Needs `≥ k + d - 1` bars. Returns `(%K, %D)` else `None`.
- **Williams %R(period=14):** `hh = max(highs[-period:])`, `ll = min(lows[-period:])`;
  `%R = (hh - close)/(hh - ll) * -100`, and `%R = -50.0` when `hh == ll`. Range [-100, 0]. Needs
  `≥ period` bars. Returns `float` else `None`.
- **Choppiness(period=14):** `sum_tr = sum of the last period TR values`; `hh = max(highs[-period:])`,
  `ll = min(lows[-period:])`, `rng = hh - ll`. `CI = 100 * log10(sum_tr / rng) / log10(period)`.
  Needs `≥ period + 1` bars; if `rng == 0` (or `sum_tr == 0`) → `None`. Returns `float` (≈0–100).
  Use `math.log10`.

### Scoring rules (0–100; implement exactly)

- **ATR%** (`atr_pct = ATR / last_close * 100`): `<2 → 70`, `<4 → 55`, `else → 35` (lower
  volatility scores higher).
- **Stochastic** (`%K`, `%D`): `(%K<20 and %D<20) → 80`, `(%K<20) → 65`, `(%K>80 and %D>80) → 20`,
  `(%K>80) → 35`, `else → 50`. *(Check the two "both" branches before the single-`%K` branches, in
  this order.)*
- **Williams %R:** `< -80 → 75` (oversold), `> -20 → 25` (overbought), `else → 50`.
- **Choppiness:** `< 38.2 → 75` (trending — favourable), `> 61.8 → 30` (choppy), `else → 50`.
  (38.2 / 61.8 are the standard Fibonacci bands; named constants, not tunables.)

Use strict `<` / `>` exactly as written, consistent with Sprint 30's boundary convention.

## Part A — Settings

`agents/analyst/settings.py` — add justified, bounded `tunable(...)` periods:
`atr_period=14` (ge=2, le=100), `stoch_k_period=14` (ge=2, le=100), `stoch_d_period=3`
(ge=1, le=20), `williams_period=14` (ge=2, le=100), `choppiness_period=14` (ge=2, le=100).
No validators needed beyond the bounds. Keep `why` strings concise (the file is at 122L).

## Part B — Range indicators

`agents/analyst/domain/indicators_range.py` — ≤ 130L.

```python
"""Pure-Python range-based indicators (ATR, Stochastic, Williams %R, Choppiness).

Agent: analyst
Role: compute volatility/oscillator indicators from high/low/close history; no I/O.
External I/O: none.
"""
```

Take parallel `list[float]` inputs (`highs`, `lows`, `closes`) — or a `list[OHLCVBar]` and extract
internally; pick one and be consistent. Provide a private `_true_ranges(highs, lows, closes) ->
list[float]` helper (shared by ATR and Choppiness). Public:
`atr(highs, lows, closes, period) -> float | None`,
`stochastic(highs, lows, closes, k, d) -> tuple[float, float] | None`,
`williams_r(highs, lows, closes, period) -> float | None`,
`choppiness(highs, lows, closes, period) -> float | None`. Total functions; never raise on short
input — return `None`.

## Part C — Range scoring rules

`agents/analyst/domain/technical_rules_range.py` — ≤ 90L.

```python
"""Range-indicator scoring rules and their composite contribution.

Agent: analyst
Role: map ATR/Stochastic/Williams/Choppiness values to 0-100 sub-scores.
External I/O: none.
"""
```

- Named band constants (mirroring `technical_rules.py`'s style) + `score_atr(atr_pct)`,
  `score_stochastic(k, d)`, `score_williams(value)`, `score_choppiness(value)`.
- `range_indicator_scores(highs, lows, closes, settings) -> list[tuple[str, float, float]]` —
  compute each indicator (skip `None`), score it, return `(name, value, score)` triples. For
  Stochastic, record `%K` as the value (e.g. name `"stochastic_k"`) and pass both `%K`,`%D` to the
  rule. Return only the available ones.

## Part D — Fold into the composite

`agents/analyst/domain/technical_rules.py`:

- Change `score_technical` to accept the **sorted bars** (rename param `rows`/`bars:
  list[OHLCVBar]`). Inside, derive `closes`/`highs`/`lows` once.
- Keep the existing momentum/trend scoring (rename the current `_indicator_scores(closes, …)` to
  `_momentum_scores(closes, …)` if clearer). Call
  `range_indicator_scores(highs, lows, closes, settings)` from `technical_rules_range.py` and
  **concatenate** its triples with the momentum triples before averaging.
- `metrics` accumulates every `(name, value)` and `(name_score)` exactly as today;
  `indicators_available` is the total count across both groups.

`agents/analyst/domain/scoring.py`:

- Call `score_technical(rows, settings)` (pass the sorted bars). Remove the local `closes`
  construction if it becomes unused. Nothing else changes — `ScoreBreakdown`/`decide` untouched.

Confirm each touched module stays < 150L (split further only if needed; all must be < 200).

## Part E — Tests

### E1. `agents/analyst/tests/test_indicators_range.py` — ≤ 120L

Golden, hand-verified values over fixtures **with real high/low spread** (not flat bars):

- `atr`: a known H/L/C series → a pinned ATR (`pytest.approx`); `< period+1` bars → `None`.
- `stochastic`: last close at the window high → `%K == 100`; at the low → `%K == 0`; `hh==ll`
  flat window → `%K == 50.0`; `< k+d-1` bars → `None`.
- `williams_r`: close at window high → `0.0`; at low → `-100.0`; flat → `-50.0`; short → `None`.
- `choppiness`: a strongly trending series → low CI; a mean-reverting/oscillating series → high
  CI (pin both hand-computed); `rng==0` → `None`; `< period+1` → `None`.

### E2. `agents/analyst/tests/test_technical_rules_range.py` — ≤ 90L

Threshold-boundary tests for each rule (e.g. ATR% `1.99 → 70`, `2.0 → 55`; Stochastic
`(%K=19,%D=19) → 80`, `(%K=19,%D=50) → 65`, `(%K=85,%D=85) → 20`, `(%K=85,%D=50) → 35`,
`(%K=50,%D=50) → 50`; Williams `-80 → 50` (boundary: `< -80` is false), `-81 → 75`, `-19 → 25`;
Choppiness `38.2 → 50`, `38.1 → 75`, `61.9 → 30`). Pin the exact boundaries you implement.

### E3. Update `agents/analyst/tests/test_technical_rules.py` + `test_analyst_domain.py`

The composite now includes up to four more indicators, so the Sprint-30 pinned cases change:

- The "all indicators" case (a long series with real H/L) → `indicators_available == 9` (5 momentum
  + 4 range), and the mean recomputed across all nine.
- The mid-length case → recount which of the nine have enough history (e.g. a 40-bar series:
  RSI, MACD, Bollinger, ATR, Stochastic, Williams, Choppiness available; SMA200 and EMA-50 not →
  `indicators_available == 7`) and re-pin the composite.
- Keep the "no indicators" (thin) case → still `(50.0, {"indicators_available": 0.0})`.

**Recompute and re-pin every changed expected value by hand — do not weaken to "any value".**
Note: fixtures whose high==low==close make ATR=0 (→ score 70), Stochastic/%K=50, Williams=-50,
and Choppiness `None` (rng=0). For meaningful range-indicator coverage, give those test fixtures a
real H/L spread.

### E4. Confirm downstream pipeline tests still pass unchanged

The thin ~4-bar pipeline fixtures degrade all nine indicators → neutral 0.5 → confidence 0.60,
which still clears the strict-`<` regime floor (as in Sprint 30). Run the whole suite; if any
pipeline test moved, it is because a fixture has enough bars — re-pin it, don't weaken it.

## Steps

1. Branch `sprint-31-p11-analyst-oscillators` off `main`.
2. **A** settings → **B** `indicators_range.py` (+ E1) → **C** `technical_rules_range.py` (+ E2).
3. **D** fold into `score_technical` + `scoring.py`. `make ci`.
4. **E3/E4** update + re-pin analyst/pipeline tests. `make ci` green.
5. `wc -l agents/analyst/domain/*.py agents/analyst/settings.py` — all < 200 (< 150 preferred).
6. Push; hand back.

## Acceptance criteria

- ATR, Stochastic, Williams %R, Choppiness compute hand-verified values and return `None` (never
  raise) on insufficient history or degenerate (`hh==ll` / `rng==0`) windows.
- Each new rule maps to the exact 0–100 bands; `score_technical` averages all available sub-scores
  across momentum + range groups; `indicators_available` reflects the true count.
- `score_candidate`/`ScoreBreakdown`/`decide` and the analyst contract are unchanged.
- All analyst and pipeline tests pass with **pinned** expected values; `make ci` green at/above the
  coverage floor (100.00).
- Import-linter 4/4 kept; every touched module < 200L (< 150 where the spec targets it).

## Out of scope (later P11 sprints)

- OBV, golden cross, calendar signals, Nadaraya-Watson kernel, geometric patterns.
- Fundamental + sentiment scoring and relative strength — **blocked on a provider data feed**
  (OHLCV + VIX only today); needs a provider extension sprint first.
- Signal-diversity selection, confidence-level buckets, scanner beta. PM/scanner/reporter gaps.
- Any change outside the analyst package and its tests.

## Handback report (paste into PR / reply)

- Confirm no contract change; `score_technical` signature change (closes → bars) and that
  `scoring.py` is the only caller updated.
- The exact `<`/`>` boundaries and the Stochastic branch order as implemented.
- `indicators_available` counts you re-pinned for the long and mid-length composite cases (the new
  expected numbers).
- Final line counts: `indicators_range.py`, `technical_rules_range.py`, `technical_rules.py`,
  `scoring.py`, `settings.py`.
- New coverage % and floor; total test count.

The planning agent reviews, merges to `main`, and plans the next P11 slice (volume/event +
patterns — OBV, golden cross, Nadaraya-Watson, geometric patterns).
