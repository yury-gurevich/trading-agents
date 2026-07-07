# `Execution` — Laws

**Prefix:** `EXEC` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

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

---

## Observability & audit (`OBS`)

- **EXEC-OBS-01** — Every fill, every reconciliation outcome, and every stage transition is
  fully reconstructable from the graph. `ExecutionResultEvent` nodes cross-reference the
  originating `pm_run_id` and `intent_id` for end-to-end provenance.
- **EXEC-OBS-02** — Broker rejections, timeouts, and stage-gate rejections are all routed to
  the central fault channel. No broker interaction is silent: all outcomes (filled, partial,
  rejected) are recorded.

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
    "labels": ["Fill", "Reconciliation", "StageTransition", "ExecutionResultEvent"],
    "access": "write_own_labels_only"
  },
  "broker": {
    "operations": ["submit_order", "list_fills"],
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

---

## Divergence register

| ID | Law says | PRD / code says | Decision needed |
| --- | --- | --- | --- |
| — | — | — | No divergences at DRAFT v0 |

---

## Changelog

- v0 — drafted (ideal-design, S70). Not yet locked.
