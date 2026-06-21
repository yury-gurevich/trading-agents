# Sprint 81 — PM graph-pull: analyst→PM handoff

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-81-pm-graph-pull`
**Status:** shipped (0.20.00)

---

## Goal

Extend the graph-pull slice by one more handoff: the **portfolio manager** reads its work
from the graph instead of live bus RPC, so it sizes and risk-checks orders with neither the
analyst nor the provider container alive. Third agent on the pull model (provider→scanner→
analyst→**PM**); proves the S79/S80 template holds again.

Scoped to **PM only** — execution, monitor, reporter carried to S82 (same discipline as
S79 deferring analyst→reporter, S80 deferring PM→reporter).

---

## What shipped

- **Analyst** now persists the full `RecommendationSet` on its `AnalystRun` node
  (`agents/analyst/poll.py`) — S80 left it `{}`, carrying only counts, so the PM had nothing
  to pull. Mirrors how the scanner persists its `CandidateSet` on the `ScanRun`.
- **PM** `agents/portfolio_manager/poll.py`:
  - `find_pending(graph)` — `AnalystRun` nodes with no `EVALUATED_BY` descendant.
  - `evaluate_analyst_node(node, …)` — pulls the `RecommendationSet` from node props, the
    `MarketData` via the AnalystRun's `ANALYZED_BY` ancestor (the ScanRun) and its
    `DERIVED_FROM` descendant, and the same-day `RegimeContext` by date; sizes + risk-checks;
    writes the `PMRun`; links an `EVALUATED_BY` edge.
- **Shared sizing/risk core** extracted to `agents/portfolio_manager/run.py`
  (`run_evaluation`) so the bus path (`_evaluate_orders`) and the graph path use one
  implementation — including the provider-degraded checks, `provider_unavailable`/
  `no_recommendations`/`portfolio_evaluation_failed` rejection reasons. This shrank
  `agent.py` (the `_provider_rejection`/`_record_fault`/`_empty_result` helpers moved into
  `run.py`).
- **PM entrypoint** drops `idle_loop()` for the `work_loop()` graph poll.
- `test_entrypoints.py` drops PM from the idle-loop smoke list (now graph-pull, tested under
  `agents/portfolio_manager/tests/`).

---

## Lineage traversal

The PM starts from the pending `AnalystRun` and walks back to the market facts the analyst
already consumed, so PM and analyst score the same correlated snapshot:

```
AnalystRun ──ancestors(ANALYZED_BY)──▶ ScanRun
ScanRun    ──descendants(DERIVED_FROM)──▶ MarketData
MarketData ──key regime-context:{window_end}──▶ RegimeContext
```

`(scan)-[:ANALYZED_BY]->(analyst)` is written by the analyst, `(scan)-[:DERIVED_FROM]->(market)`
by the scanner, so the analyst's MarketData is its `ANALYZED_BY` ancestor's `DERIVED_FROM`
descendant — the same direction discipline that bit S80.

---

## Known limitations (carried forward)

- **Portfolio state is a fresh default each poll.** Graph-pull PM builds
  `default_portfolio(starting_cash)` per `AnalystRun` rather than reconstructing live
  positions/cash from the graph. Fine for the slice (one ingest cycle/day, paper portfolio),
  but real position-aware sizing needs the execution/monitor state — revisit once those run
  graph-pull (S82+).
- Same `MarketData` field gaps as S80 (no `benchmark`/vendor `sentiment` from provider
  ingest) — affects analyst scoring, not PM sizing.

---

## Exit criteria

- [x] Starting only the PM (with provider+scanner+analyst data in the graph) produces `PMRun`
  + `OrderIntent` nodes within one poll interval — proven by `test_pm_poll.py`.
- [x] `make ci` green; 100 % coverage; every new module ≤ 200 lines.
- [x] `idle_loop()` only called by entrypoints with no work loop yet (execution/monitor/
  reporter/forecaster/operator/supervisor/curator/researcher).

---

## Version bump

New capability (PM does real graph-pull work). **0.20.00** (feat → MINOR, HARD RULE).

---

## Deferred (S82)

- Execution, monitor, reporter graph-pull data paths. Execution needs the full
  `OrderIntentSet` (or to reconstruct from `OrderIntent` nodes) and an `ExecutionRun`
  processed-edge anchor; monitor needs close prices read from the graph `MarketData` bars
  instead of its `latest_close_cents` bus RPC; reporter is already graph-centric
  (`build_snapshot`) and just needs a work-loop trigger keyed off the `MonitorRun`.
- Forecaster / control-plane agents (supervisor / curator / researcher / operator) work loops.
- P14 pub/sub doorbell overlay; dispatcher cron; Alpaca live keys.
- **Permanent graph store** before the Aura trial lapses (~2026-06-29) — these agents need a
  reachable store to run in the fleet.
