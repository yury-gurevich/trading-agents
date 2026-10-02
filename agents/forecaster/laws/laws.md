# `Forecaster` — Laws

**Prefix:** `FORE` · **status:** LOCKED v1.10 · **Owner:** Yury Gurevich

> Produce clearly-labelled shadow ML forecasts (sentiment + price/return) and measure
> them via scorecards — every output is advisory and never gates a decision until
> scorecard evidence earns promotion.

Each clause has a stable ID (`FORE-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **FORE-IDN-01** — The forecaster's single job is advisory ML signal production over **four
  legs**: the sentiment model (`forecast`, FinBERT-class), the return model (`forecast_return`,
  LightGBM), the approved-factor shadow (`forecast_factor`), and the barrier model
  (`forecast_barrier`, EXP-018's GARCH barrier claim, `FORE-OUT-07`). Each leg returns a
  `ShadowPrediction` whose `shadow=True` flag is always set. It produces evidence; it never decides.
  *(DRIFT-081; was: the sentiment and return models only.)*
- **FORE-IDN-02** — The forecaster exclusively writes these graph labels (single-writer rule):
  `ShadowPrediction`, `Model`, `ForecasterRun`, `BarrierForecast`, `BarrierSettlement`,
  `BarrierSettlementPass`.

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
- **FORE-IN-07** — `forecast_barrier` accepts `ForecastRequest`: `subject_ref` is the ticker,
  `features` carries a buy's `stop_pct` and `target_pct`, each a fraction of the entry close in
  (0, 1], and `history_ref` names the `BarrierHistory` the provider wrote for the run. A request
  missing either barrier, or with either outside that range, is refused before the history is read:
  no claim, a fault, and the `FORE-OUT-06` neutral reading, never a raise to the bus. The stock's
  daily bars are read **only** from that provider-written node, never requested over the bus; no
  named node, a node that does not hold the ticker, a ticker the provider dropped, or a failed node
  is a refusal (`FORE-FAIL-04`).

## Triggers (`TRG`)

- **FORE-TRG-01** — Every capability runs on a request, never on an event subscription. A request
  comes from an RPC caller or from the forecaster's graph-pull loop: for each `AnalystRun` that has no
  `ForecasterRun` yet (and, when it holds a buy with both a stop and a target, whose `BarrierHistory`
  the provider has written; a run with no such buy never waits), the loop requests the legs its
  caller names and then records one `ForecasterRun` for it, so an `AnalystRun` is forecast once. The **deployed** loop names
  `forecast_barrier` only, fired once per buy that carries both a stop and a target; `forecast`,
  `forecast_return` and `forecast_factor` are fired by the in-process pipeline or an RPC caller, never
  by the deployed loop. A leg name the loop does not know is refused before any request. The deployed
  loop also counts only a *current* `AnalystRun`, one created within 24 h (the shared
  `contracts/barrier_history.is_current_run`, DL-241 D11): an older run is never claimed. The loop's
  second work is one **settlement pass** per `AnalystRun` with no `BarrierSettlementPass` yet (the
  deployed loop: per current run only, by the same rule): it reads that run's `MarketData` through the
  run's lineage (`AnalystRun ←ANALYZED_BY— ScanRun —DERIVED_FROM→ MarketData`: one node, never a
  listing of them), settles or voids each open claim (`FORE-OUT-08`, `FORE-FAIL-05`) and records the
  pass (`FORE-IDM-05`). The pass is the loop's own work, fired by the run it reads, not a capability;
  it sends nothing on the bus, and the in-process pipeline runs the same pass. Both loop works
  are found **by key and edge alone**: `AnalystRun`s without `FORECAST_BY` for forecasting, and
  without `BARRIER_SETTLEMENT_BY` for settlement. The deployed loop supplies the shared 24 h
  `created_at` bound before fetching props and still applies the current-run rule; without `now`
  the in-process pipeline supplies no recency bound. **Props are fetched only for those keys**;
  history readiness is checked only on the forecasting candidates.
- **FORE-TRG-02** — The forecaster never self-triggers: no timer, schedule or idle loop starts work.
  An unconsumed `AnalystRun` is an artifact another stage wrote, and finding one is a trigger, not a
  self-trigger; a poll that finds none requests nothing.

## Outputs (`OUT`)

- **FORE-OUT-01** — `forecast` and `forecast_return` return `ShadowPrediction { model_id,
  subject_ref, value: float [0,1], confidence: float [0,1], shadow: True, provenance }`.
- **FORE-OUT-02** — `shadow` is structurally `True` on every `ShadowPrediction`; no code path
  produces `shadow=False`.
- **FORE-OUT-03** — `scorecard` / `sentiment_scorecard` / `return_scorecard` / `barrier_scorecard`
  return `Scorecard { model_id, metrics, sample_size, fresh_as_of, promotion_eligible: False }`.
- **FORE-OUT-04** — `promotion_eligible` is structurally `False` on every `Scorecard`; no code
  path produces `True`.
- **FORE-OUT-05** — A `ShadowPrediction` graph node is written per `forecast` / `forecast_return`
  call. A `Model` node is upserted per model_id.
- **FORE-OUT-06** — On scoring failure, `value=NEUTRAL (0.5)`, `confidence=0.0` is returned with
  provenance; a fault is recorded.
- **FORE-OUT-07** — For a buy's stop and target, `forecast_barrier` states the probability that
  over the next 10 sessions the price reaches the stop first (`p_stop_first`), the target first
  (`p_target_first`) or neither (`p_neither`). Within a session the low is checked before the high,
  so a session touching both counts as the stop; the three sum to 1. The model is EXP-018's:
  GARCH(1,1) with Student-t innovations fitted on the stock's own daily bars as the provider's
  `BarrierHistory` holds them (at most its `sessions_requested`), persistence above 0.999 scaled in
  proportion to 0.999 (`capped`), and `barrier_paths` filtered-historical-simulation paths. On
  success it writes exactly one `BarrierForecast` node, the claim, carrying `ticker`, `as_of` (the
  last bar's date), `entry_close` (that bar's close), `horizon_sessions`, `stop_pct`, `target_pct`,
  the three probabilities, `model_id`, `model_version`, `history_bars`, `history_ref` (the
  `BarrierHistory` the bars were read from), `n_paths`, `seed`, `fit_status` (`accepted` |
  `capped`), the fitted `garch_mu` / `garch_omega` / `garch_alpha` / `garch_beta`, `created_at` and
  `shadow: true`, and returns a `ShadowPrediction` whose `value` is `p_target_first` and whose
  `confidence` is `history_bars ÷` the history's `sessions_requested` (at most 1). It writes no
  `ShadowPrediction` node. The claim is advisory evidence only (`FORE-NEV-01/02`).
- **FORE-OUT-08** — Each `BarrierForecast` claim is settled against what the market did, by
  EXP-018's outcome rule on the daily bars of a later run's `MarketData` (a node the provider wrote,
  read as `FORE-TRG-01` says): over the 10 sessions after the claim's `as_of` bar (matched by date), a
  low at or below `entry × (1 − stop_pct)` is the stop, checked first in each session, a high at or
  above `entry × (1 + target_pct)` the target, else neither, where `entry` is that series' own close
  on `as_of`, never the claim's `entry_close`. The claim's probabilities never decide the outcome.
  The first run whose bars decide it settles it, once, as an append-only `BarrierSettlement` (key
  `settlement:{claim key}`, linked `BarrierForecast -SETTLED_BY-> BarrierSettlement`) carrying
  `claim_key`, `model_id`, `ticker`, `as_of`, `outcome` (`stop` | `target` | `neither` | `void`),
  `void_reason`, `settled_on` (the tenth session's date, or for a void the date of the pass that
  voided it), `settling_ref` (that run's `MarketData` key), `entry_close_settling`, `entry_ratio`
  (settling ÷ claimed close), the claim's three-class `brier` (absent for `void`) and `created_at`; the
  claim itself is never written to. `barrier_scorecard` (`BarrierScorecardRequest { model_id }`)
  reports one model's ledger: the `settled`, `void` and `open` counts; the realised share and the mean
  declared probability of each outcome; `brier_model`; `brier_climatology` from EXP-018's fixed shares
  (stop 0.287, target 0.477, neither 0.236), never re-estimated from the ledger; `skill` = 1 −
  `brier_model` ÷ `brier_climatology`; and EXP-018's date-bootstrap 95 % interval `skill_lo` /
  `skill_hi` (1,000 resamples of whole `as_of` dates, a fixed seed). A score it cannot compute is
  absent, never zero: with no settled claim only the counts are reported, and with fewer than two
  settled dates there is no interval. The scorecard reports; it decides nothing (`FORE-NEV-01/02`).

## Prohibitions (`NEV`)

- **FORE-NEV-01** — Never emits a non-shadow (binding) signal. `shadow=True` is a structural
  invariant; no feature flag or setting can override it.
- **FORE-NEV-02** — Never gates, vetoes, or blocks a recommendation, sizing, or exit. The
  forecaster is read by the scorecard harness; it has no write path to OrderIntent or
  CloseDecision.
- **FORE-NEV-03** — Never self-promotes a model. `promotion_eligible=False` is structurally
  set on all Scorecard outputs; promotion is exclusively the curator's domain.
- **FORE-NEV-04** — Never calls a data source directly; market data and news come only from the
  provider: requested over the bus, or read from a node the provider wrote (the barrier history,
  `FORE-IN-07`).

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
- **FORE-IDM-03** — The three shadow scorecards (`scorecard`, `sentiment_scorecard`,
  `return_scorecard`) are read-only over `ShadowPrediction` nodes; calling one twice returns the same
  metrics (same graph state). `barrier_scorecard` reads the barrier ledger and is governed by
  `FORE-IDM-05`. *(DRIFT-083; was: every scorecard method, over `ShadowPrediction` nodes.)*
- **FORE-IDM-04** — A barrier claim is deterministic given the same bars and barriers: the
  simulation's seed is a stable hash of `(ticker, as_of)` (the first four bytes of sha-256 over
  `ticker:as_of`), never a per-process salted hash. The claim is keyed by model, ticker and last bar
  date, so a second call on the same last bar merges into the same node, keeping the first call's
  `created_at` and `history_ref`; a second call that would state a different claim under that key
  is refused with a fault and the `FORE-OUT-06` neutral reading, and the first claim stands.
- **FORE-IDM-05** — Settlement is idempotent. A claim that has a `BarrierSettlement` is never
  settled again, and each `AnalystRun` gets one settlement pass, recorded last as one
  `BarrierSettlementPass` (key `settlement-pass:{run key}`, linked
  `AnalystRun -BARRIER_SETTLEMENT_BY-> BarrierSettlementPass`) with its pass date, `settling_ref` and
  counts: a second pass over the same run, or a later run whose bars also cover the claim, writes
  nothing, so the first covering run stays the claim's `settling_ref`. `barrier_scorecard` is
  read-only and returns the same metrics, its interval included, for the same ledger (the bootstrap's
  seed is fixed).

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
- **FORE-FAIL-04** — `forecast_barrier` records a claim only from a successful fit on enough
  history. A fit outside EXP-018's acceptance rule (not converged, ω ≤ 0, α < 0, β < 0, or
  α + β > 1 beyond 1e-9), an optimiser exception, an absent `arch`, fewer than
  `barrier_min_history_sessions` bars, no named `BarrierHistory`, or a ticker the provider dropped
  or a history it wrote as failed (the fault says `provider dropped: <the provider's reason>`,
  distinct from short history) writes no `BarrierForecast`, records a fault, and returns the
  `FORE-OUT-06` neutral reading. A claim is never fabricated: no default,
  fake, cached or earlier run's parameters stand in for a failed fit. The fault's **severity says
  whose the refusal is**. A **designed** "no claim", the system working as intended, is a
  `warning`, never an open incident: a ticker the provider dropped or a history it wrote as failed
  (the provider records its own fault for the failed fetch), fewer than
  `barrier_min_history_sessions` bars, or a fit outside EXP-018's acceptance rule. A **missing or
  broken input** is an `error`: no named `BarrierHistory`, one that does not hold the ticker,
  malformed barriers (`FORE-IN-07`), an optimiser exception or an absent `arch`. *(DL-247 D3,
  DRIFT-089.)*
