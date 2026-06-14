<!-- Agent: planning | Role: sprint handover -->
# Sprint 35 — Analyst fundamental scoring (a second pillar over MarketData.fundamentals)

**Status:** planned · **Branch:** `sprint-35-analyst-fundamental-scoring` · **Build phase:** P11 · **Effort: M**

## Goal

Give the analyst a **fundamental pillar** alongside its technical engine. Port `score_fundamental`
— eight valuation/quality/growth metrics (P/E, ROE, net margin, current ratio, P/B, debt/equity,
EPS growth, revenue growth), each mapped to a 0–100 sub-score and averaged — then **blend** it with
the existing technical score into the confidence that gates each recommendation. The metrics come
from `MarketData.fundamentals`, which the provider began serving in Sprint 34.

The analyst contract already has the field (`Recommendation.fundamental_score: float | None`), so
**no contract change**. The blend is designed so that **when fundamentals are absent the pillar is
skipped and the composite equals the technical score exactly** — i.e. every existing test keeps its
current values; only new fundamentals-bearing tests are pinned fresh.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/sprints/sprint-34-provider-fundamentals.md`
  (the feed you now consume — `MarketData.fundamentals: dict[Ticker, dict[str, float]]`, keyed by
  the Finnhub metric names this sprint reads).
- **Shipped code you extend (read it):**
  - `agents/analyst/domain/scoring.py` (64L) — `score_candidate(candidate, bars, settings)` builds
    `ScoreBreakdown(technical_score, confidence, metrics, rejection_reason)`. Today
    `confidence = floor + technical * span`. You add a fundamentals argument, compute the
    fundamental pillar, blend, and recompute confidence from the **composite**.
  - `agents/analyst/domain/recommend.py` (74L) — `decide(...)` builds the `Recommendation`. You set
    `fundamental_score` from the breakdown and extend the rationale **only when** a fundamental
    pillar is present (keep the existing string unchanged when it is absent).
  - `agents/analyst/domain/technical_rules_range.py` / `technical_rules_event.py` — the band-rule
    convention to mirror: fixed cut-points as **named module constants** with the standard "this is
    the rule, not tunable policy" comment.
  - `agents/analyst/agent.py` (`_score`, line ~133) — pass each ticker's fundamentals into
    `score_candidate`: `market.fundamentals.get(candidate.ticker, {})`.
  - `agents/analyst/provider_client.py` (`request_market_data`, ~line 44) — the `DataRequest`
    currently defaults `fields=("ohlcv",)`. Add `"fundamentals"`.
  - `agents/analyst/settings.py` (61L) — add the two blend-weight tunables here (scoring policy,
    not indicator periods, so the concrete class, not `_IndicatorSettings`).
  - `contracts/analyst.py` — confirm `Recommendation.fundamental_score`/`sentiment_score` already
    exist; CONTRACT stays version 0.1.0, `owns_graph` untouched.

### The scoring rule (port these bands exactly)

`score_fundamental(metrics)` reads each metric by its Finnhub key (first present of the fallbacks
wins), applies the bands top-to-bottom (first match wins, else the default), and averages the
sub-scores of the metrics that were present. `require_positive` metrics are **skipped** when the
value is `≤ 0`. Skip any metric whose key is missing. Strict `<`/`>` for `lt`/`gt`, inclusive for
`le`.

| Metric | Key(s) (first present wins) | require_positive | Bands (first match wins) | Default |
| --- | --- | --- | --- | --- |
| P/E | `peBasicExclExtraTTM`, `peTTM` | yes | `<10 → 80`, `≤25 → 60` | `30` |
| ROE | `roeTTM` | no | `>15 → 80`, `>5 → 55` | `25` |
| Net margin | `netProfitMarginTTM` | no | `>20 → 80`, `>10 → 55` | `30` |
| Current ratio | `currentRatioQuarterly` | yes | `>1.5 → 70`, `>1.0 → 50` | `25` |
| P/B | `pbQuarterly`, `pbAnnual` | yes | `<1.5 → 80`, `≤3.0 → 60`, `≤5.0 → 40` | `20` |
| Debt/Equity | `totalDebt/totalEquityQuarterly`, `totalDebt/totalEquityAnnual` | no | `<0.5 → 80`, `<1.0 → 65`, `<2.0 → 45` | `20` |
| EPS growth YoY | `epsGrowthTTMYoy` | no | `>20 → 85`, `>5 → 65`, `>-5 → 45` | `20` |
| Revenue growth YoY | `revenueGrowthTTMYoy` | no | `>15 → 80`, `>5 → 60`, `>-5 → 45` | `25` |

`score_fundamental(metrics) -> tuple[float | None, dict[str, float]]`: returns
`(mean_of_available_sub_scores, {metric_name: sub_score, ..., "fundamentals_available": n})`, or
`(None, {})` when **no** metric is usable. The values are 0–100 (the caller divides by 100).

### Design decision — absent fundamentals are *skipped*, not neutral-50 (decided; please read)

The reference engine returned a neutral **50** for the fundamental pillar when no metrics were
available, and blended that 50 in at the fundamental weight. **This sprint instead skips the pillar
entirely when no metric is usable** (`score_fundamental → None` → composite = technical only).

Rationale: this matches v2's established "skip absent evidence, never dilute" idiom (every technical
indicator returns `None` below its history; the provider degrades gracefully), and it keeps the
composite identical to today whenever fundamentals are missing — so the gate isn't quietly dragged
toward neutral on the (common) Finnhub-has-no-data path, and **no existing test re-pins**. If the
planning owner prefers strict reference parity (blend a neutral 50 when absent), flag it back before
implementing — that path re-pins essentially every analyst/pipeline confidence and dilutes scores
whenever fundamentals are unavailable.

### The blend

Composite (all in 0–1):

- `technical = bounded(raw_technical / 100)` (unchanged).
- `fundamental = bounded(raw_fundamental / 100)` when `score_fundamental` returned a value, else
  `None`.
- `composite = technical` when `fundamental is None`; otherwise the weight-renormalised blend
  `composite = (w_t * technical + w_f * fundamental) / (w_t + w_f)`.
- `confidence = bounded(floor + composite * span)` (same floor/span as today).

`Recommendation.technical_score` stays the pure technical value; `Recommendation.fundamental_score`
carries the fundamental 0–1 value (or `None`). The confidence is the blended gate.

## Part A — Settings

`agents/analyst/settings.py` — add to `AnalystSettings` (the concrete class):

- `technical_weight: float = tunable(0.50, why="Reference composite weight for the technical pillar.", ge=0.0, le=1.0)`
- `fundamental_weight: float = tunable(0.30, why="Reference composite weight for the fundamental pillar; renormalised over present pillars.", ge=0.0, le=1.0)`

(The reference also reserves 0.20 for sentiment — **do not** add a sentiment weight yet; it lands
with the sentiment sprint.) Keep `settings.py` < 200L.

## Part B — Fundamental rules

New `agents/analyst/domain/fundamental_rules.py` — ≤ 160L.

```python
"""Fundamental metric scoring rules and their pillar score.

Agent: analyst
Role: map Finnhub valuation/quality/growth metrics to 0-100 sub-scores and average them.
External I/O: none.
"""
```

- Encode the table above as a **named, module-level constant rule table** (the fixed reference
  rule, not tunable policy — mirror the "named band constants" comment style of
  `technical_rules_range.py`). A structured tuple of metric specs
  `(name, keys, require_positive, bands, default)` is preferred over ~30 scattered constants for
  readability; keep the explanatory header comment.
- A small pure `_match(value, op, threshold) -> bool` helper for `lt`/`le`/`gt` (mirror the
  reference `_matches_rule`).
- `score_fundamental(metrics: dict[str, float]) -> tuple[float | None, dict[str, float]]` as
  specified above. Never raises.

## Part C — Fold into scoring

`agents/analyst/domain/scoring.py`:

- Change the signature to
  `score_candidate(candidate, bars, fundamentals: dict[str, float], settings)` (insert
  `fundamentals` before `settings`).
- Compute `technical` as today; then `raw_fund, fmetrics = score_fundamental(fundamentals)` and the
  blend above. Add `fundamental_score: float | None = None` to `ScoreBreakdown`; set it on the
  result. Put the composite and the fundamental sub-scores into `metrics` (e.g. `composite_score`,
  the `fmetrics` entries) so they are auditable. The `insufficient_market_history` early return is
  unchanged (fundamentals don't rescue a candidate with no price history).

## Part D — Wire the agent + request

- `agents/analyst/provider_client.py`: in `request_market_data`, set
  `fields=("ohlcv", "fundamentals")` on the `DataRequest`. (An empty/degraded fundamentals result is
  handled downstream — note the provider only sets `quality.used_fallback` on a fundamentals
  **fault**, not on empty data, so the analyst's existing `used_fallback` rejection is unaffected.)
- `agents/analyst/agent.py`: in `_score`, pass
  `market.fundamentals.get(candidate.ticker, {})` into `score_candidate`.

## Part E — Decision + rationale

`agents/analyst/domain/recommend.py`:

- Set `fundamental_score=score.fundamental_score` on the `Recommendation`.
- When `score.fundamental_score is not None`, extend the rationale summary with a short clause
  (e.g. "…and a fundamental score of X"); when it is `None`, leave the existing summary **byte-for-
  byte unchanged** (so current tests that assert the exact string stay green). Optionally add an
  evidence ref `"analyst.fundamental_score"` only in the present branch.

## Part F — Tests

### F1. `agents/analyst/tests/test_fundamental_rules.py` — ≤ 130L

Hand-verified band boundaries for each metric (both sides of each cut-point), the fallback-key
precedence (e.g. `peTTM` used when `peBasicExclExtraTTM` absent), `require_positive` skipping a
`≤ 0` value, a missing key skipped, the partial-average over a subset, and the empty/all-unusable
case → `(None, {})`.

### F2. Scoring + decision tests

- New: a candidate **with** fundamentals → hand-computed blended `confidence`
  (`floor + ((w_t*tech + w_f*fund)/(w_t+w_f)) * span`) and `Recommendation.fundamental_score` set;
  rationale gains the fundamental clause.
- Existing `score_candidate` call sites (in `test_analyst_domain.py` / `test_technical_rules.py` /
  the scoring tests) gain the new `fundamentals={}` argument. With `{}` the pillar is skipped →
  **every pinned confidence/technical value is unchanged** (mechanical arg addition only — do not
  alter the expected numbers).

### F3. Agent + pipeline regression

- An analyst agent test where `market.fundamentals` carries metrics for a ticker → the recommendation
  shows a populated `fundamental_score`.
- Existing analyst-agent and full-pipeline tests use `FakeDataSource` with no fundamentals fixture →
  `market.fundamentals == {}` → skipped pillar → **no re-pin**. (Requesting the `"fundamentals"`
  field does not degrade quality on empty data — confirm the degraded-rejection tests are
  unaffected.) Run the whole suite.

## Steps

1. Branch `sprint-35-analyst-fundamental-scoring` off `main`.
2. **A** settings → **B** `fundamental_rules.py` (+ F1) → **C** fold into `scoring.py`.
3. **D** request + agent wiring → **E** decision/rationale. `make ci`.
4. **F2/F3** add fundamentals-bearing tests; add `fundamentals={}` to existing call sites; full-suite
   regression. `make ci` green at the coverage floor.
5. `wc -l agents/analyst/domain/*.py agents/analyst/settings*.py` — all < 200.
6. Push; hand back.

## Acceptance criteria

- `score_fundamental` reproduces the band table exactly (hand-verified), averages only present
  metrics, and returns `(None, {})` when none are usable; never raises.
- Confidence is gated on the renormalised composite; when fundamentals are absent the composite
  equals the technical score and **no existing expected value changes**.
- `Recommendation.fundamental_score` is populated when present, `None` otherwise; rationale extended
  only in the present branch.
- **No contract change** (CONTRACT 0.1.0, `owns_graph` untouched); analyst now requests the
  `"fundamentals"` field.
- All tests pass with pinned values; `make ci` green at/above the coverage floor (100.00);
  import-linter kept; every touched/new module < 200L.

## Out of scope (later sprints)

- **News + sentiment** (FinBERT/embeddings) + the provider **news feed**, and the third composite
  weight (`sentiment_weight` 0.20). Separate slice.
- **Relative strength** — analyst-side, only needs benchmark OHLCV (not blocked here).
- **Signal-diversity selection**, confidence buckets; PM/scanner/reporter gaps.
- Persisting fundamentals to the graph; any change outside the analyst package + its tests
  (plus the one-line provider-request field change).

## Handback report (paste into PR / reply)

- Confirm no contract change (analyst 0.1.0) and that the absent-fundamentals path leaves the
  composite == technical (so existing values were re-used, not re-pinned).
- The blend formula implemented and the two weights; one worked example (tech, fund → confidence).
- How `score_fundamental` handles fallback keys, `require_positive`, missing keys, and the
  all-unusable case.
- Final line counts: `fundamental_rules.py`, `scoring.py`, `recommend.py`, `settings.py`.
- New coverage % and floor; total test count; confirmation existing tests needed no value re-pin
  (only the mechanical `fundamentals={}` argument addition).

The planning agent reviews, merges to `main`, and plans the next slice (news + sentiment feed +
scoring, which adds the third composite pillar).
