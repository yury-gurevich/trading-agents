<!-- Agent: planning | Role: sprint handover -->
# Sprint 30 — P11 analyst: technical scoring core (RSI/MACD/Bollinger/SMA/EMA)

**Status:** planned · **Branch:** `sprint-30-p11-analyst-technical-core` · **Build phase:** P11 · **Effort: L**

## Goal

Replace the analyst's placeholder 3-component heuristic (scanner-prior + lookback-momentum +
short/long MA) with a real **technical scoring engine**: five deterministic indicators (RSI,
MACD, Bollinger-band position, SMA-distance, EMA crossover), each scored on a 0–100 band-rule
scale, averaged into a composite `technical_score`. Indicators degrade **per-indicator** when
history is short (neutral 50), so the engine is safe on thin fixtures and meaningful on real
history. Establishes the modular `indicators` + `technical_rules` architecture that later P11
sprints extend (oscillators, volume/event signals, patterns, then fundamental and sentiment).

**No contract change.** `Recommendation` already carries `technical_score` (and nullable
`sentiment_score`/`fundamental_score` for later). This sprint enriches how `technical_score`
is computed; the message boundary is unchanged.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/build-plan.md` **P11 — Decision-logic
  depth** (this is its first sprint).
- **No pandas / numpy in this repo** (confirmed — `pyproject.toml` has neither). Implement every
  indicator in **pure Python** over `tuple[OHLCVBar, ...]`. This is a deterministic rewrite, not
  a library port. Bars are `contracts.provider.OHLCVBar` with `bar_date, open, high, low, close,
  volume` (all present; `close`/`volume` are what you need here).
- **Current integration point** (`agents/analyst/domain/scoring.py`): `score_candidate(candidate,
  bars, settings) -> ScoreBreakdown`. Keep this signature and the `ScoreBreakdown` shape
  (`technical_score: float` in [0,1], `confidence: float`, `metrics: dict[str,float]`,
  `rejection_reason: str | None`). `agents/analyst/domain/recommend.py::decide` reads only
  `score.technical_score`, `score.confidence`, `score.rejection_reason` — do not change it (you
  may update the rationale wording in `decide`).
- **Confidence model stays:** `confidence = _bounded(settings.confidence_floor + technical *
  settings.confidence_span)` with the existing `confidence_floor=0.30`, `confidence_span=0.60`.
- **The scanner candidate-prior and the momentum/MA heuristic are removed.** The analyst now
  scores on its own technical evidence (the scanner already decided *which* candidates arrive;
  the analyst's job is to score them). This is a deliberate behaviour change — existing analyst
  and P2-slice tests that asserted specific scores/recommendations **will need their fixtures and
  expectations updated this sprint** (seed enough bars; assert against the new engine). That test
  maintenance is in scope.
- **Score scale convention** (keep it faithful and testable): each indicator rule returns a
  **0–100** sub-score; `score_technical` = arithmetic mean of the **available** sub-scores (0–100);
  `technical_score = score_technical / 100.0` → [0,1]. If **no** indicator is computable (too few
  bars) → `technical_score = 0.50` (neutral) with a `metrics["indicators_available"] = 0` flag.
  Only the existing near-empty guard (`len(bars) < min_history_bars`) yields a rejection.

### Indicator formulas (implement exactly — self-contained)

All operate on `closes = [bar.close for bar in bars sorted by bar_date]` (ascending). "EMA" is
the standard exponential moving average with multiplier `k = 2/(period+1)`, seeded with the
simple mean of the first `period` values.

- **RSI(period=14):** over the last `period+1` closes, split consecutive deltas into gains/losses;
  `avg_gain = mean(gains)`, `avg_loss = mean(losses)` (absolute). `RS = avg_gain/avg_loss`;
  `RSI = 100 - 100/(1+RS)`. If `avg_loss == 0` → RSI = 100. Needs ≥ `period+1` closes.
- **MACD(12,26,9):** `macd_line = EMA(closes,12) - EMA(closes,26)`; `signal = EMA(macd_series,9)`
  where `macd_series` is the per-bar MACD over the tail; `histogram = macd_line - signal`. Needs
  ≥ `slow + signal` closes (≈ 35) to have a stable signal; below that → indicator unavailable.
- **Bollinger position(window=20, sigma=2.0):** `mid = SMA(closes,20)`; `sd = population stdev of
  the last 20 closes`; `upper = mid + 2*sd`, `lower = mid - 2*sd`; `position = (close - lower)/
  (upper - lower)`, clamped to [0,1]. If `upper == lower` → 0.5. Needs ≥ 20 closes.
- **SMA-distance(period=200):** `sma = SMA(closes,200)`; `distance_pct = (close - sma)/sma * 100`.
  Needs ≥ 200 closes.
- **EMA crossover(short=20, long=50):** `spread_pct = (EMA(closes,20) - EMA(closes,50))/
  EMA(closes,50) * 100`. Needs ≥ `long` closes.

### Indicator scoring rules (0–100; implement exactly)

- **RSI:** `<30 → 80` (oversold, bullish), `<50 → 65`, `<70 → 50`, `else → 25` (overbought).
- **MACD:** `(macd>0 and hist>0) → 75`, `(hist>0) → 60`, `(macd<0 and hist<0) → 25`, `else → 45`.
- **Bollinger position:** `<0.30 → 75` (near lower band), `<0.70 → 50`, `else → 30` (near upper).
- **SMA-distance:** `>5 → 75`, `>0 → 60`, `>-5 → 40`, `else → 20` (percent above/below SMA200).
- **EMA crossover:** `spread_pct >1 → 75`, `>0 → 60`, `>-1 → 40`, `else → 25`.

## Part A — Settings

`agents/analyst/settings.py`:

- **Bump** `lookback_days` `7 → 260` (why: "Indicators need up to ~200 trading days of history
  (SMA200); a ~260-calendar-day window yields enough daily bars."). Keep `ge`/`le` bounds wide
  enough (`le=512`).
- **Keep** `min_history_bars` (the near-empty rejection guard), `confidence_floor`,
  `confidence_span`.
- **Remove** the now-unused heuristic tunables: `short_ma_bars`, `long_ma_bars`,
  `candidate_score_weight`, `momentum_weight`, `trend_weight`, `score_scale`, `trend_scale`
  (and all references in `scoring.py`).
- **Add** indicator tunables, each with a justified `why` and bounds:
  `rsi_period=14` (ge=2,le=100), `macd_fast=12`, `macd_slow=26`, `macd_signal=9`,
  `bollinger_window=20`, `bollinger_sigma=2.0` (ge=0.5,le=4.0), `sma_long_period=200`
  (ge=20,le=400), `ema_short_period=20`, `ema_long_period=50`. Validate `macd_fast < macd_slow`
  and `ema_short_period < ema_long_period` (a pydantic `model_validator`, mirroring
  `contracts/common.Window`).

Watch `settings.py` size; if it exceeds ~150L, that is acceptable up to 200, but prefer concise
`why` strings.

## Part B — Indicator calculations

`agents/analyst/domain/indicators.py` — ≤ 150L (split into `indicators_momentum.py` +
`indicators_trend.py` if it would exceed 150).

```python
"""Pure-Python technical indicator calculations.

Agent: analyst
Role: compute RSI/MACD/Bollinger/SMA/EMA from close-price history; no I/O, no pandas.
External I/O: none.
"""
```

Provide small private helpers `_ema(values, period) -> float`, `_ema_series(values, period) ->
list[float]`, `_sma(values, period) -> float`, `_pstdev(values) -> float`, and the five public
calcs, each returning `float | None` (`None` when there is insufficient history):
`rsi(closes, period)`, `macd(closes, fast, slow, signal) -> tuple[float,float,float] | None`
(line, signal, histogram), `bollinger_position(closes, window, sigma)`,
`sma_distance(closes, period)`, `ema_crossover_spread(closes, short, long)`.

Keep them total and deterministic — no exceptions on short input; return `None`.

## Part C — Technical scoring rules + composite

`agents/analyst/domain/technical_rules.py` — ≤ 100L.

```python
"""Indicator scoring rules and the technical composite.

Agent: analyst
Role: map indicator values to 0-100 sub-scores and average the available ones.
External I/O: none.
"""
```

- One `score_*` per indicator implementing the exact bands above (return `int`/`float` 0–100).
- `score_technical(closes, settings) -> tuple[float, dict[str, float]]`: compute each indicator
  (skipping `None`), score the available ones, return `(mean_subscore_0_100, metrics)` where
  `metrics` records each computed indicator value and sub-score plus `indicators_available`
  (count). If none available → `(50.0, {"indicators_available": 0.0})`.

## Part D — Rewire `score_candidate`

`agents/analyst/domain/scoring.py` — keep ≤ 150L:

- Sort bars, keep the `len(rows) < settings.min_history_bars` → rejection guard.
- `closes = [bar.close for bar in rows]`; `raw, tmetrics = score_technical(closes, settings)`;
  `technical = _bounded(raw / 100.0)`.
- `confidence = _bounded(settings.confidence_floor + technical * settings.confidence_span)`.
- `metrics = {"history_bars": float(len(rows)), "technical_score": technical, "confidence":
  confidence, **tmetrics}`.
- Return `ScoreBreakdown(technical_score=technical, confidence=confidence, metrics=metrics)`.
- Delete `_weighted_score` and `_trend_component` (and the `candidate.score`/momentum usage).
  `score_candidate` no longer reads `candidate.score` — update the signature only if it becomes
  unused (it may still take `candidate` for the ticker/metrics; keep it for call-site stability).
- Update `recommend.decide`'s rationale wording to reference the technical indicators rather than
  "scanner strength, momentum, and trend".

## Part E — Tests

### E1. `agents/analyst/tests/test_indicators.py` — ≤ 120L

Golden-value tests over hand-checked series (compute the expected by hand and pin it):

- `rsi`: a strictly rising series → RSI near 100; a known mixed series → a pinned value
  (assert with `pytest.approx`, tol 1e-6 on your hand-computed number). `< period+1` closes → `None`.
- `macd`: a rising series → `histogram > 0`, `line > 0`; insufficient closes → `None`.
- `bollinger_position`: a flat series → mid band, position `0.5`; last close at the high →
  near 1.0; `< window` → `None`.
- `sma_distance`: close above a 200-flat SMA → positive pct; `< 200` closes → `None`.
- `ema_crossover_spread`: rising series → positive spread; `< long` closes → `None`.

### E2. `agents/analyst/tests/test_technical_rules.py` — ≤ 90L

Threshold-boundary tests for each `score_*` (e.g. RSI `29.9 → 80`, `30 → 65`? — pin the exact
boundary you implement and keep `<`/`<=` consistent with the spec: spec uses `<30 → 80`, so
`30 → 65`). `score_technical`: with a series rich enough for all five → `indicators_available ==
5` and the mean matches the hand-computed average; with a 25-bar series → only RSI/MACD/Bollinger
available (`indicators_available == 3`); with a 3-bar series → `(50.0, {"indicators_available":0})`.

### E3. `agents/analyst/tests/test_scoring.py` — update

Rewrite the existing scoring assertions for the new engine: a sufficient-history candidate →
`technical_score` equal to the hand-computed composite/100, confidence = floor + that*span;
a thin-history candidate → `technical_score == 0.5`; a near-empty candidate (`< min_history_bars`)
→ `rejection_reason == "insufficient_market_history"`.

### E4. Update analyst slice / integration tests + fixtures

Find every test that drives `analyze` or asserts analyst recommendations/scores (e.g. the P2
slice integration test, `agents/analyst/tests/*`, and any `tests/` pipeline test). Seed enough
bars for the indicators under test and update expected scores/confidence to the new engine.
**Do not weaken assertions to "any value"** — pin the new expected numbers. Run the full suite;
fix every break this sprint (the behaviour change is intended and bounded to the analyst score).

## Steps

1. Branch `sprint-30-p11-analyst-technical-core` off `main`.
2. **Part A** settings (bump lookback, add indicator tunables, remove old). `make ci` will fail
   on `scoring.py` references until Part D — that's expected; keep moving.
3. **Part B** indicators (+ unit tests E1 as you go — fastest feedback).
4. **Part C** technical_rules (+ E2).
5. **Part D** rewire scoring; update `decide` rationale.
6. **Part E** update scoring + slice/integration tests and fixtures. `make ci` green.
7. **Line-count check:** `wc -l agents/analyst/domain/*.py agents/analyst/settings.py`. All
   < 200L; split indicators if needed.
8. Push; hand back.

## Acceptance criteria

- All five indicators compute correct, hand-verified values on golden fixtures and return `None`
  (not an exception) on insufficient history.
- Each scoring rule maps to the exact 0–100 bands specified; `score_technical` averages only the
  available sub-scores and is neutral (50) when none are available.
- `score_candidate` produces `technical_score ∈ [0,1]` from the composite; `confidence = floor +
  technical*span`; the near-empty rejection still fires.
- `lookback_days` default is 260; the removed heuristic tunables are gone with no dangling
  references.
- The analyst contract is unchanged; `decide` still consumes `ScoreBreakdown` unchanged.
- Every analyst and pipeline test updated to the new engine with **pinned** expected values
  (no weakened assertions); `make ci` green at/above the coverage floor (100.00).
- Import-linter 4/4 kept (analyst imports only `kernel` + `contracts`).

## Out of scope (do NOT build this sprint — later P11 sprints)

- **Oscillators & volatility:** ATR, Stochastic, Williams %R, Choppiness (next P11 sprint).
- **Volume/event & patterns:** OBV, golden cross, calendar signals, Nadaraya-Watson kernel,
  geometric patterns.
- **Fundamental scoring** (P/E, ROE, margins, leverage, growth) and **sentiment scoring** —
  **both are blocked on provider data the system does not yet collect** (the provider supplies
  OHLCV + VIX only). These need a provider data-feed extension first; flag to the planning agent,
  do not stub fake fundamentals/sentiment here.
- **Relative-strength blend** and **signal-diversity selection** (`select_top_signals`).
- **Confidence-level buckets** (high/med/low) and **beta** (a scanner-side gap, separate sprint).
- Any change outside the analyst package or its tests.

## P11 sequencing (planning agent tracks; see memory `v1-deterministic-port-gaps.md`)

P11 order after this sprint: (2) oscillators + volatility, (3) volume/event + patterns,
(4) **provider fundamental/sentiment data feed** (prerequisite), (5) fundamental + sentiment
scoring + relative-strength + signal-diversity selection. Then the PM, scanner, and reporter
gaps (reward/risk + sector caps; beta + earnings filter; profit-factor + expectancy) as their
own small sprints.

## Handback report (paste into PR / reply)

- Confirm no contract change; `ScoreBreakdown`/`decide` interface unchanged.
- The EMA-crossover periods used (20/50 unless you justify otherwise) and any boundary `<` vs `<=`
  decisions in the scoring rules.
- Which tests/fixtures needed updating and the new pinned expected scores (one or two examples).
- Final line counts: indicators module(s), technical_rules.py, scoring.py, settings.py.
- New coverage % and floor; total test count.
- Anything in the formulas/thresholds that was ambiguous and how you resolved it.

The planning agent reviews, merges to `main`, and plans the next P11 sprint (oscillators +
volatility).
