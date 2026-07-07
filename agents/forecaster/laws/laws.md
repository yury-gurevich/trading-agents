# `Forecaster` — Laws

**Prefix:** `FORE` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Produce clearly-labelled shadow ML forecasts (sentiment + price/return) and measure
> them via scorecards — every output is advisory and never gates a decision until
> scorecard evidence earns promotion.

Each clause has a stable ID (`FORE-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **FORE-IDN-01** — The forecaster's single job is advisory ML signal production: run the
  sentiment model (FinBERT-class) and the return model (LightGBM) on their respective inputs and
  return `ShadowPrediction` objects whose `shadow=True` flag is always set. It produces evidence;
  it never decides.
- **FORE-IDN-02** — The forecaster exclusively writes these graph labels (single-writer rule):
  `ShadowPrediction`, `Model`.

## Inputs (`IN`)

- **FORE-IN-01** — `forecast` accepts `ForecastRequest { subject_kind, subject_ref, features }`.
  `subject_kind` is `"recommendation"` or `"position"`.
- **FORE-IN-02** — `forecast_return` accepts `ForecastRequest` (same schema). The return model
  fetches OHLCV from the provider via bus, ignoring `features`.
- **FORE-IN-03** — `scorecard` accepts `ScorecardRequest { model_id: str }`.
- **FORE-IN-04** — `sentiment_scorecard` accepts
  `SentimentScorecardRequest { model_id, forward_returns: dict[str, float] }`.
  `forward_returns` are injected by the caller (offline harness); never a live dependency.
- **FORE-IN-05** — `return_scorecard` accepts `ReturnScorecardRequest { model_id, forward_returns
  }`. Same offline-injection contract.
- **FORE-IN-06** — Malformed input → degraded response or empty scorecard; fault recorded; never
  raises to bus.

## Triggers (`TRG`)

- **FORE-TRG-01** — All capabilities triggered by RPC request only. No event subscription.
- **FORE-TRG-02** — The forecaster never self-triggers.

## Outputs (`OUT`)

- **FORE-OUT-01** — `forecast` and `forecast_return` return `ShadowPrediction { model_id,
  subject_ref, value: float [0,1], confidence: float [0,1], shadow: True, provenance }`.
- **FORE-OUT-02** — `shadow` is structurally `True` on every `ShadowPrediction`; no code path
  produces `shadow=False`.
- **FORE-OUT-03** — `scorecard` / `sentiment_scorecard` / `return_scorecard` return `Scorecard {
  model_id, metrics, sample_size, fresh_as_of, promotion_eligible: False }`.
- **FORE-OUT-04** — `promotion_eligible` is structurally `False` on every `Scorecard`; no code
  path produces `True`.
- **FORE-OUT-05** — A `ShadowPrediction` graph node is written per `forecast` / `forecast_return`
  call. A `Model` node is upserted per model_id.
- **FORE-OUT-06** — On scoring failure, `value=NEUTRAL (0.5)`, `confidence=0.0` is returned with
  provenance; a fault is recorded.

## Prohibitions (`NEV`)

- **FORE-NEV-01** — Never emits a non-shadow (binding) signal. `shadow=True` is a structural
  invariant; no feature flag or setting can override it.
- **FORE-NEV-02** — Never gates, vetoes, or blocks a recommendation, sizing, or exit. The
  forecaster is read by the scorecard harness; it has no write path to OrderIntent or
  CloseDecision.
- **FORE-NEV-03** — Never self-promotes a model. `promotion_eligible=False` is structurally
  set on all Scorecard outputs; promotion is exclusively the curator's domain.
- **FORE-NEV-04** — Never calls a data source directly; market data and news are requested from
  the provider via the bus.

## State & effects (`STA`)

- **FORE-STA-01** — Stateless between calls. Model weights are loaded lazily from disk; no
  in-memory per-session state persists between `forecast` calls.
- **FORE-STA-02** — Graph writes are append-only. `ShadowPrediction` nodes accumulate; none are
  overwritten.

## Determinism & idempotency (`IDM`)

- **FORE-IDM-01** — The sentiment model output is model-deterministic given the same headlines.
  Re-invoking `forecast` for the same `subject_ref` with the same news window produces a new
  `ShadowPrediction` node (not idempotent at the graph level).
- **FORE-IDM-02** — Return model output is deterministic given the same OHLCV bars. Price
  randomness is bounded by the provider fetch, stamped in the node's `fresh_as_of`.
- **FORE-IDM-03** — Scorecard methods are read-only over `ShadowPrediction` nodes; calling twice
  returns the same metrics (same graph state).

## Ordering & concurrency (`ORD`)

- **FORE-ORD-01** — No ordering dependency between forecast calls.
- **FORE-ORD-02** — Concurrent `forecast` calls are safe (no shared mutable state).

## Failure, recovery & rollback (`FAIL`)

- **FORE-FAIL-01** — Model scoring failure (exception in `score_headlines` or return model):
  `fault_boundary` captures; returns `ModelReading(NEUTRAL, 0.0)`; fault emitted; prediction node
  still written with neutral values.
- **FORE-FAIL-02** — Provider bus error (news/price fetch): returns neutral reading; fault
  recorded; model node not written (no data, no provenance).
- **FORE-FAIL-03** — LightGBM model file not found: `fault_boundary` captures; neutral
  `ShadowPrediction` returned; no crash.

## Type alignment (`TYP`)

- **FORE-TYP-01** — `ShadowPrediction` and `Scorecard` match `contracts/forecaster.py` exactly.
- **FORE-TYP-02** — `value` and `confidence` are floats in `[0, 1]`; the logistic squash applied
  to raw LightGBM outputs ensures the range.
- **FORE-TYP-03** — `ShadowPrediction` graph node serialisation matches the contract so downstream
  `claim_check_read` or direct graph reads reconstruct a valid object.

## Security & privilege (`SEC`)

- **FORE-SEC-01** — Holds no broker or market-data credentials. The only elevated-privilege path
  is model file I/O, which is read-only and sandboxed.
- **FORE-SEC-02** — `return_model_path` is a relative path to a local model artefact; never an
  external URL or a user-controlled input.
- **FORE-SEC-03** — Never logs raw news headlines or proprietary market data to external systems.

## Dependencies (`DEP`)

- **FORE-DEP-01** — `DEP-BUS` — requests news from provider (`get_market_data`) and price bars
  via the bus for the return model.
- **FORE-DEP-02** — `DEP-POSTGRES` — reads `SentimentReading` and `ShadowPrediction` nodes for
  scorecard correlation; writes `ShadowPrediction` and `Model`.
- **FORE-DEP-03** — `DEP-FEED` (indirect) — provider resolves the feed; forecaster is insulated.

## Observability & audit (`OBS`)

- **FORE-OBS-01** — A `ShadowPrediction` node is written per prediction; model lineage
  (`Model` node) is reconstructable from the graph.
- **FORE-OBS-02** — Degraded paths (neutral reading, scoring failure) emit faults to the sink;
  never buried.
- **FORE-OBS-03** — Scorecard metrics are deterministic given the graph state at call time;
  `fresh_as_of` timestamps the observation window.

## Performance envelope (`PERF`)

- **FORE-PERF-01** — FinBERT model is injected (no network call at inference); latency is
  CPU-bound on the inference batch.
- **FORE-PERF-02** — LightGBM model loads from disk on first call (`bars_for_full_confidence=60`
  bars minimum for full confidence).
- **FORE-PERF-03** — `news_lookback_days=7` caps the provider request window; `price_lookback_days
  =90` caps the return model window.

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["request"],
    "peers": ["provider"]
  },
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["ShadowPrediction", "Model"],
    "labels_read": ["SentimentReading"]
  },
  "filesystem": {
    "operations": ["read"],
    "paths": ["models/lgbm-return-v1.txt"]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `model_id` | `"finbert-sentiment"` | `str` | NO | Identity of the injected sentiment model; structural |
| `model_ref` | `"ProsusAI/finbert"` | `str` | NO | HuggingFace model reference; structural |
| `news_lookback_days` | `7` | `int ≥ 1 ≤ 90` | YES | Recent-headline window for shadow sentiment |
| `headlines_for_full_confidence` | `5` | `int ≥ 1 ≤ 50` | YES | Headline count reaching full advisory confidence |
| `return_model_id` | `"lgbm-return-v1"` | `str` | NO | Identity of the return model; structural |
| `return_model_ref` | `"lightgbm-gbdt"` | `str` | NO | Algorithm family reference; structural |
| `return_model_path` | `"models/lgbm-return-v1.txt"` | `str` | NO | Local artefact path; structural |
| `price_lookback_days` | `90` | `int ≥ 30 ≤ 365` | YES | Trailing calendar window of daily bars for price features |
| `return_short_horizon` | `1` | `int ≥ 1 ≤ 10` | YES | Short trailing-return horizon in price feature row |
| `return_mid_horizon` | `5` | `int ≥ 2 ≤ 30` | YES | Medium trailing-return horizon in price feature row |
| `return_long_horizon` | `20` | `int ≥ 5 ≤ 120` | YES | Long trailing-return horizon in price feature row |
| `volatility_window` | `20` | `int ≥ 2 ≤ 120` | YES | Window for realized volatility of daily returns |
| `momentum_window` | `20` | `int ≥ 2 ≤ 120` | YES | Window for price/SMA momentum and volume ratio |
| `bars_for_full_confidence` | `60` | `int ≥ 1 ≤ 365` | YES | Bar count at which price reading reaches full confidence |
| `return_squash_scale` | `0.05` | `float ≥ 0.001 ≤ 1.0` | YES | Logistic scale mapping predicted return onto [0, 1] |
| `system_prompt` | `""` | `str` | YES | Champion slot for DSPy-compiled macro-event extraction prompt (ADR-0010); pre-declared; empty until P13 LLM path ships |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
- v1.1 — S72: added `system_prompt` tunable (ADR-0010 immediate consequence); pre-declared for P13.