- **FORE-FAIL-05** — A claim that cannot be settled honestly is never scored as a stop, a target or
  neither: it is settled `void` with a named `void_reason` and no `brier`. `suspected_corporate_action`
  when any session-over-session raw close ratio across its 10 sessions (from the `as_of` close to the
  tenth session's) is below 0.6 or above 1.67 (the bars are raw, so a split reads as a crash);
  `no_settling_bars` when it is still open on the pass of a run created 45 or more calendar days after
  its `as_of`. Before then, a claim whose settling series lacks the `as_of` bar or holds fewer than 10
  sessions after it stays open, and nothing is written. A claim the pass cannot read records a fault
  and stays open; a `MarketData` it cannot read records a fault and gives no bars (the 45-day rule
  still applies); either way the pass completes. The thresholds are constants, not settings.

## Type alignment (`TYP`)

- **FORE-TYP-01** — The forecaster payload types carry, at minimum, the fields its own clauses
  require; the clause, not `contracts/forecaster.py`, is the authority on what must be present.
  `ShadowPrediction` carries `model_id`, `subject_ref`, `value`, `confidence`, `shadow`, and
  `provenance` (`FORE-OUT-01`/`FORE-OUT-02`/`FORE-OUT-05`). `Scorecard` carries `model_id`,
  `metrics`, `sample_size`, `fresh_as_of`, and `promotion_eligible`
  (`FORE-OUT-03`/`FORE-OUT-04`).
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

- **FORE-OBS-01** — Each prediction is recorded as **one node**. A `forecast`, `forecast_return`
  or `forecast_factor` reading is a `ShadowPrediction` node, with its model's lineage in a `Model`
  node. A barrier claim is its `BarrierForecast` node, which carries its own `model_id` and
  `model_version` (`FORE-OUT-07`) and writes no `ShadowPrediction` node. *(DRIFT-081; was: a
  `ShadowPrediction` node per prediction.)*
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
    "labels_owned": [
      "ShadowPrediction",
      "Model",
      "ForecasterRun",
      "BarrierForecast",
      "BarrierSettlement",
      "BarrierSettlementPass"
    ],
    "labels_read": [
      "SentimentReading",
      "AnalystRun",
      "BarrierHistory",
      "ScanRun",
      "MarketData"
    ]
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
| `retrain_window_days` | `60` | `int ≥ 20 ≤ 252` | YES | Trailing distinct-date window (trading days) for the rolling IC-decay check |
| `retrain_trigger_fraction` | `0.5` | `float > 0.0 ≤ 1.0` | YES | Fraction of the reference metric below which a retrain is recommended |
| `retrain_horizon_days` | `20` | `int ≥ 1 ≤ 60` | YES | Forward-return horizon the decay trigger and champion comparison score at; the S110 baseline is strongest at h=20 (IC-IR 0.27) |
| `retrain_min_cases` | `500` | `int ≥ 50` | YES | Minimum aligned recent-window observations before a decay verdict is meaningful |
| `factor_name` | `""` | `str` | YES | Approved catalogue factor to shadow; empty keeps approved-factor shadowing disabled |
| `factor_params` | `""` | `str` | YES | Operator-approved catalogue params for that factor, e.g. `lookback=60` |
| `factor_model_id` | `""` | `str` | YES | Optional explicit factor scorecard key; empty derives it from the selection |
| `barrier_min_history_sessions` | `700` | `int ≥ 252 ≤ 2520` | YES | Fewer bars in the provider's history than this and no claim is stated (`FORE-FAIL-04`); the depth itself is the provider's `barrier_history_sessions` (DL-241 D10) |
| `barrier_paths` | `1000` | `int ≥ 100 ≤ 10000` | YES | Simulated paths per barrier claim, as EXP-018; probabilities move in steps of 1 ÷ paths |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| DRIFT-081 | `FORE-IDN-01` names the sentiment and return models as the job; `FORE-OBS-01` writes a `ShadowPrediction` node per prediction; `FORE-IDN-02` lists the labels written | The factor leg (Q5) and the barrier model (S239) are unnamed in `IDN-01`; the barrier prediction is recorded as a `BarrierForecast`, not a `ShadowPrediction` node; the poll writes `ForecasterRun`, which `IDN-02` never listed | CORRECTED: `IDN-02` in v1.7; `IDN-01` (four legs) and `OBS-01` (one node per prediction, by leg) in v1.9 |
| DRIFT-089 | `FORE-FAIL-04`: every refusal *"records a fault"* | Every refusal was recorded at `error`, which `kernel/fault_incidents.py` counts as an open incident, so a designed "no claim" (TXN/COP, the provider's guard, `sched-2026-09-28`) read "Needs you: 2 open incidents" | CORRECTED in v1.8: a designed refusal is a `warning`, a missing or broken input an `error` |
| DRIFT-083 | `FORE-IDM-03`: *"Scorecard methods are read-only over `ShadowPrediction` nodes"* | From v1.7 `barrier_scorecard` reads `BarrierForecast` and `BarrierSettlement` nodes, not `ShadowPrediction` ones; `FORE-IDM-05` governs it | CORRECTED in v1.9: `IDM-03` covers the three shadow scorecards; `IDM-05` keeps the barrier one |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
- v1.1 — S72: added `system_prompt` tunable (ADR-0010 immediate consequence); pre-declared for P13.
- v1.2 — S205 rewrites `FORE-TYP-01` from a file-as-oracle contract assertion into explicit
  required fields for `ShadowPrediction` and `Scorecard`. `FORE-TYP-03` remains a separate
  serialization-shape clause. No contract shape changes.
- v1.3 — DL-203 / work-queue item 33 (2026-09-23): `PARAM` only. Declares the four IC-decay
  retrain knobs and the three approved-factor shadowing fields, all already `tunable()` in
  `settings.py`. No clause moves.
- v1.4 — S239 / DL-241 (2026-09-28): the barrier claim. `FORE-IDN-02` amended (the forecaster also
  writes `BarrierForecast`); new `FORE-IN-07` (the `forecast_barrier` input), `FORE-OUT-07` (the
  three probabilities and the append-only, advisory claim that records them), `FORE-IDM-04` (a
  stable seed; a rerun merges, a conflicting rerun is refused) and `FORE-FAIL-04` (no claim without
  a successful fit on enough history; never fabricated). `CAP` owns `BarrierForecast`; three
  `PARAM` rows. Why: DL-240 manages the book as a distribution, and EXP-018 found the first model
  whose probabilities clear the pre-registered bar; a ledger of its claims is what tests them live.
  `IN-07` and `IDM-04` go beyond the two clauses the spec named: determinism is an `IDM` guarantee,
  and `FORE-IDM-02` concerns the return model only. Silences found are `DRIFT-081`.
- v1.5 — S239 follow-up / DL-241 D9 (2026-09-28, the planner's decision): the trigger. `FORE-TRG-01`
  and `FORE-TRG-02` amended. DL-241 found no deployed process fired the poll, so no `BarrierForecast`
  could ever be written in the fleet (F4 blocked); the forecaster's entrypoint now runs the peers'
  graph-pull loop. The clauses said *"RPC request only"* and *"never self-triggers"*; they now name the
  unconsumed `AnalystRun` as the trigger (an artifact, not a timer) and which legs the deployed loop
  fires: `forecast_barrier` only, because the three advisory legs have never run in the fleet and
  their cost there is unmeasured. No clause is weakened: event subscription and self-triggering stay
  forbidden. Cited tests: `test_forecaster_entrypoint.py::test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only`,
  `test_barrier_poll.py::test_an_unknown_leg_is_refused_before_any_request`, and
  `orchestration/tests/test_forecaster_stage.py::test_the_local_pipeline_still_fires_all_four_legs`.
- v1.6 — S239 second follow-up / DL-241 D10 (2026-09-28, the planner's decision): the route. D9 left
  the deployed barrier leg unable to reach the provider for its bars (F4 blocked). The provider now
  writes a `BarrierHistory` per `AnalystRun` with qualifying buys, and the forecaster reads it:
  `FORE-IN-07` (the bars come only from that node, named by `ForecastRequest.history_ref`, never over
  the bus), `FORE-TRG-01` (the loop waits for the node when the run has a qualifying buy; D11: the deployed loop
  counts only a run created within 24 h),
  `FORE-OUT-07` (the claim records `history_ref`; `confidence` is over the history's
  `sessions_requested`), `FORE-IDM-04` (a rerun keeps the first `history_ref`), `FORE-FAIL-04` (a
  dropped ticker or a failed history refuses as `provider dropped: <reason>`), `FORE-NEV-04` (market
  data comes only from the provider: over the bus, or from a node the provider wrote; read literally,
  the old wording forbade the route). `PARAM`: `barrier_history_sessions` moves to the provider, which
  owns the fetch depth. No clause added; 22 / 49 unchanged.
- v1.7 — S241 / DL-243 (2026-09-28): the settlement and the scorecard. Why: DL-240, nothing sizes or
  exits on a probability until a ledger shows it comes true; S239 states the claims and this sprint
  settles and scores them. `FORE-IDN-02` amended (the forecaster also writes `BarrierSettlement` and the
  per-run `BarrierSettlementPass`, and `ForecasterRun`, which the loop always wrote: the third of
  `DRIFT-081`, prescribed for this amendment); `FORE-TRG-01` amended (the loop's second work, one
  settlement pass per run; the deployed loop's per current run); `FORE-OUT-03` names
  `barrier_scorecard` (it returns the same `Scorecard`). New `FORE-OUT-08` (each claim settled once, by
  EXP-018's rule, from a provider-written `MarketData`, measured from the settling series' own close;
  the scorecard over EXP-018's fixed climatology with its date bootstrap), `FORE-IDM-05` (settled once,
  one pass per run, a repeatable scorecard) and `FORE-FAIL-05` (void with a named reason, never a false
  outcome). `IDM-05` is beyond the spec's list: the spec's C6 cites "`FORE-IDM`", and no existing `IDM`
  clause covers settlement (§7a forbids narrowing one to fit). `CAP` now lists every label the
  forecaster writes and reads (`ForecasterRun`, `AnalystRun` and `BarrierHistory` had gone undeclared).
  `PARAM`: no new setting; the thresholds (0.6, 1.67, 45 days), the horizon, the baseline shares and
  the bootstrap (1,000 draws, seed 20260929) are constants citing the spec and EXP-018. Silences found:
  `DRIFT-083` (`IDM-03`'s subject), `DRIFT-084` (the price adjustment of the bars, unstated where they
  are written).
- v1.8 — S243 / DL-247 (2026-09-29): a refusal's severity. `FORE-FAIL-04` amended: a designed "no
  claim" (the provider dropped the ticker or wrote a failed history, too little history, a fit outside
  EXP-018's rule) records its fault at `warning`; a missing or broken input (no named history, one
  that does not hold the ticker, malformed barriers, an optimiser exception, an absent `arch`) at
  `error`. Why: the clause said only "records a fault", every refusal was an `error`, and
  `kernel/fault_incidents.py` counts `error` as an open incident, so the operator's brief asked for
  them on `sched-2026-09-28` for two designed refusals (TXN, COP; DL-245). A failed history is
  designed because the provider records the failed fetch's own `error`; the forecaster's echo counted
  one outage twice. The fault's `error_type` (`BarrierClaimRefusedError`) does not change. No clause
  added; 25 / 52 unchanged. `DRIFT-089` corrected.
- v1.9 — S251 / DL-259, DL-260 (2026-10-01). `FORE-IDN-01` names the four legs the forecaster runs
  (sentiment, return, approved factor, barrier). `FORE-OBS-01` says each prediction is one recorded
  node: a `ShadowPrediction` for the three shadow legs, a `BarrierForecast` for a barrier claim
  (DRIFT-081, now fully corrected). `FORE-IDM-03` covers the three shadow scorecards, and
  `FORE-IDM-05` keeps the barrier one (DRIFT-083). All three stay ⬜: no test proves the return leg's
  node, and `IDN-01` states a whole purpose. The partial proofs are named in their rows. No behaviour
  change; 25 / 52 unchanged.
- v1.10 — S252 / DL-261 (2026-10-02). `FORE-TRG-01` bounds both graph-pull finders
  by key and processed edge, passing the shared 24 h creation bound before the deployed loop reads
  candidate props. The existing current-run and history-readiness predicates remain; a local call
  without `now` stays unbounded. Why: the two idle polls downloaded every `AnalystRun` separately.
  Payload, backlog, bad-stamp and existing loop tests re-prove the clause; 25 / 52 unchanged.
