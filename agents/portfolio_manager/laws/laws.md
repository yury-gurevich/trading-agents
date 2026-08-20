# `Portfolio Manager` — Laws

**Prefix:** `PM` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Size and risk-check analyst recommendations into concrete order intents — or reject them
> with a documented reason. Never touch the broker.

Each clause has a stable ID (`PM-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

---

## Identity & purpose (`IDN`)

- **PM-IDN-01** — The portfolio manager's sole job is recommendation → sized order intent.
  It checks each recommendation against the current portfolio state (cash, open positions,
  sector exposure) and the regime's risk envelope (sector cap, reward/risk floor), then sizes
  each approved recommendation to whole shares using the estimated entry price. It never
  submits orders to the broker, never calls a market-data API directly, and never promotes
  the execution stage.
- **PM-IDN-02** — The portfolio manager exclusively owns the `PMRun`, `OrderIntent`,
  `Rejection`, and `OrderIntentResult` graph labels. No other agent writes to these labels.

---

## Inputs (`IN`)

- **PM-IN-01** — `evaluate_orders` accepts a `RecommendationSet` (from `contracts/analyst.py`):
  `run_id`, `recommendations`, `rejections`, `explanation`, `provenance`. All fields must pass
  Pydantic validation before any sizing begins.
- **PM-IN-02** — In pub/sub mode the PM subscribes to `analysis.recommendations.ready`; it
  resolves the claim-check reference to a `RecommendationSet` before calling `evaluate_orders`.
  The event is authoritative; unknown extra fields are ignored.
- **PM-IN-03** — An empty `RecommendationSet` (zero recommendations) → empty `OrderIntentSet`
  with reason `"no_recommendations"`. No provider calls are made; no graph nodes are written.
- **PM-IN-04** — `explain_decision` accepts a `RecommendationSet`; returns an `Explanation`
  of the sizing and risk logic. No provider call, no graph write.

---

## Triggers (`TRG`)

- **PM-TRG-01** — RPC capability `evaluate_orders`: invoked on demand by any caller in
  `allowed_callers`. Pull mode; returns an `OrderIntentSet` synchronously.
- **PM-TRG-02** — Pub/sub: `analysis.recommendations.ready` event auto-invokes
  `evaluate_orders`; the result is written via claim-check and `portfolio.orders.ready` is
  published. This is the primary production trigger path.
- **PM-TRG-03** — The PM never self-triggers. Idle (no inbound request or event) → zero
  provider calls, zero graph writes.

---

## Outputs (`OUT`)

- **PM-OUT-01** — `evaluate_orders` always returns an `OrderIntentSet`: `run_id`, `approved`
  (tuple of `OrderIntent`), `rejected` (tuple of `RejectedOrder`), `portfolio_state_snapshot`,
  `explanation`, `provenance`. Every recommendation is accounted for in one of the two tuples
  (or in the empty-result path).
- **PM-OUT-02** — Each approved `OrderIntent` carries: `ticker`, `action`, `quantity ≥ 1`
  (whole shares), `est_price` (Decimal — exact money type), `stop_pct`, `target_pct`,
  `pm_run_id`, and `provenance`.
- **PM-OUT-03** — Each `RejectedOrder` carries the original recommendation plus a `reason`
  string that names the gate that blocked it (`"max_positions"`, `"sector_cap"`,
  `"reward_risk_below_floor"`, `"provider_degraded"`, etc.). Silence is always attributed.
- **PM-OUT-04** — If the provider is unavailable, all recommendations are rejected with reason
  `"provider_unavailable"` and a fault is recorded. An empty `OrderIntentSet` is returned.
- **PM-OUT-05** — In pub/sub mode the outbound `portfolio.orders.ready` event carries only a
  claim-check reference; the `OrderIntentSet` payload lives in the graph.
- **PM-OUT-06** — `portfolio_state_snapshot` in the result captures the post-evaluation cash,
  open positions, and sector weights at the moment the intents were computed. This snapshot
  is the inputs for the next PM run's reconciliation; it is never a live broker query.

---

## Prohibitions (`NEV`)

- **PM-NEV-01** — Never sends orders to the broker directly. The PM's output is an
  `OrderIntentSet` — a plan, not an execution. Only the execution agent bridges to the broker.
- **PM-NEV-02** — Never calls a market-data API directly. Estimated entry prices are obtained
  from the provider's `get_market_data` capability via the bus.
- **PM-NEV-03** — Never promotes the execution stage (`promote_stage` is the execution
  agent's gated capability, not the PM's).
- **PM-NEV-04** — Never approves a recommendation that has not passed every configured risk
  gate. Partial gate bypasses are not possible — all gates are applied before approval.
- **PM-NEV-05** — Never outputs fractional shares. `quantity` is always a whole-number
  integer ≥ `min_order_quantity` (default 1). Fractional math is truncated, not rounded.
- **PM-NEV-06** — Never opens more than `max_names_per_sector` distinct **issuers** in any one
  sector label, independent of the dollar cap. The label is whatever classification the sector
  source supplies; it is **not** guaranteed to be GICS level 1, and the cap must be set for the
  granularity actually received — finer labels scatter one bet across more buckets and make a fixed
  count cap weaker, not stronger. This is a **label-bucket cap, not the correlation penalty**:
  correlation is measured, not labelled, and is enforced by `PM-NEV-08`. `0` disables the gate;
  already-held issuers in the label count toward the limit.
- **PM-NEV-07** — Never counts two share classes of one issuer as two names or two exposures.
  Every concentration gate — position count, sector-label count, sector weight, correlated-cluster
  weight — aggregates by issuer key before it counts or weighs. The issuer key comes from the
  trading pack's issuer map; a ticker absent from the map is its own issuer, which is the correct
  default for a single-class name and is **not** a not-evaluated outcome. The map's completeness is
  a pack-data concern, not an agent one.
- **PM-NEV-08** — Never approves an order that would push the weight of one **correlated cluster**
  above `max_correlated_cluster_pct`. A cluster is the candidate issuer plus every held issuer whose
  pairwise return correlation with it, over `correlation_lookback_days`, is at least
  `correlation_threshold`. Correlation is computed from bars the run already carries; the PM never
  fetches market data to obtain it (`PM-NEV-02`). This clause is the correlation penalty; the
  label-bucket count of `PM-NEV-06` is not.
- **PM-NEV-09** — Never records a concentration gate it could not evaluate as passed. When the
  sector label is missing, or fewer than `min_correlation_bars` overlapping bars exist for a pair,
  the gate emits an explicit **not-evaluated** outcome naming the missing input. An absent outcome
  and a passing outcome are never the same value. Every not-evaluated outcome appears in
  `gate_report` (`PM-OBS-01`) so a reader can tell a gate that passed from a gate that never ran.

---

## State & effects (`STA`)

- **PM-STA-01** — `PortfolioState` is maintained in-process (cash, positions dict, sector
  weights). It is not persisted between process restarts; it is reconstructed from the graph
  on startup.
- **PM-STA-02** — Every `evaluate_orders` call writes a `PMRun` node, one `OrderIntent` node
  per approved order, and one `Rejection` node per rejected recommendation. All writes are
  append-only; no prior record is modified.
- **PM-STA-03** — The in-process `PortfolioState` is mutated during a run to reflect
  tentatively approved intents (so position cap and sector cap are enforced across candidates
  within the same run). The mutation is not visible to concurrent requests; the PM is
  single-tenant within a container.
- **PM-STA-04** — The graph write of an `OrderIntentResult` node captures the final
  `portfolio_state_snapshot` after the run completes.

---

## Determinism & idempotency (`IDM`)

- **PM-IDM-01** — Given identical `RecommendationSet`, `MarketData`, and starting
  `PortfolioState`, the sizing and gate logic is fully deterministic: same input → same
  `OrderIntentSet`.
- **PM-IDM-02** — `run_id` is taken from the input `RecommendationSet` and threaded through.
  Re-running appends a new `PMRun` record (append-only); the caller is responsible for not
  duplicating triggers.

---

## Ordering & concurrency (`ORD`)

- **PM-ORD-01** — Recommendations are evaluated in iteration order; the position cap and
  sector cap enforce ordering effects (first-approved takes priority). The same
  `RecommendationSet` with the same ordering always produces the same `OrderIntentSet`.
- **PM-ORD-02** — Concurrent `evaluate_orders` requests would share the in-process
  `PortfolioState` and are **not safe** under true parallelism. The PM is designed for
  single-threaded, single-container operation.

---

## Failure, recovery & rollback (`FAIL`)

- **PM-FAIL-01** — Provider unavailable (no price data or regime) → all recommendations
  rejected with `"provider_unavailable"`; fault recorded; no exception propagates to caller.
- **PM-FAIL-02** — Per-recommendation evaluation exception → that recommendation is rejected
  with `"evaluation_error"`; remaining recommendations proceed normally.
- **PM-FAIL-03** — Graph write failure → fault recorded; the `OrderIntentSet` computed in
  memory is still returned to the caller. Safe to retry: a repeated write appends a second
  `PMRun` record (append-only).

---

## Type alignment (`TYP`)

- **PM-TYP-01** — `OrderIntent.est_price` is a `Decimal` (exact money type, 8 decimal places
  max). Never a `float`. This prevents rounding errors in downstream sizing math.
- **PM-TYP-02** — `OrderIntent.quantity` is a positive `int ≥ 1`; `stop_pct` and `target_pct`
  are `float ∈ [0.0, 1.0]`; stop is always strictly less than target.
- **PM-TYP-03** — The PM's payload types carry, at minimum, the fields its own clauses require.
  They are *defined* in `contracts/portfolio_manager.py`, but **the clause, not the file, is the
  authority on what must be present** — "matches the file" is unfalsifiable, because the file would
  then be both the claim and the oracle. `OrderIntentSet` carries `run_id`, `approved`, `rejected`,
  `portfolio_state_snapshot`, `explanation`, `provenance` (`PM-OUT-01`). `OrderIntent` carries
  `ticker`, `action`, `quantity`, `est_price`, `stop_pct`, `target_pct`, `pm_run_id`, `provenance`,
  and `gate_report` (`PM-OUT-02`). `RejectedOrder` carries the originating recommendation, a
  `reason`, and `gate_report` (`PM-OUT-03`). `GateOutcome` carries the gate name, the value, the
  threshold, the detail, and an outcome that can express **passed, failed, and not-evaluated as
  three distinct values** (`PM-NEV-09`) — a two-state boolean cannot satisfy this clause.
  `CONTRACT.version` is the authoritative version string; `gate_report` is additive and defaults to
  empty for older payloads.

---

## Security & privilege (`SEC`)

- **PM-SEC-01** — The PM holds no credentials and makes no external API calls. Its blast
  radius if compromised is mis-sized or policy-violating order intents flowing to execution —
  it cannot submit broker orders directly.
- **PM-SEC-02** — Only callers in the declared `allowed_callers` list (analyst, dispatcher,
  operator, supervisor) may invoke `evaluate_orders`. The bus enforces `caller_authorized`
  at receipt.
- **PM-SEC-03** — The PM is quarantinable: removing its `analysis.recommendations.ready`
  subscription stalls the pipeline at the sizing gate without corrupting persisted state.

---

## Dependencies (`DEP`)

- **PM-DEP-01** — `DEP-BUS`: requires request/reply (provider calls) and subscribe/publish
  (`analysis.recommendations.ready` / `portfolio.orders.ready`).
- **PM-DEP-02** — `DEP-POSTGRES`: requires graph append-write access for `PMRun`, `OrderIntent`,
  `Rejection`, `OrderIntentResult`; claim-check read for `analysis.recommendations.ready`.
- **PM-DEP-03** — `DEP-FEED` (via provider): the provider's `get_market_data` and
  `get_regime` capabilities must be reachable for price estimates and the sector/RR gate.
  Provider degradation causes a full rejection pass, not a crash.

---

## Observability & audit (`OBS`)

- **PM-OBS-01** — Every `PMRun` node in the graph is fully reconstructable: input
  recommendations, per-recommendation `gate_report` outcomes (gate name, value,
  threshold, pass/fail, detail), reason strings, estimated prices used, and the final
  `OrderIntentSet`. The `portfolio_state_snapshot` captures pre- and post-run state on
  the `OrderIntentResult` node.
- **PM-OBS-02** — Faults (provider degradation, per-evaluation errors) are routed to the
  central fault channel. Every rejection has an attributed reason; no silence, no mystery.

---

## Performance envelope (`PERF`)

- **PM-PERF-01** — The PM's latency budget is dominated by one provider round-trip (price
  - regime). The risk-gate math and sizing computation are pure in-process Python and add
  negligible latency for typical candidate sets (≤ 5 items from the analyst).

---

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["request_reply", "subscribe", "publish", "claim_check_read"],
    "topics": {
      "subscribe": ["analysis.recommendations.ready"],
      "publish": ["portfolio.orders.ready"]
    },
    "delivery": "at_least_once",
    "schema_version": "1.0"
  },
  "graph": {
    "operations": ["append_write", "claim_check_read"],
    "labels": ["PMRun", "OrderIntent", "Rejection", "OrderIntentResult"],
    "access": "write_own_labels_only"
  }
}
```

**Allowed callers for `evaluate_orders`:** `analyst`, `dispatcher`, `supervisor`, `operator`
**Allowed callers for `explain_decision`:** `dispatcher`, `supervisor`, `operator`, `researcher`

---

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `starting_cash` | `100000.00` | `Decimal ≥ 0` (USD) | YES | Paper account size; all position limits are derived as fractions of this |
| `max_position_pct` | `0.10` | `float ≥ 0.01, ≤ 1.0` | YES | Single-name cap at 10 % of portfolio; caps concentration risk |
| `max_positions` | `10` | `int ≥ 1, ≤ 50` | YES | Maximum concurrent open positions; caps correlation exposure |
| `cash_buffer_pct` | `0.05` | `float ≥ 0.0, ≤ 0.50` | YES | Reserve fraction of cash never deployed; covers fees and slippage |
| `min_order_quantity` | `1` | `int ≥ 1` (shares) | YES | Minimum order size; prevents sub-1-share intents |
| `price_lookback_days` | `7` | `int ≥ 1, ≤ 30` (days) | YES | How far back to look for a valid close price from the provider |
| `min_reward_risk_ratio` | `1.5` | `float ≥ 0.0, ≤ 20.0` | YES | Minimum R/R ratio; target pct ÷ stop pct must exceed this or reject |
| `max_sector_pct` | `0.30` | `float ≥ 0.0, ≤ 1.0` | YES | Maximum portfolio weight in any single sector label, counted over held **and** in-run issuers |
| `max_names_per_sector` | `3` | `int ≥ 0, ≤ 500` | YES | Max distinct issuers per sector label; a label-bucket cap, **not** the correlation penalty (`PM-NEV-08`); set it for the granularity the sector source actually returns; 0 disables |
| `correlation_lookback_days` | `120` | `int ≥ 20, ≤ 250` (days) | YES | Bars used for the pairwise return correlation — long enough to be stable, short enough to track the current regime; runs already carry ~200 bars, so this costs no fetch |
| `correlation_threshold` | `0.70` | `float ≥ 0.0, ≤ 1.0` | YES | Pairwise return correlation at or above which two issuers are treated as one bet |
| `max_correlated_cluster_pct` | `0.25` | `float ≥ 0.0, ≤ 1.0` | YES | Max portfolio weight in one correlated cluster; tighter than `max_sector_pct` because a measured cluster is a truer bet boundary than a label |
| `min_correlation_bars` | `60` | `int ≥ 20, ≤ 250` (bars) | YES | Minimum overlapping bars for a usable estimate; below it the pair is **not evaluated** (`PM-NEV-09`), never silently passed |
| `issuer_map` | pack data | `mapping ticker → issuer key` | NO (pack data) | Owned by the trading pack (ADR-0012), not the agent; collapses share classes of one issuer to one key. Absence means single-class, which is the common case |

---

## Divergence register

| ID | Law says | PRD / code says | Decision needed |
| --- | --- | --- | --- |
| D-PM-1 | `PM-NEV-06` counts distinct **issuers**; `PM-NEV-07` aggregates share classes. | No issuer mapping exists anywhere in the repo; GOOG and GOOGL consume two of three slots as if they were two independent bets. | **DECIDED (ADR-0023)** — issuer map ships as trading-pack data. Central: DRIFT-042. |
| D-PM-2 | `PM-NEV-08` enforces a measured correlation cap against the held book. | The PM receives tickers, quantities, sector labels, cash and portfolio value — and nothing else. `beta` is computed by the scanner and never forwarded. There is no correlation input of any kind. | **DECIDED (ADR-0023)** — computed from the ~200 bars each run already carries; no new feed. Central: DRIFT-043. |
| D-PM-3 | `PM-NEV-09` forbids recording an unevaluable gate as passed. | `concentration.py:55-57` returns an empty outcome tuple when a ticker has no sector label, and an empty tuple is indistinguishable from a passed gate. | **DECIDED (ADR-0023)** — explicit not-evaluated outcome. Central: DRIFT-044. |
| D-PM-4 | `max_sector_pct` caps portfolio weight in a sector label. | `SectorBook.__init__` seeds `_names` from held positions but never `_deployed`, so the dollar cap sees only the current batch. Masked today because the name count binds first. | **DECIDED (ADR-0023)** — must land with the name-count fix or the dollar cap silently becomes the weak gate. Central: DRIFT-045. |
| D-PM-5 | `PM-TYP-03` requires `GateOutcome` to express passed, failed and not-evaluated as three distinct values. | `contracts/portfolio_manager.py` declares `passed: bool` — two states. The clause is unexpressible in the contract that carries its evidence, and no test fails. | **DECIDED (DL-121)** — contract gains a third state in the same sprint as `PM-NEV-09`. Central: DRIFT-046. |

---

## Changelog

- v1 — drafted (ideal-design) and **LOCKED (S70)**. (The earlier "v0 — not yet locked" footer was
  stale; reconciled in the DL-19 cage audit — see drift-register DRIFT-010.)
- v1.1 — amendment: added PM-NEV-06 (per-sector name-count cap, `max_names_per_sector`) — the
  name-correlation penalty the dollar cap missed; closes the gap the deliberation firewall
  surfaced (EXP-004..006) and the live book exposed (4 correlated semis). Cited test:
  `test_sector_name_count.py`.
- v1.2 — amendment: added additive `OrderIntent.gate_report` with explicit PM risk-gate
  outcomes for deliberation evidence completeness (DL-41 / S114). Cited tests:
  `test_portfolio_manager_audit.py::test_order_intent_emits_pm_gate_report` and
  `tests/test_veto_context.py::test_context_completeness_renders_every_enforced_gate_with_outcome`.
- v1.3 — amendment (ADR-0023 / DL-121, 2026-08-20). **Two claims in `PM-NEV-06` were measured
  false and are withdrawn**: the labels are not GICS level 1 (the source returns 30
  industry-granularity labels, and 11 was assumed), and the count cap is **not** the
  name-correlation penalty (the mega-cap cluster scatters across five labels, so the cap admits
  3 × 5 = 15 correlated names before firing once). The duty those claims asserted does not
  disappear — it moves to new clauses that start ⬜ unproven, so the amendment adds asserted truth
  rather than removing it. Added `PM-NEV-07` (aggregate by issuer before counting), `PM-NEV-08`
  (measured correlated-cluster cap — this is the correlation penalty), `PM-NEV-09` (a gate that
  could not evaluate says so, never a silent pass). **`PM-TYP-03` rewritten** from *"matches
  `contracts/portfolio_manager.py` exactly"* — unfalsifiable, since the file was both claim and
  oracle — to an enumeration of the fields each payload must carry, including a `GateOutcome`
  able to express **not-evaluated** as a third value. New PARAM rows:
  `correlation_lookback_days`, `correlation_threshold`, `max_correlated_cluster_pct`,
  `min_correlation_bars`, `issuer_map` (NO — pack data). All new clauses are ⬜ until a functional
  test cites them; no green was moved by this amendment.
