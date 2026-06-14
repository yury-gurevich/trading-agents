<!-- Agent: planning | Role: sprint handover -->
# Sprint 33 — P11 analyst: patterns, smoothing & calendar (NW kernel / geometric patterns / turnaround)

**Status:** planned · **Branch:** `sprint-33-p11-analyst-patterns` · **Build phase:** P11 · **Effort: L**

## Goal

Add the final three deterministic technical signals from the analyst engine:

1. **Nadaraya-Watson kernel smoother** — a Gaussian-weighted price estimate; score on how far the
   last close deviates from the smoothed line (mean-reversion read).
2. **Geometric chart patterns** — swing-point detection then double top/bottom,
   (inverse) head-and-shoulders, and ascending/descending triangles, each with a confidence.
3. **Calendar "turnaround" signal** — the Monday-after-a-weak-Friday mean-reversion pattern.

Each is scored 0–100 and folded into the same composite `technical_score`, taking the engine from
12 to **15** indicators. All use data the `OHLCVBar` already carries (`close`, `high`, `low`,
`bar_date`) — **no provider change, no contract change**.

This is the heavier slice that Sprints 30–32 deliberately deferred (`docs/sprints/sprint-32-…`
"Out of scope"). It is materially more involved than the prior batches: it ports geometric
pattern recognition and introduces **calendar-dependence** into the composite, plus a **settings
split** (the file is at the 200-line cap). Budget accordingly.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/sprints/sprint-32-p11-analyst-volume-event.md`
  (the immediately-prior slice — identical structure: new `indicators_*` + `technical_rules_*`
  companion modules folded into `score_technical`).
- **Shipped code you extend (read it):**
  - `agents/analyst/domain/technical_rules.py` (144L) — `score_technical(bars, settings)` already
    derives `closes`/`highs`/`lows`/`volumes` and concatenates `_momentum_scores` +
    `range_indicator_scores` + `event_indicator_scores`. You add a **dates** extraction and a
    fourth group `pattern_indicator_scores(closes, highs, lows, dates, settings)`.
  - `agents/analyst/domain/technical_rules_range.py` / `technical_rules_event.py` — the exact
    companion pattern to mirror (named band constants; a `*_indicator_scores(...)` that computes
    each indicator, skips `None`, returns `(name, value, score)` triples).
  - `agents/analyst/domain/indicators.py` — reuse `_mean`, `_sma` style helpers (do not re-import
    pandas/numpy).
  - `agents/analyst/settings.py` (**178L — at the warn band, will cross 200 with this slice's
    tunables**). See Part A: a settings split is required, not optional.
  - `contracts/provider.py` — `OHLCVBar` carries `bar_date: date` (a stdlib `datetime.date`) and
    `volume: int`. Use `bar_date.weekday()` (Mon=0 … Fri=4) for the calendar signal — **no
    pandas**.
- **Pure Python only** (no pandas/numpy). Work over the ascending-sorted bars (the caller sorts).
- **Graceful degradation unchanged:** each indicator returns `None` on insufficient history (and,
  for the calendar signal, when the day does not apply — see the design decision below); the
  composite averages only the available sub-scores.

### Indicator formulas (implement exactly — self-contained, ported from the reference engine)

Let `closes`, `highs`, `lows` be parallel lists over the ascending bars; `dates` the parallel
list of each bar's `bar_date`.

- **Nadaraya-Watson(`bandwidth=8.0`, `lookback=50`)** → `float | None` (the deviation %):
  - `n = min(lookback, len(closes))`; **`None`** if `n < 10`.
  - `prices = closes[-n:]`; `target = n - 1` (the last index in the window).
  - `weights[i] = exp(-0.5 * ((i - target) / bandwidth) ** 2)` for `i in range(n)` (`math.exp`).
  - `wsum = sum(weights)`; **`None`** if `wsum == 0.0` (defensive; a Gaussian never is, but guard).
  - `smoothed = sum(w * p) / wsum`; **`None`** if `smoothed == 0.0`.
  - return `deviation_pct = (prices[-1] - smoothed) / smoothed * 100.0`.
- **Swing points(`min_swing_pct=2.0`)** → `list[tuple[int, float, str]]` (index, price, "high"/"low"):
  - `[]` if `len(closes) < 5`.
  - For each `index` in `2 .. len-3` (inclusive): a **swing high** if `highs[index]` strictly
    exceeds all four neighbours `{index-2, index-1, index+1, index+2}`; a **swing low** if
    `lows[index]` is strictly below all four. Append `(index, price, "high"|"low")`.
  - If no swings or `closes[-1] == 0` → return the raw swings. Otherwise keep only swings whose
    price is at least `min_swing_pct * 0.5` percent away from the last close:
    `abs(price - last) / last * 100 >= min_swing_pct * 0.5`.
- **Geometric patterns(`lookback=60`, `min_swing_pct=2.0`)** → `tuple[str, float] | None` (name, conf):
  - `n = min(lookback, len(closes))`; **`None`** if `n < 20`. Take the last-`n` windows of
    close/high/low, find swing points, **`None`** if `< 3` swings.
  - `tolerance = min_swing_pct / 100.0`; `last = close_window[-1]`. Test in this order, return the
    first match:
    - **Double top:** last two swing **highs** match (`abs(a-b)/a < tolerance` **and** index gap
      `>= 5`) **and** `last < second_high * (1 - tolerance)` →
      `("double_top", round(min(1 - abs(a-b)/a/tolerance, 0.85), 2))`.
    - **Double bottom:** symmetric on swing **lows**, `last > second_low * (1 + tolerance)` →
      `("double_bottom", round(min(1 - abs(a-b)/a/tolerance, 0.85), 2))`.
    - **Head & shoulders:** last three swing highs `(s1, head, s2)` with `head > s1`, `head > s2`,
      `abs(s1-s2)/s1 < tolerance`, and `last < min(s1, s2)` → `("head_and_shoulders", 0.70)`.
    - **Inverse H&S:** symmetric on swing lows, `last > max(s1, s2)` →
      `("inverse_head_and_shoulders", 0.70)`.
    - **Ascending triangle:** last two highs flat (`abs(a-b)/a < tolerance`) **and** last two lows
      rising (`low2 > low1 * (1 + tolerance*0.5)`) → `("ascending_triangle", 0.65)`.
    - **Descending triangle:** last two lows flat **and** last two highs falling
      (`high2 < high1 * (1 - tolerance*0.5)`) → `("descending_triangle", 0.65)`.
    - else `None`.
- **Turnaround signal** → `bool | None` (always-emit — see the design decision below):
  - **`None`** if `len(closes) < 3` (the only unavailability condition).
  - If `dates[-1].weekday() != 0` (not a Monday) → return `False` (emitted as neutral, not skipped).
  - On a Monday: walk back up to 4 prior bars to find the most recent **Friday** (`weekday() == 4`);
    if found, return `closes[-1] < friday_close` (the prior Friday's close). If no Friday found →
    `False`.

### Scoring rules (0–100; implement exactly — strict `<` / `>`)

- **NW kernel** (`deviation_pct`): `< -1.0 → 70` (price below the smooth line, mean-reversion
  bullish), `> 1.0 → 30` (overextended above, bearish), else `→ 50`.
- **Geometric pattern** (`name`, `conf`): bullish set
  `{"double_bottom", "inverse_head_and_shoulders", "ascending_triangle"}` → `50 + conf * 30`; the
  bearish remainder (`double_top`, `head_and_shoulders`, `descending_triangle`) → `50 - conf * 30`.
- **Turnaround** (`is_signal`): `True → 75`, `False → 50`.

### Design decision — calendar gating (decided: always-emit)

The turnaround signal is **always-emit**, matching the reference engine: once there are ≥3 bars it
contributes on **every** day — `75` on a true Monday turnaround, `50` otherwise (including all
non-Monday days). It returns `None` **only** below 3 bars.

Consequence the coding agent must plan for: this injects a sub-score (usually a neutral `50`) into
*every* fixture with ≥3 bars, which pulls those composites toward neutral. The re-pin in F4/F5 is
therefore **wider** than the prior three slices — recompute every affected composite by hand
(see F4). This is the intended, accepted behavior, not a bug; do **not** silently switch to
gating-on-Monday to shrink the re-pin.

## Part A — Settings split + new tunables

`settings.py` is at **178L**; four new tunables push it past the 200-line cap. Split first:

1. Create `agents/analyst/settings_indicators.py` with a base class holding **all indicator
   period/window tunables** (`rsi_period` through `rsi2_period`, and the four new ones below):

   ```python
   """Analyst indicator-period and window tunables (the calculation knobs).

   Agent: analyst
   Role: own the justified periods/windows the technical indicators are computed over.
   External I/O: process environment and the .env file.
   """
   ```

   Define `class _IndicatorSettings(AgentSettings):` (leading underscore — never instantiated
   directly). Move the existing indicator tunables here verbatim (keep every `why`/bound).
2. In `settings.py`, make `class AnalystSettings(_IndicatorSettings):` and keep only
   `lookback_days`, `min_history_bars`, `confidence_floor`, `confidence_span`, the
   `model_config` (`env_prefix="ANALYST_"`, `frozen=True`), and the `_spans_are_ordered`
   validator (it references inherited `macd_*`/`ema_*` fields — works under inheritance).
   All fields stay reachable as `AnalystSettings(...)` attributes, so **no caller changes** and
   `test_analyst_settings.py` should pass unchanged (re-pin only if it asserts a literal line
   count or field-definition location — it should not).
3. Add four justified, bounded `tunable(...)` in `_IndicatorSettings`:
   - `nw_bandwidth=8.0` (ge=0.5, le=50.0) — Gaussian kernel width.
   - `nw_lookback=50` (ge=10, le=200, unit="bars") — kernel window.
   - `pattern_lookback=60` (ge=20, le=200, unit="bars") — swing-search window.
   - `pattern_min_swing_pct=2.0` (ge=0.5, le=10.0) — swing significance / matching tolerance.

   The turnaround signal needs **no tunable** (it reads `bar_date.weekday()`).

**Size watch:** confirm `settings_indicators.py` < 200L (≈150) and `settings.py` < 100L after the
split.

## Part B — Kernel + calendar indicators

`agents/analyst/domain/indicators_kernel.py` — ≤ 70L.

```python
"""Pure-Python kernel smoother and calendar signal (NW estimate, turnaround).

Agent: analyst
Role: compute the Nadaraya-Watson deviation and the Monday turnaround flag; no I/O, no numpy.
External I/O: none.
"""
```

Provide `nadaraya_watson(closes, bandwidth, lookback) -> float | None` (returns the deviation %)
and `turnaround_signal(closes, dates) -> bool | None`. Import `math` for `exp`; take `dates` as
`list[date]`. Never raise — return `None`.

## Part C — Geometric pattern indicators

`agents/analyst/domain/indicators_pattern.py` — ≤ 200L (target < 170; if it would cross ~190L,
split swing-finding into `indicators_swing.py` and flag it — do **not** otherwise refactor).

```python
"""Pure-Python geometric chart-pattern detection (swing points → patterns).

Agent: analyst
Role: find swing highs/lows and classify double/H&S/triangle patterns; no I/O, no pandas.
External I/O: none.
"""
```

Public `find_swing_points(closes, highs, lows, min_swing_pct) -> list[tuple[int, float, str]]` and
`geometric_patterns(closes, highs, lows, lookback, min_swing_pct) -> tuple[str, float] | None`.
Keep the private `_double_pattern` / `_shoulder_pattern` / `_triangle_pattern` / `_matching_swings`
helpers mirroring the formulas above. Operate on plain `list`s (slice with `[-n:]`); never raise.

## Part D — Pattern scoring rules

`agents/analyst/domain/technical_rules_pattern.py` — ≤ 100L.

```python
"""Pattern/kernel/calendar scoring rules and their composite contribution.

Agent: analyst
Role: map NW deviation / geometric pattern / turnaround to 0-100 sub-scores.
External I/O: none.
"""
```

- Named band constants (mirror `technical_rules_range.py`): `_NW_DEV_BAND = 1.0`,
  `_NW_BULLISH = 70.0`, `_NW_BEARISH = 30.0`, `_PATTERN_BASE = 50.0`, `_PATTERN_SWING = 30.0`,
  `_TURNAROUND_SIGNAL = 75.0`, `_NEUTRAL = 50.0`, and a
  `_BULLISH_PATTERNS = frozenset({"double_bottom", "inverse_head_and_shoulders", "ascending_triangle"})`.
- `score_kernel(deviation_pct)`, `score_pattern(name, conf)`, `score_turnaround(is_signal: bool)`.
- `pattern_indicator_scores(closes, highs, lows, dates, settings) -> list[tuple[str, float, float]]`:
  - NW: `("nw_deviation_pct", dev, score_kernel(dev))` when `nadaraya_watson(...)` is not `None`.
  - Pattern: `("geometric_pattern", conf, score_pattern(name, conf))` when
    `geometric_patterns(...)` is not `None`. *(The flat float metrics dict can't carry the pattern
    name; the directional score encodes it — note this in the handback.)*
  - Turnaround: `("turnaround", 1.0 if sig else 0.0, score_turnaround(sig))` when
    `turnaround_signal(...)` is not `None`.
  - Skip any that returned `None`. Import `indicators_kernel` and `indicators_pattern`.

## Part E — Fold into the composite

`agents/analyst/domain/technical_rules.py`:

- In `score_technical`, add `dates = [bar.bar_date for bar in bars]` (alongside the existing
  extractions).
- Concatenate a fourth group onto the existing three: append
  `pattern_indicator_scores(closes, highs, lows, dates, settings)` to the `triples` list built from
  `_momentum_scores` + `range_indicator_scores` + `event_indicator_scores`. Everything downstream
  (metrics, averaging, `indicators_available`) is unchanged.

`scoring.py` needs **no change** (it already passes the sorted bars). Confirm `technical_rules.py`
stays < 150L after the small addition (~147L expected).

## Part F — Tests

### F1. `agents/analyst/tests/test_indicators_kernel.py` — ≤ 90L

- `nadaraya_watson`: a short hand-built series → a pinned deviation %; `< 10` closes → `None`.
  Include a case where the last close sits above vs below the smoothed line (sign of the deviation).
- `turnaround_signal` (always-emit): a fixture whose last `bar_date` is a **Monday** with
  `monday_close < friday_close` → `True`; Monday with `monday_close >= friday_close` → `False`; a
  **non-Monday** last date → `False` (emitted, not skipped); `< 3` bars → `None` (the only `None`).

### F2. `agents/analyst/tests/test_indicators_pattern.py` — ≤ 120L

- `find_swing_points`: a series with a clear isolated swing high and swing low → the expected
  index/price/kind triples; `< 5` bars → `[]`.
- `geometric_patterns`: purpose-built fixtures that each trigger exactly one of double_top,
  double_bottom, head_and_shoulders, inverse_head_and_shoulders, ascending_triangle,
  descending_triangle → the pinned `(name, conf)`; a smooth/monotone series → `None`; `< 20`
  bars → `None`. (Construct these by hand — getting clean swings is the fiddly part; keep each
  fixture minimal.)

### F3. `agents/analyst/tests/test_technical_rules_pattern.py` — ≤ 90L

Boundary tests for each rule: NW `-1.1 → 70`, `-1.0 → 50`, `1.0 → 50`, `1.1 → 30` (strict band);
pattern `("double_bottom", 0.8) → 74.0`, `("double_top", 0.8) → 26.0`, every name on the correct
side; turnaround `True → 75`, `False → 50`. Plus `pattern_indicator_scores` returning the right
triples / skipping unavailable ones.

### F4. Update `test_technical_rules.py` + `test_analyst_domain.py` (re-pin the composite)

The engine is now up to 15 indicators, and **turnaround always emits at ≥3 bars** — so every
composite fixture with ≥3 bars gains both NW (at ≥10 bars) and turnaround. Note each fixture's last
`bar_date` weekday: a non-Monday last bar makes turnaround `50` (`False`); a Monday makes it `75`
or `50` depending on the prior Friday's close — compute it from the actual fixture dates. Then by
hand:

- **"All available" long case** (the ~220-bar series): NW available (needs ≥10 ✓) **and**
  turnaround available (≥3 ✓); geometric pattern `None` for a smooth/non-patterned fixture →
  `indicators_available == 14` (12 + NW + turnaround). Determine the turnaround value (75 vs 50)
  from the fixture's last-bar weekday, then recompute the mean and derived confidence. *(If the
  existing long fixture happens to form a geometric pattern, recount honestly to 15 and re-pin —
  do not reshape the fixture to avoid it.)*
- **Mid-length case** (~40 bars): NW available (≥10 ✓) **and** turnaround available (≥3 ✓), pattern
  `None` (smooth) → `indicators_available == 11` (was 9). Re-pin the composite + confidence.
- **Thin case unchanged** → `(50.0, {"indicators_available": 0.0})`.

**Recompute and re-pin every changed expected value by hand — do not weaken assertions.** Because
turnaround emits at ≥3 bars, expect to touch any fixture-rich test with ≥3 bars, not just the two
above.

### F5. Confirm downstream pipeline tests still pass unchanged

The ~2-bar pipeline fixtures degrade all 15 indicators (NW needs ≥10, pattern needs ≥20,
turnaround needs ≥3) → neutral 0.5 → confidence 0.60, which still clears the strict-`<` regime
floor — **no pipeline re-pin expected** at 2 bars. But under always-emit, **any** pipeline or
integration fixture with ≥3 bars now also carries turnaround (and NW at ≥10) — run the whole suite
and re-pin (don't weaken) every fixture-rich test that moved.

## Steps

1. Branch `sprint-33-p11-analyst-patterns` off `main`.
2. **A** settings split + tunables. `make ci` (catch the split early).
3. **B** `indicators_kernel.py` (+ F1) → **C** `indicators_pattern.py` (+ F2) →
   **D** `technical_rules_pattern.py` (+ F3).
4. **E** fold into `score_technical`. `make ci`.
5. **F4/F5** re-pin analyst tests; confirm pipeline tests unchanged. `make ci` green.
6. `wc -l agents/analyst/domain/*.py agents/analyst/settings*.py` — all < 200 (< 150 preferred).
7. Push; hand back.

## Acceptance criteria

- NW deviation, swing points, geometric patterns, and the turnaround flag compute hand-verified
  values and return `None` (never raise) on insufficient history / inapplicable day.
- Each rule maps to the exact 0–100 bands; `score_technical` averages all available sub-scores
  across momentum + range + event + pattern groups; `indicators_available` reflects the true count.
- `score_candidate`/`ScoreBreakdown`/`decide` and the analyst contract are unchanged.
- Settings split done: `AnalystSettings` exposes every field as before (no caller change);
  `settings.py` and `settings_indicators.py` both < 200L.
- All analyst + pipeline tests pass with **pinned** expected values; `make ci` green at/above the
  coverage floor (100.00).
- Import-linter kept; every touched/new module < 200L.

## Out of scope (later P11 sprints)

- **Provider data-feed extension** (the next prerequisite): fundamentals + news/sentiment feeds.
  Blocks fundamental + sentiment scoring and relative strength — needs a provider sprint first.
- **Signal-diversity selection**, confidence buckets, scanner beta; PM/scanner/reporter gaps
  (reward/risk + sector caps; beta + earnings exclusion; profit-factor + expectancy). Sequenced in
  the build plan after the provider extension.
- Any change outside the analyst package and its tests.

## Handback report (paste into PR / reply)

- Confirm no contract change and no `scoring.py` change (only `technical_rules.py` gained the
  dates extraction + pattern group), and that turnaround is **always-emit** (the decided behavior:
  `None` only below 3 bars, neutral `50` on every non-signal day).
- The exact `<`/`>` boundaries implemented (NW ±1.0, pattern confidence rounding).
- The re-pinned `indicators_available` counts and composites for the long and mid cases (long: 14,
  or 15 if the fixture formed a geometric pattern; mid: 11), and the turnaround value each took.
- Final line counts: `indicators_kernel.py`, `indicators_pattern.py` (and `indicators_swing.py`
  if you split it), `technical_rules_pattern.py`, `technical_rules.py`, `settings.py`,
  `settings_indicators.py`.
- New coverage % and floor; total test count.

The planning agent reviews, merges to `main`, and plans the next P11 slice (the **provider
data-feed extension** that unblocks fundamental + sentiment scoring + relative strength).
