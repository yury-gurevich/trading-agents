# Sprint 13 — Reporter agent (run snapshot + per-trade narrative)

**Status:** shipped (merged to `main` @ `ab328a5`) · **Branch:** `sprint-13-reporter` · **Build phase:** P3 (decision loop) · **Effort: M**

## Goal

Implement the **`reporter`** agent — the final P3 link. It traverses the provenance graph to
produce a `RunSnapshot` (portfolio, signal, and regime metrics for a full paper run) and a
`TradeNarrative` (one stitched scan-to-exit story per position). It is **read-only** except for
writing its own `Snapshot` and `TradeNarrative` nodes. The **P3 exit criterion** is proven by a
**7-agent pipeline test** that drives the complete loop end-to-end and asserts both outputs are
produced with coherent content and no agent imports another.

## Why (context)

- Reporter is the only agent standing between the current state and P3 exit.
- P3 exit criterion: "a full paper trading day runs end-to-end with a stitched narrative and
  single-writer data ownership intact."
- Read first: `docs/sprints/README.md` (guardrails + gate); **`contracts/reporter.py`** (the
  contract — `ReportRequest`, `NarrativeRequest`, `RunSnapshot`, `TradeNarrative`; implement
  exactly); `agents/reporter/mission.md`; the full provenance graph written by earlier agents
  (read ALL of these stores to understand what props are available):
  - `agents/provider/store.py` — `MarketSnapshot` (`tickers`, `bar_count`, `created_at`);
    `Regime` (`label`, `vix`, `as_of`)
  - `agents/scanner/store.py` — `ScanRun`, `Candidate`
  - `agents/analyst/store.py` — `AnalystRun`, `Recommendation` (`confidence`, `technical_score`)
  - `agents/portfolio_manager/store.py` — `PMRun` (`approved_count`, `rejected_count`),
    `OrderIntent` (`ticker`, `action`, `quantity`, `stop_pct`, `target_pct`, `est_price_cents`)
  - `agents/execution/store.py` — `Fill` (`ticker`, `price_cents`, `status`)
  - `agents/monitor/store.py` — `Position` (`opened_price_cents`, `quantity`, `stop_pct`,
    `target_pct`, `horizon_days`, `opened_at`), `CloseDecision` (`trigger`, `rationale`),
    `MonitorRun` (`closes`, `holds`)
  - The Sprint 12 6-agent pipeline test for the full edge-type map
  - `kernel/graph.py` for the `GraphStore` protocol
  - `docs/decisions/0001-neo4j-primary-store.md` (append-only; reporter reads all, writes only
    its two labels)

## Key design constraints (do not break)

- **Implement `contracts/reporter.py` exactly** — two capabilities:
  `report(ReportRequest) -> RunSnapshot` and `narrative(NarrativeRequest) -> TradeNarrative`.
- **The one rule.** `agents/reporter/` imports `kernel` + `contracts` only. It reads the graph;
  it never imports another agent. It **never mutates** any other agent's nodes.
- **`ReportRequest.run_id` is the PM run ID** (same `run_id` used throughout — passed from
  `OrderIntentSet.run_id` / `MonitorRequest.run_id`). `NarrativeRequest.position_id` is the
  `Position` node key (`f"{pm_run_id}:{ticker}"`).
- **Graph traversal — the canonical edge map** (confirm against the store files above):

  ```text
  PMRun ←[:EMITTED_BY]─ OrderIntent ←[:EXECUTES]─ Fill ─[:OPENS]→ Position
                                     ─[:APPROVES]→ Recommendation ─[:DERIVED_FROM]→ Candidate
                                                                                    ─[:SURVIVED]→ ScanRun
                                                                                                  ─[:DERIVED_FROM]→ MarketSnapshot
  Position ←[:CLOSES]─ CloseDecision
  ```

  Traversal directions:
  - `ancestors(pm_run, max_depth=1, {"EMITTED_BY"})` → `OrderIntent` nodes
  - `ancestors(order_intent, max_depth=1, {"EXECUTES"})` → `Fill` nodes
  - `descendants(fill, max_depth=1, {"OPENS"})` → `Position` nodes
  - `descendants(order_intent, max_depth=1, {"APPROVES"})` → `Recommendation` nodes
  - `ancestors(position, max_depth=1, {"CLOSES"})` → `CloseDecision` nodes (absent if held)
  - `descendants(recommendation, max_depth=1, {"DERIVED_FROM"})` → `Candidate` nodes
  - `descendants(candidate, max_depth=1, {"SURVIVED"})` → `ScanRun` nodes
  - `descendants(scan_run, max_depth=1, {"DERIVED_FROM"})` → `MarketSnapshot` nodes
  - Regime: the `Regime` node is a separate provider artifact (not linked to the scan chain);
    locate it via `get_node("Regime", key)` — the key is `"provider-regime-{uuid}"` from the
    provider's store. Since the key is opaque, the simplest approach for P3 is: when building
    metrics, skip regime attribution if no direct link is reachable (return `{}` or
    `{"vix_available": 0.0}`); flag this as a known gap (regime ↔ run linkage is a P6 surface
    concern). If the analyst run links to a Regime node (check `agents/analyst/store.py`), use
    that instead.
