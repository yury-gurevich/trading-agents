# `Reporter` — Laws

**Prefix:** `RPT` · **status:** LOCKED v1.5 · **Owner:** Yury Gurevich

> Stitch each completed run and each trade into durable, human-readable metrics and
> narrative — the truth surface the dashboard and operator read.

Each clause has a stable ID (`RPT-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **RPT-IDN-01** — The reporter's single job is traversal: walk the provenance graph built by
  upstream agents and project it into a `RunSnapshot` (metrics + attribution) or a
  `TradeNarrative` (per-trade story). It synthesises; it never decides.
- **RPT-IDN-02** — The reporter exclusively writes these graph labels (single-writer rule):
  `Snapshot`, `TradeNarrative`, `ReportSnapshotResult`.

## Inputs (`IN`)

- **RPT-IN-01** — `report` accepts `ReportRequest { run_id: str }`. Identifies the `PMRun` whose
  snapshot is built. From that run's own lineage it reads its Recommendations, Rejections, market
  lineage and the `CloseDecision`s behind `close_trigger_target` / `close_trigger_time`. By time, not
  by lineage, it reads the filled `Fill`s and the other `PMRun`s' `created_at` that bound the run's
  window (`RPT-OUT-02`, `RPT-IDM-04`), and the fresh `BrokerPositionSnapshot`s and the run's own
  `MarketData` (`RPT-OUT-07`). *(S253; was: "the pipeline run whose PMRun, Fills, CloseDecisions,
  and Recommendations to aggregate".)*
- **RPT-IN-02** — `narrative` accepts `NarrativeRequest { position_id: str }`. Keys the position
  whose scan-to-exit chain is stitched into a story.
- **RPT-IN-03** — Pub/sub path: consumes a `ReadyEvent` on `monitor.decisions.ready`; resolves
  via `claim_check_read` → `pm_run_id` extracted → calls `report(ReportRequest(run_id=pm_run_id))`.
- **RPT-IN-04** — Malformed input → degraded `RunSnapshot` or `TradeNarrative` returned; fault
  recorded; never raises to bus.

## Triggers (`TRG`)

- **RPT-TRG-01** — `report` triggered by RPC request (dispatcher or any authorized caller).
- **RPT-TRG-02** — Event-driven, never a timer. **Pub/sub:** a `monitor.decisions.ready` event
  triggers `report` through the pub/sub path. **Graph-pull** (DL-08/08b, the path the fleet runs): a
  `MonitorRun` with no `REPORTED_BY` edge that is not a position-sync marker is a request. The poll
  builds the snapshot of its source PM run from the graph alone, writes the `Snapshot`, and links
  `MonitorRun -REPORTED_BY-> Snapshot`, so each `MonitorRun` is reported once. The poll finds its
  pending work **by key and edge alone** and **fetches props only for `MonitorRun`s without that
  edge** (DL-246). A position-sync marker never gains the edge, so each poll fetches every sync
  marker and drops it. *(DRIFT-086; was: the pub/sub path only.)*
- **RPT-TRG-03** — `narrative` triggered by RPC request only; no event path.
- **RPT-TRG-04** — The reporter never self-triggers.

## Outputs (`OUT`)

- **RPT-OUT-01** — `report` returns `RunSnapshot { run_id, portfolio_metrics, signal_metrics,
  regime_attribution, performance_metrics, headline, provenance }`.
- **RPT-OUT-02** — `portfolio_metrics` reports the book from the broker's fills, never from the
  run's own orders. A `Fill` counts once its `broker_status` is in `FILLED_BROKER_STATUSES`, at its
  `broker_status_refreshed_at` (never `submitted_at`, never `status`); one whose time cannot be read
  is in no window. The run's **window** runs after the latest other `PMRun.created_at` strictly
  before the reported one's (open when there is none), up to and including the reported
  `PMRun.created_at`. `positions_opened` is the buy fills in the window, `positions_closed` the sell
  fills, `close_trigger_stop` those sells that are resting broker stops. `positions_held` is the
  number of holdings in the last snapshot `RPT-OUT-07` chooses (the latest fresh one at or before
  `PMRun.created_at`). `closed_trades_with_pnl`, `profit_factor` and `expectancy_cents` are over every
  filled sell carrying an integer `realized_pnl_cents` (a dropped, unfilled or invalidated one
  carries none), refreshed from 00:00 UTC of `performance_inception` up to and including
  `PMRun.created_at`. `approved_count`, `rejected_count` and `approval_rate` come from the `PMRun`;
  `close_trigger_target` and `close_trigger_time` from its lineage's `CloseDecision`s.
  *(DRIFT-099, S253 / DL-262, DL-263; was: "includes at minimum `profit_factor`,
  `expectancy_cents`, `closed_trades_with_pnl`; derived from `CloseDecision.pnl_cents` across all
  trigger types".)*
- **RPT-OUT-03** — `narrative` returns `TradeNarrative { position_id, story, provenance }`.
- **RPT-OUT-04** — A `Snapshot` graph node is written per `report` call; a `TradeNarrative` node
  per `narrative` call.
- **RPT-OUT-05** — A `report.snapshot.ready` claim-check event is published after the pub/sub
  `report` completes, so the dispatcher can observe pipeline completion.
- **RPT-OUT-06** — Degraded path: if graph traversal fails, a `degraded_snapshot` (minimal
  provenance, empty metrics) is returned and the fault is recorded. Never a crash.
- **RPT-OUT-07** — `report` returns `performance_metrics`: return on the book against the
  benchmark, from `performance_inception` to the run's as-of date. It is computed only from facts
  other agents wrote: fresh `BrokerPositionSnapshot` equity and holdings, and the benchmark bars on
  the run's **own** `MarketData`, reached by its lineage (`PMRun.source_analyst_run_id` →
  `AnalystRun` ← `ScanRun` → `MarketData`, one node a hop, never a listing). A broken lineage, a
  `MarketData` dated after the as-of, or one with no benchmark bars is the no-benchmark path
  (`missing benchmark`). Another run's series is never read. Each UTC date contributes one point: the
  **latest** fresh snapshot of that date, the one nearest the close its benchmark bar measures.
  *(DRIFT-087, DL-246.)*

## Prohibitions (`NEV`)

- **RPT-NEV-01** — Never makes or alters a trading decision. The reporter reads-only and
  projects; it has no write path to OrderIntent, Recommendation, or CloseDecision.
- **RPT-NEV-02** — Never mutates another agent's graph nodes. Every node it reads was written by
  scanner, analyst, PM, execution, or monitor; the reporter may only write its own labels.
- **RPT-NEV-03** — Never silences a partial graph, and never a `KeyError`. A metric the graph
  cannot define is **absent**, never a confident zero. With no exit carrying realised P&L in the span,
  `profit_factor` and `expectancy_cents` are absent and `closed_trades_with_pnl` reads 0.0 (no wins
  over some losses is a real profit factor of 0.0, not an undefined one). When the reported `PMRun`
  has no readable `created_at`, the book counts and the three outcome keys are absent and the
  headline prints `?` for each count; with no as-of position snapshot, `positions_held` is absent; a
  failed book read leaves the book keys absent and records a fault. A degraded snapshot
  (`RPT-OUT-06`) reports its counts as 0.0 and its headline states why. *(DRIFT-101, S253; was: "If
  metrics are undefined (no closed trades), they are reported as 0 / 0.0; the explanation states
  why.")*

## State & effects (`STA`)

- **RPT-STA-01** — Stateless between calls. All data lives in the graph.
- **RPT-STA-02** — Graph writes are append-only. A `Snapshot` node, once written, is never
  overwritten; each `report` call produces a new node.

## Determinism & idempotency (`IDM`)

- **RPT-IDM-01** — Given the same graph state, `report(run_id)` produces the same `RunSnapshot`.
  Re-running is safe in the sense that new Snapshot nodes accumulate but no prior nodes are
  mutated.
- **RPT-IDM-02** — `run_id` is threaded from the `ReportRequest` into the Snapshot provenance and
  the `report.snapshot.ready` event.
- **RPT-IDM-03** — The performance as-of date is the UTC date of `PMRun.created_at`. No fact dated
  after it is read, and no `BrokerPositionSnapshot` created after `PMRun.created_at` is read, so
  re-reporting an old run reproduces its figures even after the graph grows, including on its own date.
- **RPT-IDM-04** — The book metrics read no `Fill` whose `broker_status_refreshed_at` is after
  `PMRun.created_at`, and the window's start is another `PMRun`'s `created_at`, never the reporter's
  own earlier output (`RPT-ORD-01`). So each filled fill belongs to exactly one run's window, and
  re-reporting an old run reproduces its book metrics even after the graph grows. *(S253.)*

## Ordering & concurrency (`ORD`)

- **RPT-ORD-01** — No cross-run ordering dependency. Reading upstream facts recorded by earlier
  runs is allowed; depending on the reporter's own earlier output is not.
- **RPT-ORD-02** — Concurrent calls for the same `run_id` produce duplicate Snapshot nodes; no
  data corruption because all writes are append-only.

## Failure, recovery & rollback (`FAIL`)

- **RPT-FAIL-01** — Graph traversal failure in `report`: `fault_boundary` captures the exception;
  `degraded_snapshot` is returned; fault is emitted to sink; event is still published.
- **RPT-FAIL-02** — Graph traversal failure in `narrative`: `fault_boundary` captures; a
  `degraded_narrative` is returned.
- **RPT-FAIL-03** — All faults are non-terminal: the pipeline continues whether or not the
  reporter succeeds.
- **RPT-FAIL-04** — Performance input or calculation failure is contained. The rest of the
  snapshot is still produced, `performance_metrics` reports zero sessions, and a fault is recorded.

## Type alignment (`TYP`)

- **RPT-TYP-01** — The reporter payload types carry, at minimum, the fields its own clauses
  require; the clause, not `contracts/reporter.py`, is the authority on what must be present.
  `RunSnapshot` carries `run_id`, `portfolio_metrics`, `signal_metrics`, `regime_attribution`,
  `performance_metrics`, `headline`, and `provenance`
  (`RPT-OUT-01`/`RPT-OUT-02`/`RPT-OUT-06`/`RPT-OUT-07`). `TradeNarrative` carries `position_id`,
  `story`, and `provenance` (`RPT-OUT-03`).
- **RPT-TYP-02** — `portfolio_metrics` is a `dict[str, float]`; `expectancy_cents` is float
  (integer cents represented as float); no type coercion silently drops precision.
- **RPT-TYP-03** — `ReportSnapshotResult` graph node payload matches `RunSnapshot` schema so
  `claim_check_read` reconstructs a valid object.

## Security & privilege (`SEC`)

- **RPT-SEC-01** — Holds no credentials; no elevated privilege. Read-only over the graph except
  for its own labels.
- **RPT-SEC-02** — Never logs trade details, PnL, or position data to external systems.

## Dependencies (`DEP`)

- **RPT-DEP-01** — `DEP-BUS` — consumes `monitor.decisions.ready`, publishes
  `report.snapshot.ready`.
- **RPT-DEP-02** — `DEP-POSTGRES` — graph traversal across all agent labels (read-only for all
  except Snapshot/TradeNarrative/ReportSnapshotResult).

## Observability & audit (`OBS`)

- **RPT-OBS-01** — A `Snapshot` node is written per `report` call; every metric is reconstructable
  from the graph without the RPC response.
- **RPT-OBS-02** — Degraded paths emit a fault to the sink; degradation is never silent.

## Performance envelope (`PERF`)

- **RPT-PERF-01** — `max_narrative_length_chars=2000` caps narrative output size and prevents
  runaway graph traversals.
- **RPT-PERF-02** — The reporter holds no open connections; graph traversal latency is the
  dominant cost.

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["subscribe", "publish"],
    "topics_subscribed": ["monitor.decisions.ready"],
    "topics_published": ["report.snapshot.ready"],
    "delivery": "at_least_once"
  },
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["Snapshot", "TradeNarrative", "ReportSnapshotResult"],
    "labels_read": [
      "PMRun", "OrderIntent", "Fill", "CloseDecision", "Position",
      "Recommendation", "ScanRun", "Candidate", "AnalystRun", "MonitorRun",
      "BrokerPositionSnapshot", "MarketData"
    ]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `max_narrative_length_chars` | `2000` | `int ≥ 200 ≤ 10000` | YES | Cap narrative length for dashboard rendering; future-proofs against deeper graph |
| `performance_inception` | `2026-08-10` | `date` | YES | Start benchmark scoring after DL-93 flattened and resized the prior leveraged margin book (`REPORTER_PERFORMANCE_INCEPTION`) |
| `performance_rolling_sessions` | `20` | `int ≥ 5 ≤ 120` | YES | Trading-month rolling window beside since-inception performance (`REPORTER_PERFORMANCE_ROLLING_SESSIONS`) |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
- v1.1 — S205 rewrites `RPT-TYP-01` from a file-as-oracle contract assertion into explicit
  required fields for `RunSnapshot` and `TradeNarrative`. `RPT-TYP-03` remains a separate
  claim-check serialization-shape clause. No contract shape changes.
- v1.2 — S226 adds benchmark-relative performance metrics bounded to the PM run as-of date,
  records the needed CAP/PARAM rows, and makes performance failures contained within `report`.
- v1.3 — work-queue 88 (DL-224): `RPT-OUT-07` names the day's point as its latest fresh snapshot, not
  the earliest, which on a two-run day was an intraday sync set against a closing bar; `RPT-IDM-03`
  bounds snapshots by `PMRun.created_at` itself, so the latest-per-date rule stays reproducible.
- v1.4 — S251 / DL-259, DL-260 (2026-10-01). `RPT-OUT-07` says which `MarketData` the benchmark comes
  from: the run's own, by lineage. A missing one is `missing benchmark`, never another run's series
  (DRIFT-087). `RPT-TRG-02` names the graph-pull trigger and its key-and-edge bound, including the
  sync markers it fetches and drops (DRIFT-086). Both stay 🟩, on S242's lineage tests and the
  reporter's poll tests. No behaviour change; 25 / 42 unchanged.
- v1.5 — S253 / DL-262, DL-263 (2026-10-02). `RPT-OUT-02` rewritten: the book counts are the
  broker's filled `Fill`s in the run's window (after the previous `PMRun.created_at`, up to and
  including its own), `positions_held` is the as-of position snapshot's holdings, and the outcomes are
  cumulative over filled exits since the inception, no longer `CloseDecision.pnl_cents`
  (DRIFT-099); `execution_count`, `approval_execution_gap` and `dropped_decision_count` are removed.
  `RPT-IN-01` says what a report reads. `RPT-NEV-03` amended to what the code does: an undefined
  metric is absent, not 0 / 0.0, and the degraded snapshot's zero counts are named (DRIFT-101). New
  `RPT-IDM-04`: no fill refreshed after the run is read and the window starts at another `PMRun`, so
  a re-report reproduces the book. Proven by `test_book_window.py` and `test_book_window_edges.py`.
  25 / 42 → 26 / 43.
