# `Reporter` — Laws

**Prefix:** `RPT` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

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

- **RPT-IN-01** — `report` accepts `ReportRequest { run_id: str }`. Identifies the pipeline run
  whose PMRun, Fills, CloseDecisions, and Recommendations to aggregate.
- **RPT-IN-02** — `narrative` accepts `NarrativeRequest { position_id: str }`. Keys the position
  whose scan-to-exit chain is stitched into a story.
- **RPT-IN-03** — Pub/sub path: consumes a `ReadyEvent` on `monitor.decisions.ready`; resolves
  via `claim_check_read` → `pm_run_id` extracted → calls `report(ReportRequest(run_id=pm_run_id))`.
- **RPT-IN-04** — Malformed input → degraded `RunSnapshot` or `TradeNarrative` returned; fault
  recorded; never raises to bus.

## Triggers (`TRG`)

- **RPT-TRG-01** — `report` triggered by RPC request (dispatcher or any authorized caller).
- **RPT-TRG-02** — `monitor.decisions.ready` event triggers `report` through the pub/sub path.
- **RPT-TRG-03** — `narrative` triggered by RPC request only; no event path.
- **RPT-TRG-04** — The reporter never self-triggers.

## Outputs (`OUT`)

- **RPT-OUT-01** — `report` returns `RunSnapshot { run_id, portfolio_metrics, signal_metrics,
  regime_attribution, headline, provenance }`.
- **RPT-OUT-02** — `portfolio_metrics` includes at minimum `profit_factor`, `expectancy_cents`,
  `closed_trades_with_pnl`; derived from `CloseDecision.pnl_cents` across all trigger types.
- **RPT-OUT-03** — `narrative` returns `TradeNarrative { position_id, story, provenance }`.
- **RPT-OUT-04** — A `Snapshot` graph node is written per `report` call; a `TradeNarrative` node
  per `narrative` call.
- **RPT-OUT-05** — A `report.snapshot.ready` claim-check event is published after the pub/sub
  `report` completes, so the dispatcher can observe pipeline completion.
- **RPT-OUT-06** — Degraded path: if graph traversal fails, a `degraded_snapshot` (minimal
  provenance, empty metrics) is returned and the fault is recorded. Never a crash.

## Prohibitions (`NEV`)

- **RPT-NEV-01** — Never makes or alters a trading decision. The reporter reads-only and
  projects; it has no write path to OrderIntent, Recommendation, or CloseDecision.
- **RPT-NEV-02** — Never mutates another agent's graph nodes. Every node it reads was written by
  scanner, analyst, PM, execution, or monitor; the reporter may only write its own labels.
- **RPT-NEV-03** — Never silences a partial graph. If metrics are undefined (no closed trades),
  they are reported as 0 / 0.0; the explanation states why. Never KeyError.

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

## Ordering & concurrency (`ORD`)

- **RPT-ORD-01** — No cross-run dependency. Each `report(run_id)` is independent.
- **RPT-ORD-02** — Concurrent calls for the same `run_id` produce duplicate Snapshot nodes; no
  data corruption because all writes are append-only.

## Failure, recovery & rollback (`FAIL`)

- **RPT-FAIL-01** — Graph traversal failure in `report`: `fault_boundary` captures the exception;
  `degraded_snapshot` is returned; fault is emitted to sink; event is still published.
- **RPT-FAIL-02** — Graph traversal failure in `narrative`: `fault_boundary` captures; a
  `degraded_narrative` is returned.
- **RPT-FAIL-03** — All faults are non-terminal: the pipeline continues whether or not the
  reporter succeeds.

## Type alignment (`TYP`)

- **RPT-TYP-01** — `RunSnapshot` and `TradeNarrative` match `contracts/reporter.py` exactly.
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
- **RPT-DEP-02** — `DEP-NEO4J` — graph traversal across all agent labels (read-only for all
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
      "Recommendation", "ScanRun", "Candidate", "AnalystRun", "MonitorRun"
    ]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `max_narrative_length_chars` | `2000` | `int ≥ 200 ≤ 10000` | YES | Cap narrative length for dashboard rendering; future-proofs against deeper graph |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
