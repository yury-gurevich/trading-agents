# `Execution` — Laws

**Prefix:** `EXEC` · **status:** LOCKED v1.4 · **Owner:** Yury Gurevich

> Be the single, auditable, idempotent broker boundary. Execute only what the portfolio
> manager has approved and the stage gate allows.

Each clause has a stable ID (`EXEC-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

---

## Identity & purpose (`IDN`)

- **EXEC-IDN-01** — The execution agent is the sole broker interface. Its job is to convert
  approved `OrderIntent` records into idempotent broker submissions, capture `Fill` records,
  and provide reconciliation and stage-transition primitives. It never decides what to trade,
  never overrides quantities, and never skips the idempotency key.
- **EXEC-IDN-02** — The execution agent exclusively owns the `Fill`, `Reconciliation`,
  `StageTransition`, and `ExecutionResultEvent` graph labels. No other agent writes to these
  labels.
- **EXEC-IDN-03** — The execution agent also exclusively owns the broker-boundary evidence
  labels `BrokerStopOrder` (ADR-0015 §3 resting protective stops), `BrokerPositionSnapshot`
  (the run-start holdings snapshot, DL-44) and `BrokerOrderStatus` (append-only broker
  order-status reads). No other agent writes to these labels. *(Declares capability decided in
  ADR-0015 §3 and DL-44; see changelog v1.1.)*

---

## Inputs (`IN`)

- **EXEC-IN-01** — `submit` accepts an `OrderIntentSet` (from `contracts/portfolio_manager.py`):
  `run_id`, `approved`, `rejected`, `pm_run_id`, `provenance`. Only the `approved` tuple is
  submitted; `rejected` entries are recorded for provenance only.
- **EXEC-IN-02** — `execute_close` accepts a `CloseDecisionSet` (from monitor): a set of
  position-close decisions with ticker, quantity, and reason. Every entry must have a
  non-empty `close_reason`.
- **EXEC-IN-03** — In pub/sub mode the execution agent subscribes to `portfolio.orders.ready`;
  it resolves the claim-check reference to an `OrderIntentSet` before calling `submit`. The
  event is authoritative; unknown extra fields are ignored.
- **EXEC-IN-04** — `promote_stage` requires `confirmed=True` in the `PromoteStageRequest` to
  take effect. A request with `confirmed=False` is a dry-run: it returns what the transition
  _would_ do without writing a `StageTransition` node or mutating the live stage.

---

## Triggers (`TRG`)

- **EXEC-TRG-01** — RPC `submit`: invoked on demand by the portfolio manager or dispatcher.
  Checks the stage gate and submits approved intents to the broker.
- **EXEC-TRG-02** — Pub/sub: `portfolio.orders.ready` event auto-invokes `submit`; fills are
  written and `execution.fills.ready` is published with the `pm_run_id` threaded through.
  This is the primary production trigger path.
- **EXEC-TRG-03** — RPC `execute_close`: invoked on demand by the monitor to close open
  positions. Goes through the same stage gate as `submit`.
- **EXEC-TRG-04** — RPC `reconcile`: invoked on demand by the supervisor to reconcile
  in-process fill records against the broker's reported fills.
- **EXEC-TRG-05** — RPC `stage_status`: read-only; returns the current stage without side
  effects. Safe to call from any authorised caller.
- **EXEC-TRG-06** — RPC `promote_stage`: invoked on demand by the supervisor to advance the
  execution stage. Requires `confirmed=True`; writes a `StageTransition` node.
- **EXEC-TRG-07** — Run-start reconciliation (`position_sync`): on an unconsumed `RunRequest`
  the execution agent reconciles holdings against the broker and writes exactly one
  `BrokerPositionSnapshot` for the run **before** downstream scoring is released. The snapshot
  is the run's foundation: any cleanup performed alongside it is separately contained and may
  never prevent it (DL-79). *(Declares capability decided in DL-44; see changelog v1.1.)*

---

## Outputs (`OUT`)

- **EXEC-OUT-01** — `submit` always returns an `ExecutionResult`: `run_id`, `stage`, `fills`
  (tuple of `Fill`), `submitted` count, `rejected` count (stage-gate rejections, not
  portfolio rejections), `pm_run_id`, `provenance`.
- **EXEC-OUT-02** — Each `Fill` carries: `ticker`, `side`, `quantity`, `price` (Decimal),
  `broker_order_id`, `client_order_id` (idempotency key), `status`, `timestamp`, `stage`.
- **EXEC-OUT-03** — If the current stage is not in `{"paper", "broker_shadow"}`, every intent
  is rejected with reason `"live_gate_rejected"` and zero fills are submitted. The
  `ExecutionResult` still returns with `submitted=0`.
- **EXEC-OUT-04** — `reconcile` returns a `ReconcileResult`: `run_id`, `matched`, `discrepancies`
  (list of unmatched in-process fills), `provenance`. A `Reconciliation` node is written.
- **EXEC-OUT-05** — `promote_stage` returns a `PromoteStageResult` with `from_stage`,
  `to_stage`, `evidence_summary`, `dry_run`. When not dry-run, a `StageTransition` node is
  written to the graph.
- **EXEC-OUT-06** — `execution.fills.ready` pub/sub event carries only a claim-check
  reference, not the `ExecutionResult` payload. `pm_run_id` is included in the event envelope
  for downstream routing.
- **EXEC-OUT-07** — A decision that did not fill in the session it was decided for is
  **dropped**, and `dropped` is an outcome distinct from `rejected` (broker or stage refusal)
  and `skipped` (never submitted). Drop evidence is append-safe: `Fill.drop_reason` and
  `Fill.dropped_at` plus an append-only `BrokerOrderStatus` drop fact. The broker's normalised
  account of the order stays in `Fill.broker_status` and a **raw terminal reason is never
  written into it** — two vocabularies in that one property is what stalled the fleet on
  2026-07-30. *(Declares capability decided in ADR-0018; shape settled by S151/DL-79.)*
- **EXEC-OUT-08** — Every submitted order records its price-tolerance evidence durably: the
  selected mode, the decided price, the **applied** tolerance and limit price, and the
  **counterfactual** mode, tolerance and limit price for the band that was not used. The
  counterfactual is evidence only and never reaches the broker. *(Declares capability decided
  in ADR-0013 champion–challenger; shipped off by default in S149.)*
- **EXEC-OUT-09** — Every graph-pull `ExecutionRun` records the deliberation posture that was
  in force (`advisory` or `binding`), the deliberation status that occurred
  (`applied`, `applied_failed_open`, `not_required`, `waiting`, or
  `proceeded_unvetoed`), and the count of buy intents blocked by that posture. The status answers
  what happened to the review; the posture answers the operator policy that decided what to do
  about it. *(Declares capability decided in S185 / DL-128.)*

---

## Prohibitions (`NEV`)

- **EXEC-NEV-01** — Never decides what to trade. The execution agent only executes intents
  approved by the portfolio manager; it has no scoring, sizing, or selection logic.
- **EXEC-NEV-02** — Never overrides the quantity or side from an `OrderIntent`. The
  `Fill.quantity` matches the `OrderIntent.quantity` exactly (subject to broker partial fill).
- **EXEC-NEV-03** — Never skips the idempotency key (`client_order_id`) on any submission.
  Every broker call carries a unique, stable key derived from the `OrderIntent.intent_id`;
  a duplicate submission is caught by the broker, not silently doubled.
- **EXEC-NEV-04** — Never auto-promotes beyond `"broker_shadow"` without `confirmed=True`
  plus evidence-gate passage (min_promotion_runs and min_approval_rate satisfied). The
  stage-gate escalation path requires explicit operator/supervisor action.
- **EXEC-NEV-05** — Never logs or returns the Alpaca API key, secret, or base URL in any
  capability response, graph node, or fault record. Credentials are settings only.
- **EXEC-NEV-06** — Under `deliberation_posture="binding"`, execution never opens buy exposure
  from a PMRun whose `DeliberationRun` did not arrive after the bounded grace; those buy intents
  are skipped with evidence instead of reaching the broker. Exits are never delayed or dropped by
  deliberation posture, and an arrived veto is still honoured exactly as an upstream block.
  *(Declares capability decided in S185 / DL-128; preserves ADR-0017 and ADR-0022.)*

---

## State & effects (`STA`)

- **EXEC-STA-01** — Fill records are held in an in-process `_recorded` dict (keyed by
  `client_order_id`) for reconciliation. The graph is the durable record; the in-process
  dict is a working cache rebuilt on startup from the graph.
- **EXEC-STA-02** — Stage is graph-authoritative. The execution agent reads the current stage
  from the graph on every capability call; it does not cache stage in process memory between
  calls. Stage transitions are atomic graph writes.
- **EXEC-STA-03** — All graph writes are append-only. `Fill`, `Reconciliation`,
  `StageTransition`, and `ExecutionResultEvent` nodes are never modified after creation.
- **EXEC-STA-04** — A `StageTransition` node is the only record of a stage promotion. It
  includes `from_stage`, `to_stage`, `promoted_by`, `promoted_at`, and `evidence_summary`.
- **EXEC-STA-05** — **Broker-status refresh terminates.** `Fill.status` is written once at
  submit and, under the append-only store, can never change; the broker's account lives in
  `Fill.broker_status`. A `Fill` whose `broker_status` is **terminal** (`filled` or `rejected`)
  is settled: it is not re-read from the broker and no further `BrokerOrderStatus` fact is
  appended for it. `partial` is **not** terminal and continues to refresh. Selecting settled
  fills as pending work is unbounded write growth, not idempotence. *(Declares the boundary
  implied by ADR-0014 and left open by DL-44; closed by S154.)*
- **EXEC-STA-06** — A realized-PnL conclusion the agent **cannot** resolve is durable, not
  repeated: `Fill.pnl_unresolved_at` is written once, and the accompanying fault is emitted on
  that pass only. A marked fill is never re-evaluated for realized PnL, and the marker never
  asserts a PnL figure. *(Declares the evidence shape decided in the S154 spec and DL-81.)*

---

## Determinism & idempotency (`IDM`)

- **EXEC-IDM-01** — Submitting the same `OrderIntentSet` twice produces the same broker
  behaviour: the second submission is rejected by the broker (duplicate `client_order_id`).
  The execution agent records both attempts; the second is flagged as `"duplicate"`.
- **EXEC-IDM-02** — `client_order_id` is derived deterministically from
  `OrderIntent.intent_id`; it is stable across retries and process restarts.

---

## Ordering & concurrency (`ORD`)

- **EXEC-ORD-01** — `OrderIntent` entries within a single `submit` call are submitted
  sequentially; no parallel broker calls within one `submit`. The order of submission matches
  the order of `approved` in the `OrderIntentSet`.
- **EXEC-ORD-02** — Concurrent `submit` calls from different callers are not safe (shared
  `_recorded` dict). The execution agent is designed for single-container, single-threaded
  operation.

---

## Failure, recovery & rollback (`FAIL`)

- **EXEC-FAIL-01** — Broker timeout or rejection for a single order → `Fill` with
  `status="rejected"` is recorded; the next order in the set continues. No exception
  propagates to the caller; the `ExecutionResult` reflects the partial outcome.
- **EXEC-FAIL-02** — Broker total unavailability → all `OrderIntent` entries result in
  `Fill(status="rejected")`; `ExecutionResult.submitted=0`; fault recorded.
- **EXEC-FAIL-03** — Graph write failure → fault recorded; fills already held in-process
  are safe (idempotency key prevents re-submission to broker). Safe to retry: a repeated
  graph write appends a new record.
- **EXEC-FAIL-04** — Process restart → in-process `_recorded` dict is rebuilt from the
  `Fill` nodes in the graph. No fills are lost; idempotency is maintained via the graph.

---

## Type alignment (`TYP`)

- **EXEC-TYP-01** — `Fill.price` is a `Decimal` (exact money type). Never a `float`.
  Broker-returned price strings are parsed to `Decimal` before persisting.
- **EXEC-TYP-02** — `Fill.status` is one of the literal string union
  `{"filled", "partial", "rejected", "pending"}`; no other values are written.
- **EXEC-TYP-03** — `ExecutionResult`, `Fill`, `ReconcileResult`, `StageStatus`, and
  `PromoteStageResult` match `contracts/execution.py` exactly; `CONTRACT.version` is the
  authoritative version string.

---

## Security & privilege (`SEC`)

- **EXEC-SEC-01** — Alpaca API key and secret live in `ExecutionSettings` (Pydantic secret
  fields). They are never included in graph nodes, log lines, capability responses, or fault
  records.
- **EXEC-SEC-02** — The blast radius of a compromised execution agent is direct unauthorized
  order submission to the broker. This makes the execution agent the highest-privilege
  component; it must be isolated behind the `allowed_callers` gate.
- **EXEC-SEC-03** — Only callers in `allowed_callers` for `submit` (portfolio_manager,
  dispatcher, supervisor) may trigger broker submissions. `promote_stage` is restricted to
  supervisor and operator.
- **EXEC-SEC-04** — The stage gate is the primary blast-radius limiter. Paper stage limits
  exposure to the paper broker only. Promotion to any live stage requires explicit multi-step
  approval (min_promotion_runs + min_approval_rate + confirmed=True).
- **EXEC-SEC-05** — The execution agent is quarantinable: removing its
  `portfolio.orders.ready` subscription freezes the pipeline at the broker boundary without
  corrupting any in-flight data.

---

## Dependencies (`DEP`)

- **EXEC-DEP-01** — `DEP-BUS`: requires subscribe/publish (`portfolio.orders.ready` /
  `execution.fills.ready`) and claim-check resolve for the inbound intent.
- **EXEC-DEP-02** — `DEP-POSTGRES`: requires graph append-write for `Fill`, `Reconciliation`,
  `StageTransition`, `ExecutionResultEvent`; read for stage-authoritative lookup.
- **EXEC-DEP-03** — `DEP-BROKER` (Alpaca paper API): the execution agent's core I/O boundary.
  Alpaca timeout is bounded by `alpaca_timeout` (default 15 s). Broker unavailability causes
  fill failures, not a crash.
- **EXEC-DEP-04** — `DEP-POSTGRES`: graph append-write for the broker-boundary evidence labels
  `BrokerStopOrder`, `BrokerPositionSnapshot` and `BrokerOrderStatus`; read for stop liveness
  and holdings reconciliation. `DEP-BROKER` additionally requires order cancellation and
  stop-order placement, not submission alone. *(Declares capability decided in ADR-0015 §3,
  ADR-0018 and DL-44.)*

---

## Observability & audit (`OBS`)

- **EXEC-OBS-01** — Every fill, every reconciliation outcome, and every stage transition is
  fully reconstructable from the graph. `ExecutionResultEvent` nodes cross-reference the
  originating `pm_run_id` and `intent_id` for end-to-end provenance.
- **EXEC-OBS-02** — Broker rejections, timeouts, and stage-gate rejections are all routed to
  the central fault channel. No broker interaction is silent: all outcomes (filled, partial,
  rejected) are recorded.
- **EXEC-OBS-03** — The protective-stop lifecycle is fully reconstructable: placement is an
  immutable `BrokerStopOrder` fact, cancellation is a `cancelled_at` marker (never a deletion),
  and the broker remains truth for liveness. A held position that ends a run with **no live
  broker stop** is surfaced as an `UnprotectedPosition` fault and retried on the next run — a
  refusal is never recorded once and then forgotten. *(Declares capability decided in
  ADR-0015 §3; the silence it forbids is the defect S146 fixed.)*
- **EXEC-OBS-04** — Deliberation fail-open evidence is severity-aligned with the recorded
  posture: an unreviewed submission under `advisory` is a warning with a recorded reason and
  posture, while the same absence under `binding` is an error. Acceptance can therefore
  distinguish an expected advisory outage from a binding policy breach without muting the
  evidence. *(Declares capability decided in S185 / DL-128.)*
- **EXEC-OBS-05** — Liveness of an execution broker fact is asked in exactly one place. A
  `BrokerStopOrder` whose order has reached a terminal broker state is not live regardless of
  `cancelled_at`; a resting-stop `Fill` is not an open order; and the stale-order sweep asks the
  broker the same liveness question it asks of the graph. *(Declares the S190 / DL-139 correction
  for DRIFT-055.)*

---

## Performance envelope (`PERF`)

- **EXEC-PERF-01** — Each broker order submission is bounded by `alpaca_timeout` (default
  15 s). Sequential submission of a typical 5-order set completes within 75 s in the worst
  case. No external I/O beyond the broker is performed during `submit`.

---

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["subscribe", "publish", "claim_check_read"],
    "topics": {
      "subscribe": ["portfolio.orders.ready"],
      "publish": ["execution.fills.ready"]
    },
    "delivery": "at_least_once",
    "schema_version": "1.0"
  },
  "graph": {
    "operations": ["append_write", "read"],
    "labels": [
      "Fill",
      "Reconciliation",
      "StageTransition",
      "ExecutionResultEvent",
      "BrokerStopOrder",
      "BrokerPositionSnapshot",
      "BrokerOrderStatus"
    ],
    "access": "write_own_labels_only"
  },
  "broker": {
    "operations": [
      "submit_order",
      "list_fills",
      "list_positions",
      "place_stop_order",
      "cancel_order"
    ],
    "provider": "alpaca",
    "schema_version": "alpaca_v2",
    "auth": "api_key_secret_from_settings"
  }
}
```

**Allowed callers for `submit`:** `portfolio_manager`, `dispatcher`, `supervisor`
**Allowed callers for `execute_close`:** `monitor`, `supervisor`
**Allowed callers for `reconcile`:** `supervisor`, `operator`
**Allowed callers for `stage_status`:** `supervisor`, `operator`, `dispatcher`, `researcher`
**Allowed callers for `promote_stage`:** `supervisor`, `operator`

---

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `stage` | `"paper"` | `str` — config-file only | NO (config) | Stage is set by the operator in the config file, not in code; promotion requires `promote_stage` |
| `slippage_bps` | `0` | `int ≥ 0, ≤ 100` (basis points) | YES | Simulated slippage on paper fills; 0 = no adjustment |
| `close_quantity` | `1` | `int ≥ 1` (shares) | YES | Default close quantity when monitor does not specify |
| `close_reference_price` | `1.00` | `Decimal ≥ 0` (USD) | YES | Reference price for close orders in test/paper mode |
| `min_promotion_runs` | `10` | `int ≥ 1` | YES | Minimum completed runs before promotion past "broker_shadow" is allowed |
| `min_approval_rate` | `0.70` | `float ∈ (0, 1]` | YES | Minimum fraction of approved (non-gate-rejected) fills over min_promotion_runs |
| `alpaca_api_key` | — | `SecretStr` | NO (secret) | Alpaca paper API key; never logged or returned |
| `alpaca_secret_key` | — | `SecretStr` | NO (secret) | Alpaca paper secret key; never logged or returned |
| `alpaca_base_url` | `"https://paper-api.alpaca.markets"` | `str` | YES (environment) | Alpaca base URL; switch to live URL only when stage=live* and operator-approved |
| `alpaca_timeout` | `15` | `int ≥ 1, ≤ 120` (seconds) | YES | Per-order broker call timeout; bounded latency budget per submission |
| `order_price_tolerance_mode` | `"flat"` | `Literal["flat","scaled"]` — config | NO (mode selector) | ADR-0013 champion–challenger selector; `flat` is the champion. Not a tunable — switching it changes which formula runs, not a value within one |
| `order_price_tolerance_bps` | `50` | `int ≥ 0, ≤ 500` (bps) | YES | Bounds entry and discretionary-exit orders near the PM's decided price so after-close decisions do not trade at an unevaluated open (ADR-0018) |
| `scaled_order_price_tolerance_atr_multiplier` | `0.50` | `float ≥ 0.0, ≤ 2.0` (ratio) | YES | Challenger band near half of decision-time daily ATR; observed overnight gaps cluster at 0.3–0.6× ATR |
| `scaled_order_price_tolerance_floor_bps` | `25` | `int ≥ 0, ≤ 500` (bps) | YES | Stops the scaled challenger becoming so narrow that quiet names cannot trade at all |
| `scaled_order_price_tolerance_ceiling_bps` | `250` | `int ≥ 0, ≤ 500` (bps) | YES | Keeps the challenger narrow enough that ADR-0018 still rejects a materially unevaluated open |
| `deliberation_grace_seconds` | `900` | `int ≥ 0, ≤ 3600` (seconds) | YES | How long a buy-carrying PMRun waits for its DeliberationRun before submitting under the declared posture; exits never wait (S147 / ADR-0017) |
| `deliberation_posture` | `"advisory"` | `Literal["advisory","binding"]` — config | NO (mode selector) | S185 operator policy selector; `advisory` records expected fail-open as warning, `binding` refuses buy exposure when no `DeliberationRun` arrives. Not a tunable — switching it changes which policy runs, not a value inside one |
| `broker_stop_fallback_stop_pct` | `0.05` | `float > 0.0, ≤ 1.0` (fraction) | YES | Downside floor for broker-adopted positions with no PM stop lineage (ADR-0015 §3); matches the monitor-reconciliation paper-stage floor |

---

## Divergence register

| ID | Law says | PRD / code says | Decision needed |
| --- | --- | --- | --- |
| — | — | — | No divergences at DRAFT v0 |

---

## Changelog

- v0 — drafted (ideal-design, S70). Not yet locked.
- **v1.1 — S152 law-amendment cycle (2026-08-01).** Declares capabilities that ADRs decided and
  later sprints built, where only the constitutional declaration was skipped. **No behaviour
  changed and no production source was edited**; every clause below is new (IDs are append-only,
  conventions §2) and starts ⬜ unproven — the green totals deliberately do **not** move.
  Closes DRIFT-024…029.
  - `EXEC-IDN-03` — owns `BrokerStopOrder`, `BrokerPositionSnapshot`, `BrokerOrderStatus`.
    *Why:* ADR-0015 §3 + DL-44 decided these; `EXEC-IDN-02` listed only the original four.
    (DRIFT-024, DRIFT-025)
  - `EXEC-TRG-07` — run-start `position_sync` writes one `BrokerPositionSnapshot` before
    downstream scoring. *Why:* DL-44 decided broker-truth-for-holdings; S120 built it and S147
    gated the analyst on it, undeclared. (DRIFT-025)
  - `EXEC-OUT-07` — `dropped` as an outcome distinct from `rejected`/`skipped`, with the
    append-safe evidence shape. *Why:* ADR-0018 decided the drop; S151/DL-79 settled the shape
    after the collision stalled the fleet. (DRIFT-026)
  - `EXEC-OUT-08` — durable applied + counterfactual tolerance evidence on submitted orders.
    *Why:* ADR-0013 decided champion–challenger; S149 shipped it off by default. (DRIFT-027)
  - `EXEC-STA-05` — broker-status refresh terminates on a terminal `broker_status`; `partial`
    still refreshes. *Why:* implied by ADR-0014's append-only model and left open by DL-44;
    S154 closed it. (DRIFT-029)
  - `EXEC-STA-06` — an unresolvable realized-PnL conclusion is recorded once via
    `Fill.pnl_unresolved_at`. *Why:* decided in the S154 spec and DL-81. (DRIFT-029)
  - `EXEC-OBS-03` — protective-stop lifecycle reconstructable; `UnprotectedPosition` surfaced
    and retried. *Why:* ADR-0015 §3; the silence is what S146 fixed. (DRIFT-024)
  - `EXEC-DEP-04` — graph append-write for the three new labels; broker cancel + stop placement.
    *Why:* the dependency surface the above capabilities actually use. (DRIFT-024/025/026)
  - `CAP` block — graph `labels` and broker `operations` widened to match the clauses above.
  - `PARAM` — declares `order_price_tolerance_mode` (a **mode selector, not a tunable**),
    `order_price_tolerance_bps`, the three `scaled_order_price_tolerance_*` bounds, and
    `broker_stop_fallback_stop_pct`. Values and bounds copied from the `tunable()` declarations
    in `agents/execution/settings.py`, not restated from memory.
- **v1.2 — S185 deliberation posture declaration (2026-08-22).** Declares the operator-selected
  deliberation posture that S185 made explicit after DL-104/DL-116 left it as timing arithmetic.
  Adds `EXEC-OUT-09` (posture/status/block evidence on `ExecutionRun`), `EXEC-NEV-06` (binding
  no-verdict buy exposure is blocked while exits and arrived vetoes keep their boundaries), and
  `EXEC-OBS-04` (fault/acceptance severity follows posture). Adds the `deliberation_posture`
  `PARAM` row as **NO (mode selector)**, not a tunable. Closes DRIFT-048; DRIFT-049 remains open
  for the older missing `deliberation_grace_seconds` PARAM row.
- **v1.3 — S187 parameter declaration reconciliation (2026-08-30).** Adds the missing
  `deliberation_grace_seconds` PARAM row from the existing `tunable()` declaration, correcting
  DRIFT-049. No clauses were added or proven; rollup counters deliberately do not move.
- **v1.4 — S190 broker fact liveness (2026-08-31).** Adds `EXEC-OBS-05`: execution broker-fact
  liveness is derived in one contract module, fired `BrokerStopOrder` facts stop reading live,
  resting-stop Fills stop counting as open orders, and the stale-order sweep compares live broker
  stops to live graph stops. Also proves the previously gray `EXEC-STA-05` row and adds missing
  `EXEC-OBS-03` liveness-limb tests, correcting DRIFT-055.