- **Graceful missing nodes.** Any traversal leg may return `None` or an empty iterator (a held
  position has no `CloseDecision`; a degraded run may have no `Recommendation`). Skip gracefully
  — never crash on a missing leg.
- **Module size.** `agents/reporter/agent.py` must be ≤ 150 lines (not ≤ 200) — keep headroom.
  Delegate metric collection to `domain/metrics.py` and narrative composition to
  `domain/narrative.py`. Note: `agents/monitor/agent.py` (197) and
  `agents/monitor/tests/test_monitor_agent.py` (198) are near the limit — do not touch those
  files; reporter does not need to.
- **Append-only; faults not silent.** Wrap the graph traversal in `fault_boundary`; a missing
  PM run returns a degraded but non-crashing snapshot. No magic numbers; no bare literals.

## Deliverables

1. **`agents/reporter/domain/metrics.py`** — pure functions over graph nodes:
   - `collect_portfolio_metrics(pm_run, positions, close_decisions) -> dict[str, float]`:
     `positions_opened`, `positions_closed`, `positions_held`, `close_trigger_stop`,
     `close_trigger_target`, `close_trigger_time`, `approval_rate` (from pm_run props).
   - `collect_signal_metrics(recommendations) -> dict[str, float]`:
     `recommendation_count`, `avg_confidence`, `avg_technical_score`, `rejection_count`.
   - `collect_regime_attribution(scan_runs, market_snapshots) -> dict[str, float]`: best-effort
     for P3 — `snapshots_used`, `bar_count_total`; return `{}` if inputs empty.

2. **`agents/reporter/domain/narrative.py`** — compose one position's trade story:
   - `compose_story(position, fill, order_intent, recommendation, candidate, scan_run, close_decision | None) -> str`
     — deterministic string from node props. Shape (adapt as needed):
     `"{ticker} scanned [{scan_date}]. Technical score {score:.2f}, confidence {conf:.0%} → {action}.
     {quantity} shares approved, est. {price_cents/100:.2f}, stop {stop_pct:.0%} / target {target_pct:.0%}.
     Position opened at {opened_price_cents/100:.2f}.
     Exit: {trigger} — {rationale}."` (or `"Position still open."` if no close decision.)
   - Skip any missing leg with a `"(data unavailable)"` placeholder rather than crashing.

3. **`agents/reporter/store.py`** — two writes:
   - `write_snapshot(graph, run_id, metrics_blob, headline_summary) -> Provenance`:
     `merge_node("Snapshot", f"snapshot:{run_id}", {...})` + edge
     `Snapshot -[:SUMMARISES]-> PMRun` (skip if PMRun not found).
   - `write_trade_narrative(graph, run_id, position_id, story) -> Provenance`:
     `merge_node("TradeNarrative", f"narrative:{position_id}", {...})` + edge
     `TradeNarrative -[:NARRATES]-> Position` (skip if Position not found).

4. **`agents/reporter/agent.py`** — `ReporterAgent(AgentBase)` (inject `graph`, `settings`,
   `sink`), ≤ 150 lines:
   - `report` handler: get PMRun → traverse → collect metrics → compose headline → write
     `Snapshot` → return `RunSnapshot`.
   - `narrative` handler: get Position → traverse the chain → compose story → write
     `TradeNarrative` → return `TradeNarrative`.

5. **`agents/reporter/settings.py`** — `ReporterSettings(AgentSettings)`,
   `env_prefix="REPORTER_"`. No tunables needed for P3 — a placeholder with one justified
   stub is fine (e.g. `max_narrative_length_chars` for future truncation).

