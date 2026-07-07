# `Analyst` — Laws

**Prefix:** `ANLZ` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Score scanner candidates into evidence-backed trade recommendations — or explain clearly
> why none qualify today.

Each clause has a stable ID (`ANLZ-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

---

## Identity & purpose (`IDN`)

- **ANLZ-IDN-01** — The analyst's sole job is candidate → scored recommendation. It blends a
  technical pillar (RSI, MACD, Bollinger, SMA-200, EMA crossover, ATR, Stochastic, OBV,
  patterns), a fundamental pillar, a sentiment pillar (Loughran–McDonald lexicon champion +
  provider-sentiment shadow), and an optional Alpha158 pillar (off by default, weight = 0.00)
  into a 0–100 composite confidence. It never sizes positions, never approves orders, and
  never calls a market-data API directly.
- **ANLZ-IDN-02** — The analyst exclusively owns the `AnalystRun`, `Recommendation`, and
  `SentimentReading` graph labels. No other agent writes to these labels.

---

## Inputs (`IN`)

- **ANLZ-IN-01** — `analyze` accepts a `CandidateSet` (from `contracts/scanner.py`): `run_id`,
  `candidates` (tuple of `Candidate`), `filter_trace`, `explanation`, `provenance`. All fields
  must pass Pydantic validation; malformed input raises a validation error before any scoring.
- **ANLZ-IN-02** — In pub/sub mode the analyst subscribes to `scan.candidates.ready`; it
  resolves the claim-check reference from the graph store to a `CandidateSet` before invoking
  `analyze`. The claim-check event is authoritative; unknown extra fields are ignored.
- **ANLZ-IN-03** — An empty `CandidateSet` (zero candidates) → empty `RecommendationSet` with
  a human-readable explanation. No provider calls are made; no graph nodes are written.
- **ANLZ-IN-04** — `explain_recommendation` accepts a `CandidateSet`; returns an `Explanation`
  describing the scoring methodology. No provider call, no graph write.

---

## Triggers (`TRG`)

- **ANLZ-TRG-01** — RPC capability `analyze`: invoked on demand by any caller in
  `allowed_callers`. Pull mode; returns a `RecommendationSet` synchronously.
- **ANLZ-TRG-02** — Pub/sub: `scan.candidates.ready` event auto-invokes `analyze`; the result
  is written via claim-check and `analysis.recommendations.ready` is published. This is the
  primary production trigger path.
- **ANLZ-TRG-03** — The analyst never self-triggers. Idle (no inbound request or event) →
  zero provider calls, zero graph writes.

---

## Outputs (`OUT`)

- **ANLZ-OUT-01** — `analyze` always returns a `RecommendationSet`: `run_id`, `recommendations`,
  `rejections`, `explanation`, `provenance`. Every candidate in the input is accounted for in
  one of the two tuples or in the empty-result path.
- **ANLZ-OUT-02** — Each `Recommendation` carries: `ticker`, `action`, `confidence ∈ [0.0, 1.0]`,
  `technical_score`, optional `sentiment_score`, optional `fundamental_score`, optional
  `suggested_stop_pct`, optional `suggested_target_pct`, and a per-ticker `rationale`.
- **ANLZ-OUT-03** — Candidates that fail the regime confidence gate are placed in `rejections`
  with a reason string. The silence is always attributed.
- **ANLZ-OUT-04** — If the provider is unavailable or returns degraded data, `analyze` returns
  an empty `RecommendationSet` with `incident_refs` and a clear explanation. A fault is
  recorded to the central channel.
- **ANLZ-OUT-05** — In pub/sub mode the outbound `analysis.recommendations.ready` event carries
  only a claim-check reference; the `RecommendationSet` payload lives in the graph.
- **ANLZ-OUT-06** — A `SentimentReading` node is persisted for every ticker scored, covering
  both the lexicon champion reading and the provider-sentiment shadow reading (when the
  provider returns a sentiment score for that ticker). These nodes are the input substrate for
  the forecaster's `sentiment_scorecard`.

---

## Prohibitions (`NEV`)

- **ANLZ-NEV-01** — Never sizes positions. The analyst emits `confidence`, optional
  `suggested_stop_pct` / `suggested_target_pct`, but never a quantity, price, or dollar
  amount. Sizing is the portfolio manager's exclusive domain.
- **ANLZ-NEV-02** — Never calls a market-data or news API directly. All OHLCV, fundamentals,
  news, sentiment, and regime data are requested from the provider agent via the bus.
- **ANLZ-NEV-03** — Never overrides the regime confidence gate. A candidate whose composite
  confidence falls below `regime.base_min_confidence` is rejected; the analyst has no
  mechanism to bypass this gate.
- **ANLZ-NEV-04** — Never writes to graph labels it does not own. `ScanRun`, `Candidate`
  (scanner), `PMRun`, `OrderIntent` (PM) and all other agent labels are read-only to the
  analyst.
- **ANLZ-NEV-05** — Never promotes a `SentimentReading` shadow scorer to the champion role.
  Scorecard-based promotion is the forecaster + curator + operator gate (ADR-0002).

---

## State & effects (`STA`)

- **ANLZ-STA-01** — Stateless between calls. No scoring state, market data cache, or
  indicator values are retained in-process between `analyze` invocations.
- **ANLZ-STA-02** — Every `analyze` call writes an `AnalystRun` node plus one
  `Recommendation` or `Rejection` node per candidate, and one `SentimentReading` per scored
  ticker. All writes are append-only; no prior record is modified.
- **ANLZ-STA-03** — `SentimentReading` nodes are append-only per run. Two runs for the same
  ticker produce two separate nodes; no upsert logic merges them.

---

## Determinism & idempotency (`IDM`)

- **ANLZ-IDM-01** — Given identical `CandidateSet`, `MarketData`, `RegimeContext`, and
  `AnalystSettings`, all pillar computations and the composite blend are fully deterministic:
  same input → same `RecommendationSet`.
- **ANLZ-IDM-02** — `run_id` is taken from the input `CandidateSet` and threaded through.
  Re-running with the same data appends a second `AnalystRun` (append-only graph); the caller
  is responsible for not duplicating triggers.

---

## Ordering & concurrency (`ORD`)

- **ANLZ-ORD-01** — Candidates within a single run are scored independently; order within the
  `candidates` tuple does not affect individual scores.
- **ANLZ-ORD-02** — Consecutive `analyze` calls are independent. The analyst holds no shared
  mutable state and is safe for concurrent requests subject to the graph store's own
  concurrency guarantees.

---

## Failure, recovery & rollback (`FAIL`)

- **ANLZ-FAIL-01** — Provider unavailable (no market data or regime) → empty
  `RecommendationSet` returned; fault recorded; no exception propagates.
- **ANLZ-FAIL-02** — Provider returns degraded data (`used_fallback=True`) → fault recorded;
  empty `RecommendationSet` with `incident_refs`. The degraded data is never scored.
- **ANLZ-FAIL-03** — Per-candidate scoring exception → that candidate is rejected with a
  reason; remaining candidates proceed normally.
- **ANLZ-FAIL-04** — Sentiment scoring failure → that ticker's `SentimentReading` is absent;
  the technical score and other pillars are unaffected. The missing reading is observable (no
  node written, no silent success).

---

## Type alignment (`TYP`)

- **ANLZ-TYP-01** — `Recommendation.confidence` is a `float ∈ [0.0, 1.0]`; never fabricated
  above 1.0 or below 0.0. `RecommendationSet`, `Recommendation`, and `Rejection` match
  `contracts/analyst.py` exactly.
- **ANLZ-TYP-02** — `suggested_stop_pct` and `suggested_target_pct` are `float ∈ [0.0, 1.0]`
  or `None`; stop is always < target when both are present (enforced by the regime source).
- **ANLZ-TYP-03** — `SentimentReading` carries a `scorer` field (`"lexicon"` or `"provider"`)
  that identifies which pillar produced it. The field is never omitted or defaulted silently.

---

## Security & privilege (`SEC`)

- **ANLZ-SEC-01** — The analyst holds no credentials and makes no external API calls. Its
  blast radius if compromised is a fabricated or biased recommendation list forwarded to the
  portfolio manager — it cannot move money or access the broker.
- **ANLZ-SEC-02** — Only callers in the declared `allowed_callers` list (scanner, dispatcher,
  operator, supervisor) may invoke `analyze`. The bus enforces `caller_authorized` at receipt.
- **ANLZ-SEC-03** — The analyst is quarantinable: removing its `scan.candidates.ready`
  subscription stalls the pipeline without corrupting any persisted state.

---

## Dependencies (`DEP`)

- **ANLZ-DEP-01** — `DEP-BUS`: requires request/reply (provider calls) and subscribe/publish
  (`scan.candidates.ready` / `analysis.recommendations.ready`).
- **ANLZ-DEP-02** — `DEP-POSTGRES`: requires graph append-write access for `AnalystRun`,
  `Recommendation`, and `SentimentReading`; claim-check read for `scan.candidates.ready`.
- **ANLZ-DEP-03** — `DEP-FEED` (via provider): the provider's `get_market_data` and
  `get_regime` capabilities must be reachable. Provider degradation degrades the analyst's
  output but does not break its operation.

---

## Observability & audit (`OBS`)

- **ANLZ-OBS-01** — Every `AnalystRun` in the graph is fully reconstructable: input
  candidates, per-ticker scores, regime context used, and the `RecommendationSet` returned.
  Score breakdowns (`ScoreBreakdown`) are persisted on `Recommendation` nodes.
- **ANLZ-OBS-02** — Faults (provider degradation, per-candidate errors) are routed to the
  central fault channel. The degraded path is never silent: it produces attributed
  `incident_refs` and a fault record.

---

## Performance envelope (`PERF`)

- **ANLZ-PERF-01** — The analyst's latency budget is dominated by two provider round-trips
  (market data + regime). The scoring computation itself (all pillars for all candidates in a
  typical 5-candidate set) is pure in-process Python and adds negligible latency.

---

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["request_reply", "subscribe", "publish", "claim_check_read"],
    "topics": {
      "subscribe": ["scan.candidates.ready"],
      "publish": ["analysis.recommendations.ready"]
    },
    "delivery": "at_least_once",
    "schema_version": "1.0"
  },
  "graph": {
    "operations": ["append_write", "claim_check_read"],
    "labels": ["AnalystRun", "Recommendation", "SentimentReading"],
    "access": "write_own_labels_only"
  }
}
```

**Allowed callers for `analyze`:** `scanner`, `dispatcher`, `supervisor`, `operator`
**Allowed callers for `explain_recommendation`:** `dispatcher`, `supervisor`, `operator`,
`researcher`

---

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `lookback_days` | `260` | `int ≥ 2, ≤ 512` (days) | YES | Indicators need ~200 trading days; 260 calendar days yields enough bars |
| `min_history_bars` | `2` | `int ≥ 2, ≤ 60` (bars) | YES | At least two closes before any indicator is meaningful |
| `confidence_floor` | `0.30` | `float ≥ 0.0, ≤ 1.0` | YES | Maps composite 0 → this floor; keeps weak evidence below the regime gate |
| `confidence_span` | `0.60` | `float ≥ 0.0, ≤ 1.0` | YES | Maps composite 100 → floor + span; strong evidence clears the default regime threshold |
| `technical_weight` | `0.50` | `float ≥ 0.0, ≤ 1.0` | YES | Reference composite weight for the technical pillar |
| `fundamental_weight` | `0.30` | `float ≥ 0.0, ≤ 1.0` | YES | Reference weight for the fundamental pillar; renormalised over present pillars |
| `sentiment_weight` | `0.20` | `float ≥ 0.0, ≤ 1.0` | YES | Reference weight for the sentiment pillar; renormalised over present pillars |
| `alpha158_pillar_weight` | `0.00` | `float ≥ 0.0, ≤ 1.0` | YES | Alpha158 fifth pillar; 0.00 = off; enable after 20-day IC comparison (ΔIC ≥ 0.02) |
| `benchmark_ticker` | `"SPY"` | `str` | YES | Relative-strength benchmark; matches the scanner's universe |
| `rs_window` | `20` | `int ≥ 2, ≤ 120` (bars) | YES | Relative-strength lookback (~one trading month) |
| `relative_strength_weight` | `0.20` | `float ≥ 0.0, ≤ 1.0` | YES | Weight of relative strength within the technical pillar (alongside 0.80 core) |
| `signal_diversity_slack` | `5.0` | `float ≥ 0.0, ≤ 50.0` | YES | Slack allowing a lower-scoring signal from an unused pillar to surface in the rationale |
| `max_top_signals` | `5` | `int ≥ 1, ≤ 20` | YES | Maximum explanatory signals surfaced per recommendation rationale |

*Indicator-specific tunables (MACD spans, Bollinger window, EMA periods, etc.) are declared
in `AnalystSettings` / `_IndicatorSettings` and are all `tunable` with `why=` justifications.*

---

## Divergence register

| ID | Law says | PRD / code says | Decision needed |
| --- | --- | --- | --- |
| — | — | — | No divergences at DRAFT v0 |

---

## Changelog

- v0 — drafted (ideal-design, S70). Not yet locked.
