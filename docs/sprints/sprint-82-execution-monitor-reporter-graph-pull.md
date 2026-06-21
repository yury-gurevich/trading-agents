# Sprint 82 — Execution + monitor + reporter graph-pull: close the pipeline

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-82-execution-monitor-reporter-graph-pull`
**Status:** shipped (0.21.00)

---

## Goal

Finish the DL-08 pull model end-to-end. After S79–S81 (provider→scanner→analyst→PM),
the last three agents — **execution**, **monitor**, **reporter** — read their work from the
graph instead of live bus RPC, so the whole pipeline runs container-by-container with no
agent depending on another being alive. After this sprint, dropping a single agent into the
fleet with upstream data in the graph produces its output within one poll interval.

Scoped to **all three** (operator decision, 2026-06-22): reporter is trivial once it has a
trigger, and the Aura trial (~2026-06-29) makes finishing the pipeline now worthwhile.

---

## The edge chain this sprint completes

```text
PMRun ─[EXECUTED_BY]→ ExecutionRun ─[MONITORED_BY]→ MonitorRun ─[REPORTED_BY]→ ReporterRun
```

Each `find_pending` looks for the upstream run node lacking its downstream processed edge —
the same `SCANNED_BY` / `ANALYZED_BY` / `EVALUATED_BY` pattern from S79–S81.

---

## Work — Execution

1. **PM persists the full `OrderIntentSet` on `PMRun`** (S81 follow-on). Today
   `write_order_decision` writes counts only; execution has no orders to pull. Mirror the
   established pattern (scanner→`CandidateSet`, analyst→`RecommendationSet`,
   PM→`OrderIntentSet`): in `agents/portfolio_manager/poll.py`'s `evaluate_analyst_node`,
   merge the `PMRun` with `{"order_intent_set": result.model_dump(mode="json")}` (the node is
   already re-merged there for the `EVALUATED_BY` edge — add the payload, same as the analyst
   fix in S81).
2. **Add an `ExecutionRun` anchor.** Execution currently writes only `Fill` nodes (no run
   node), so monitor would have nothing to poll. `agents/execution/store.py`: write an
   `ExecutionRun` node keyed by the execution run id; link `PMRun ─[EXECUTED_BY]→ ExecutionRun`.
   Keep the existing `Fill ─[EXECUTES]→ OrderIntent` lineage.
3. **Extract the submit core** to `agents/execution/run.py` (mirror analyst `run.py` / PM
   `run.py`) shared by the bus path (`_on_orders_ready`) and the new graph path. Execution
   has **no provider RPC** — only the injected broker — so the extraction is clean.
4. **`agents/execution/poll.py`:**
   - `find_pending(graph)` — `PMRun` nodes with no `EXECUTED_BY` descendant.
   - `execute_pm_node(node, …)` — pull the `OrderIntentSet` from `PMRun` props, submit to the
     injected broker, `write_fills`, write the `ExecutionRun`, link `EXECUTED_BY`.
5. **Entrypoint** drops `idle_loop()` for `work_loop()`; remove execution from
   `tests/test_entrypoints.py`'s idle-loop list.

## Work — Monitor

1. **Replace the provider bus RPC with a graph read.** `_check_positions` calls
   `latest_close_cents(bus, …)` (live provider RPC — the second cross-container bus call, same
   class of problem PM/analyst had). Read the latest close per ticker from the `MarketData`
   bars already in the graph instead. Reuse monitor's own `_latest_cents` logic
   (`agents/monitor/provider_client.py`) fed by the graph `MarketData` node — **do not** import
   another agent (islands rule). Fills are already read from the graph (`fills_for_run`), so
   that half needs no change.
2. **`agents/monitor/poll.py`:**
   - `find_pending(graph)` — `ExecutionRun` nodes with no `MONITORED_BY` descendant (fills are
     guaranteed to exist before monitoring).
   - `monitor_pm_node(node, …)` — from the `ExecutionRun`, walk the `EXECUTED_BY` ancestor to
     the `PMRun` for `pm_run_id`; open positions from fills; read prices from the graph
     `MarketData` (via the PMRun lineage `EVALUATED_BY→AnalystRun→ANALYZED_BY→ScanRun→
     DERIVED_FROM→MarketData`, or the same `window_end` key); evaluate exits; write
     `MonitorRun`; link `MONITORED_BY`.
3. Extract the evaluate core to `agents/monitor/run.py` if the bus path and graph path
   share more than a couple of lines (follow the S80/S81 shape).
4. **Entrypoint** → `work_loop()`; remove monitor from the idle-loop list.

## Work — Reporter (trivial — already graph-centric)

1. `build_snapshot(graph, pm_run_id)` already reads everything from the graph; reporter has
   **no** provider RPC. It only needs a trigger.
2. **`agents/reporter/poll.py`:**
   - `find_pending(graph)` — `MonitorRun` nodes with no `REPORTED_BY` descendant.
   - `report_monitor_node(node, …)` — read `pm_run_id` from the `MonitorRun` (`source_run_id`),
     call `build_snapshot`, link `MonitorRun ─[REPORTED_BY]→ Snapshot`.
3. **Entrypoint** → `work_loop()`; remove reporter from the idle-loop list.

> **As-built note:** `build_snapshot` already writes a `Snapshot` node (`snapshot:{pm_run_id}`),
> so the `REPORTED_BY` edge targets that existing node rather than a new `ReporterRun` — one
> less node concept, and `build_snapshot` returns a degraded snapshot (still a `Snapshot`
> node) when the `PMRun` is missing, so the run is always marked reported and never re-polled.

---

## Edge-direction discipline (the bug that bit S80)

`add_edge(parent, child, type)`. Going *back up* the chain uses `ancestors`:

- `ExecutionRun → PMRun`: `ancestors(execution_run, edge_types={"EXECUTED_BY"})`
- `PMRun → AnalystRun`: `ancestors(pm_run, edge_types={"EVALUATED_BY"})`
- `AnalystRun → ScanRun`: `ancestors(analyst_run, edge_types={"ANALYZED_BY"})`
- `ScanRun → MarketData`: `descendants(scan_run, edge_types={"DERIVED_FROM"})`

Write the happy-path test first so the coverage floor catches a wrong-direction walk (S80
proved an empty-forever traversal otherwise passes silently).

---

## Known limitations (acceptable for the slice)

- **Monitor prices come from the same ingest snapshot** the position was sized against, not a
  fresh quote. Correct for one ingest cycle/day; multi-day holdings are re-checked on each new
  daily ingest as the pull model re-runs. Note it; revisit if intraday monitoring is needed.
- **Portfolio state** is still the S81 fresh-`default_portfolio` limitation until execution/
  monitor own live position state end-to-end — out of scope here.
- The pipeline still needs a **permanent reachable graph store** to run in the fleet
  (operator deferred this to a separate follow-on; Aura trial lapses ~2026-06-29). S82 tests
  run on the in-memory store; the fleet wiring is blocked until the store lands.

---

## Exit criteria

- [x] Starting only execution (with PM data in the graph) produces `Fill` + `ExecutionRun`
  nodes within one poll; only monitor produces `MonitorRun`; only reporter produces a
  `Snapshot` — each proven by its own `poll.py` test.
- [x] `make ci` green; 100 % coverage; every new module ≤ 200 lines.
- [x] `idle_loop()` only called by the remaining work-loop-less entrypoints (forecaster,
  operator, supervisor, curator, researcher).

---

## Version bump

New capability (three agents do real graph-pull work). **0.21.00** (feat → MINOR, HARD RULE).

---

## Deferred (S83+)

- Forecaster + control-plane agents (operator / supervisor / curator / researcher) work loops.
- Permanent graph store (self-host Neo4j on a small Azure VM) — the real fleet blocker.
- P14 pub/sub doorbell overlay; dispatcher cron; Alpaca live keys; live position-state
  reconstruction for portfolio sizing.
