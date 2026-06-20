# `Monitor` — Laws

**Prefix:** `MON` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Watch open positions and decide when to exit under policy (stop, target, time, regime)
> — then hand every close to execution and explain every hold.

Each clause has a stable ID (`MON-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **MON-IDN-01** — The monitor's single job is position surveillance: open fills into Position
  nodes, evaluate each against its configured exit policy (stop/target/time/regime), and produce
  an auditable CloseDecisionSet. It decides *when* to exit, never *what* to trade.
- **MON-IDN-02** — The monitor exclusively writes these graph labels (single-writer rule):
  `MonitorRun`, `PositionCheck`, `CloseDecision`, `Position`, `MonitorDecisionResult`.

## Inputs (`IN`)

- **MON-IN-01** — `check_positions` accepts `MonitorRequest { run_id: str }`. `run_id` keys the
  fills already in the graph for that pipeline run.
- **MON-IN-02** — `explain_hold` accepts `MonitorRequest { run_id: str }`. Returns an
  `Explanation` listing open held positions; no graph write.
- **MON-IN-03** — Pub/sub path: consumes a `ReadyEvent` on `execution.fills.ready`; payload is
  resolved via `claim_check_read` → fills the same `check_positions` path.
- **MON-IN-04** — Malformed input (validation failure) → `check_positions` returns a degraded
  `CloseDecisionSet`; `explain_hold` returns an `Explanation` with the error; never raises to bus.

## Triggers (`TRG`)

- **MON-TRG-01** — `check_positions` is triggered by RPC request from the dispatcher or any
  authorized caller.
- **MON-TRG-02** — `execution.fills.ready` event triggers `check_positions` through the pub/sub
  path. No manual step required.
- **MON-TRG-03** — `explain_hold` is triggered by RPC only; no event trigger.
- **MON-TRG-04** — The monitor never self-triggers.

## Outputs (`OUT`)

- **MON-OUT-01** — `check_positions` returns `CloseDecisionSet { run_id, decisions,
  positions_checked, explanation, provenance }` as the RPC response.
- **MON-OUT-02** — Each `CloseDecision` carries: `ticker`, `position_id`,
  `decision` (`"close"` | `"hold"`), `trigger`, `rationale` (Explanation), and `pnl_cents`
  (int | None).
- **MON-OUT-03** — `pnl_cents` is the realized gross PnL in integer cents on a close decision;
  `None` on a hold. Computed as `(exit − entry) × quantity`.
- **MON-OUT-04** — A `MonitorRun` graph node is written after every `check_positions` call,
  linking to the `CloseDecision` nodes.
- **MON-OUT-05** — A `CloseDecision` graph node is written for each decision (close or hold);
  holds are also persisted for auditability.
- **MON-OUT-06** — A `monitor.decisions.ready` claim-check event is published after
  `check_positions` so the reporter can consume the result.
- **MON-OUT-07** — If the price provider is unavailable (all prices None), `decisions` is empty
  and `positions_checked == 0`; a fault is recorded; the result is still returned (not raised).

## Prohibitions (`NEV`)

- **MON-NEV-01** — Never submits closes to the broker directly. Close decisions are handed to the
  execution agent over the bus.
- **MON-NEV-02** — Never opens new positions. The monitor only manages and exits existing ones.
- **MON-NEV-03** — Never calls a market-data API directly. Current prices are requested from the
  provider via the bus.
- **MON-NEV-04** — Never silently skips a position with a missing price. Records a degraded fault
  and excludes the position from the decision set with observable evidence.
- **MON-NEV-05** — Never mutates another agent's graph nodes; reads fills and recommendations
  written by execution/analyst but never alters them.

## State & effects (`STA`)

- **MON-STA-01** — Stateless between calls. All position state lives in the graph (Position nodes,
  fill ancestry). No in-memory position cache survives across invocations.
- **MON-STA-02** — All graph writes are append-only. A CloseDecision node, once written, is never
  overwritten; re-runs generate new nodes under a new `monitor_run_id`.

## Determinism & idempotency (`IDM`)

- **MON-IDM-01** — Given identical fills and identical prices, `check_positions` produces
  identical decisions. Exit rules (stop/target/time) are pure functions of position props + price.
- **MON-IDM-02** — Not globally idempotent: re-invoking with the same `run_id` re-opens positions
  from fills and re-evaluates; each invocation writes a new `MonitorRun` node. Callers must not
  assume idempotency.
- **MON-IDM-03** — `run_id` is threaded from the incoming `MonitorRequest` through
  `MonitorDecisionResult` into the `monitor.decisions.ready` event so downstream agents can
  correlate.

## Ordering & concurrency (`ORD`)

- **MON-ORD-01** — Positions are evaluated sequentially in the iteration order returned by the
  graph. No cross-position dependency in exit logic.
- **MON-ORD-02** — Concurrent `check_positions` calls for the same `run_id` may produce duplicate
  `MonitorRun` nodes. Callers are responsible for ensuring at-most-one invocation per run.

## Failure, recovery & rollback (`FAIL`)

- **MON-FAIL-01** — Provider price fetch failure (bus error or degraded response): the monitor
  receives `None` for the prices dict, returns an empty `CloseDecisionSet`, records a fault, and
  publishes a claim-check event with 0 decisions. The pipeline continues.
- **MON-FAIL-02** — Missing price for a single ticker: fault recorded via `fault_boundary`; the
  ticker is excluded from the decision set; other tickers continue.
- **MON-FAIL-03** — Position opening failure (fill without valid lineage): monitored via
  `draft.degraded` flag; a degraded fault is recorded; the position is still written with fallback
  stop/target values.
- **MON-FAIL-04** — Graph write failure: `MonitorRun` or `CloseDecision` write error propagates as
  a fault. The RPC response is still returned with whatever was computed before the failure.

## Type alignment (`TYP`)

- **MON-TYP-01** — `CloseDecisionSet` and `CloseDecision` match `contracts/monitor.py` exactly.
  `pnl_cents` is `int | None` — never a float.
- **MON-TYP-02** — `MonitorDecisionResult` graph node payload matches the `CloseDecisionSet`
  schema so `claim_check_read` returns a reconstructable object.
- **MON-TYP-03** — `MonitorRequest.run_id` is a non-empty string; empty strings produce a
  degraded result, not a crash.

## Security & privilege (`SEC`)

- **MON-SEC-01** — Holds no credentials and requires no elevated privilege. Lowest-privilege agent
  in the stack.
- **MON-SEC-02** — Never logs position data, prices, PnL, or ticker-level details to external
  systems. Fault records contain only module/error type, not trade data.
- **MON-SEC-03** — Revocable without breaking the system: if the monitor is down, fills accumulate
  in the graph and execution is quiescent; re-starting the monitor replays pending fills.

## Dependencies (`DEP`)

- **MON-DEP-01** — `DEP-BUS` — in-process or distributed bus for provider price requests and
  execution close dispatch.
- **MON-DEP-02** — `DEP-NEO4J` — graph store for Position, Fill ancestry, CloseDecision,
  MonitorRun nodes.

## Observability & audit (`OBS`)

- **MON-OBS-01** — A `MonitorRun` node is written per `check_positions` call; every decision is
  reconstructable from the graph without the RPC response.
- **MON-OBS-02** — Degraded paths (missing price, bus error, position fault) emit a fault to the
  sink; never buried silently.
- **MON-OBS-03** — `pnl_cents` on `CloseDecision` nodes is the realized-PnL audit trail; the
  reporter reads it directly.

## Performance envelope (`PERF`)

- **MON-PERF-01** — `price_lookback_days=2` keeps the provider request window narrow.
- **MON-PERF-02** — The monitor holds no open connections between calls; provider request latency
  is bounded by the bus timeout (no infinite wait).

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["request", "subscribe", "publish"],
    "topics_subscribed": ["execution.fills.ready"],
    "topics_published": ["monitor.decisions.ready"],
    "delivery": "at_least_once"
  },
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": [
      "MonitorRun", "PositionCheck", "CloseDecision",
      "Position", "MonitorDecisionResult"
    ],
    "labels_read": ["Fill", "OrderIntent", "Recommendation"]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `default_horizon_days` | `14` | `int ≥ 0 ≤ 365` | YES | Paper-stage holding window when no analyst horizon exists in graph |
| `price_lookback_days` | `2` | `int ≥ 0 ≤ 14` | YES | Small rolling window to get latest close across non-trading days |
| `default_stop_pct` | `0.05` | `float [0, 1]` | YES | Fallback stop policy if OrderIntent lineage is missing stop_pct |
| `default_target_pct` | `0.10` | `float [0, 1]` | YES | Fallback target policy if OrderIntent lineage is missing target_pct |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
