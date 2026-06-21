# Sprint 80 — Analyst graph-pull: scanner→analyst handoff

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-80-analyst-graph-pull`
**Status:** shipped (0.19.00)

---

## Goal

Extend the S79 graph-pull slice by one handoff: the **analyst** reads its work from the
graph instead of live bus RPC, so it runs standalone with neither the scanner nor the
provider container alive. Proves the DL-08 pull model holds for a *second* agent and that
the S79 template generalises.

---

## What shipped

- **Provider** persists the full `RegimeContext` payload (`ingest._write_regime_context`,
  keyed by window-end date) alongside the `MarketData` node from S79 — the analyst needs
  regime, and S79 only wrote a `Regime` summary.
- **Scanner** persists the full `CandidateSet` on its `ScanRun` node (`poll.scan_market_node`)
  so the analyst can pull it from the graph instead of receiving it as a bus payload.
- **Analyst** `agents/analyst/poll.py`:
  - `find_pending(graph)` — `ScanRun` nodes with no `ANALYZED_BY` descendant.
  - `analyze_scan_node(node, …)` — pulls the `CandidateSet` from node props, the `MarketData`
    via the ScanRun's `DERIVED_FROM` descendant, and the same-day `RegimeContext` by date;
    scores; writes the `AnalystRun`; links an `ANALYZED_BY` edge.
- **Shared scoring core** extracted to `agents/analyst/run.py` (`run_analysis`) so the bus
  path (`_analyze`) and the graph path use one implementation — and the existing analyst
  agent tests cover its branches (degraded data, scoring failure). This also shrank agent.py.
- **Analyst entrypoint** drops `idle_loop()` for the `work_loop()` graph poll.
- `REGIME_CONTEXT_LABEL` added to `contracts/provider.py` (with `MARKET_DATA_LABEL`) so the
  agents stay islands.

## Bug caught in-sprint

The lineage edge `write_scan` writes is `(scan)-[:DERIVED_FROM]->(market)`, so the MarketData
node is the ScanRun's **descendant**, not ancestor. The first cut of `_market_node` walked
`ancestors` and would have returned an empty result on every run forever — the analyst would
silently never score anything. The 100 %-coverage floor surfaced it (the happy path was
unreachable); the happy-path test now asserts a `Recommendation` node is produced.

---

## Known limitations (carried to S81+)

- The persisted `MarketData` lacks `benchmark` and vendor `sentiment` (the provider ingest
  doesn't request those fields), so the analyst scores on technical indicators only — the
  relative-strength and provider-sentiment *advisory* challengers are absent. Acceptable;
  the core technical score is unaffected.
- Correlation is "the ScanRun's DERIVED_FROM market + same-day regime". Fine for one ingest
  cycle per day; revisit if multiple same-day cycles land.

---

## Exit criteria

- [x] Starting only the analyst (with scanner+provider data in the graph) produces `AnalystRun`
  nodes within one poll interval — proven by `test_analyst_poll.py`.
- [x] `make ci` green; 100 % coverage; every new module ≤ 200 lines.
- [x] `idle_loop()` only called by entrypoints with no work loop yet (PM/execution/monitor/
  reporter/forecaster/operator/supervisor/curator/researcher).

---

## Version bump

New capability (analyst does real graph-pull work). **0.19.00** (feat → MINOR, HARD RULE).

---

## Deferred (S81)

- PM, execution, monitor, reporter graph-pull data paths (same bus→graph move; reuse
  `poll.py` + `run.py`-style shared core + `work_loop()`).
- Forecaster / control-plane agents (supervisor / curator / researcher / operator) work loops.
- P14 pub/sub doorbell overlay; dispatcher cron; Alpaca live keys.