6. **`agents/reporter/__init__.py`** — export `ReporterAgent`. Update
   **`agents/reporter/mission.md`**: replace stale "Postgres: performance_snapshots,
   trade_narratives" with graph model (ADR-0001).

7. **`agents/reporter/tests/`** — infra-free (`InProcessBus` + `InMemoryGraphStore`):
   - `report` returns a `RunSnapshot` with `portfolio_metrics["positions_opened"] >= 1` and a
     non-empty `headline.summary`; `Snapshot` node written to graph with `SUMMARISES` edge.
   - `narrative` returns a `TradeNarrative` with `story.summary` containing the ticker name;
     `TradeNarrative` node written to graph with `NARRATES` edge.
   - Missing-leg graceful: `report` on an empty graph returns a degraded snapshot, no crash;
     `narrative` with unknown `position_id` returns a degraded narrative, no crash.
   - **P3 exit test** (the headline) — `test_p3_reporter_slice.py`: wire all 7 agents
     (`provider + scanner + analyst + portfolio_manager + execution + monitor + reporter`) on one
     bus with `FakeDataSource` + `PaperBroker`; drive:

     ```text
     run_scan → analyze → evaluate_orders → submit
     → (rebind provider with lower price) → check_positions
     → report(pm_run_id) → narrative(f"{pm_run_id}:AAPL")
     ```

     Assert:
     - `RunSnapshot.portfolio_metrics["positions_opened"] >= 1`
     - `RunSnapshot.portfolio_metrics["positions_closed"] >= 1`
     - `RunSnapshot.signal_metrics["recommendation_count"] >= 1`
     - `RunSnapshot.headline.summary` is non-empty
     - `TradeNarrative.story.summary` contains "AAPL"
     - `graph` contains a `Snapshot` node and a `TradeNarrative` node
     - **No agent imports another** (boundary meta-test green) — **P3 exit criterion met**

8. **Coverage floor** — ratchet from 100.00; never lower.

## Steps

1. Branch `sprint-13-reporter` off `main`.
2. Read all six store files listed in **Why** to map every prop before writing a line of code.
3. `domain/metrics.py`; `domain/narrative.py`.
4. `store.py`; `settings.py`; `agent.py` (≤ 150 lines); `__init__.py`; refresh `mission.md`.
5. Write the tests — unit tests first, then the P3 exit pipeline test last.
6. Run the gate; confirm the P3 exit test passes; re-tune floor if needed. Push; hand back. Do
   not merge to `main`.

## Acceptance criteria

- Both capabilities answer over the bus; `import-linter` KEPT; boundary meta-test green.
- `RunSnapshot` contains non-empty `portfolio_metrics`, `signal_metrics`, and `headline`;
  `TradeNarrative.story.summary` is a non-empty string referencing the traded ticker.
- `Snapshot -[:SUMMARISES]-> PMRun` and `TradeNarrative -[:NARRATES]-> Position` edges written.
- Missing legs (no CloseDecision, empty graph) handled gracefully — no crash.
- `agent.py` ≤ 150 lines; all modules headered, < 200 lines; tunables justified.
- **P3 exit test green**: 7-agent pipeline produces coherent `RunSnapshot` + `TradeNarrative`
  with no agent importing another. **P3 exit criterion met.**
- `make ci` green at/above the floor; gate needs no external infra.

## Out of scope (do NOT build this sprint)

Realized P&L arithmetic (sell price minus buy price — execution's close fills need richer
linkage to position for this; defer to P6 surfaces); regime ↔ run edge linkage (provider writes
`Regime` nodes without connecting them to scan runs; surfacing this belongs in P6); the
`report_ready` pub/sub event (P4 orchestration — record in provenance for now); MCP (`mcp.py`);
`forecaster`. Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts (confirm `agent.py` ≤ 150).
- The traversal approach for `report` (how you collected metrics from the graph) and `narrative`
  (how you stitched the story); any legs that were absent and how you handled them.
- Whether regime attribution was reachable and what you put in that dict.
- New coverage % and floor; confirmation **the P3 exit test passes**.
- Any design decision worth recording (esp. anything that felt like it needed a contract change).

The planning agent will review, merge to `main`, close out P3, and update `docs/STATE.md` +
`docs/build-plan.md`. **P3 exit: the decision loop is complete.**
