# Sprint 12 — Monitor agent (positions, exit decisions)

**Status:** planned · **Branch:** `sprint-12-monitor` · **Build phase:** P3 (decision loop) · **Effort: L**

## Goal

Implement the **`monitor`** agent — the P3 link that turns fills into open positions and decides
when to exit. It receives a `MonitorRequest(run_id)`, opens a `Position` node for every new
fill under that execution run, fetches current prices from the provider, evaluates stop / target
/ time exit rules, and emits a `CloseDecisionSet`. Positions that trigger an exit are submitted
to `execution.execute_close` on the bus. Every position evaluation is recorded as a
`PositionCheck`; every close decision gets a `CloseDecision -[:CLOSES]-> Position` edge.
**The full P3 provenance chain is proven in a 6-agent pipeline test.**

## Why (context)

- Sprint 11 implemented `execute_close` but could only exercise it via a fixture — `monitor` is
  the agent that actually drives it.
- After this sprint, only `reporter` remains before the P3 exit criterion is met.
- Read first: `docs/sprints/README.md` (guardrails + gate); **`contracts/monitor.py`** (the
  contract — `MonitorRequest`, `CloseDecision`, `CloseDecisionSet`, `explain_hold`; implement
  exactly, no changes); **`contracts/execution.py`** (`CloseDecisionSet` is consumed by
  `execute_close`); `contracts/portfolio_manager.py` (`OrderIntent.stop_pct`, `.target_pct`);
  `contracts/analyst.py` (`Recommendation` — no `horizon` field); **`agents/execution/store.py`**
  (post-merge — read to confirm the `ExecRun`/`Fill` node structure and fill key format);
  `agents/portfolio_manager/store.py` (cross-agent lineage pattern, money as cents);
  `agents/portfolio_manager/agent.py` (bus-call pattern for provider requests);
  `kernel/graph.py`, `kernel/config.py`; `agents/monitor/mission.md`;
  `docs/decisions/0001-neo4j-primary-store.md` (append-only, money as cents).

## Key design constraints (do not break)

- **Implement `contracts/monitor.py` exactly** — two capabilities:
  `check_positions(MonitorRequest) -> CloseDecisionSet` and
  `explain_hold(MonitorRequest) -> Explanation`. Do not change the contract.
- **The one rule.** `agents/monitor/` imports `kernel` + `contracts` only. It is the **sole**
  owner of `Position`, `PositionCheck`, and `CloseDecision` nodes. **Never** submit to the
  broker directly; send close decisions to `execution.execute_close` on the bus.
- **`MonitorRequest.run_id` is the PM run ID** (= `OrderIntentSet.run_id`, also
  `ExecutionResult.provenance.run_id` stripped of its `"execution-submit-"` prefix — pass the
  PM run ID directly). There is **no `ExecRun` parent node**: fills are written directly, keyed
  `f"{pm_run_id}:{ticker}:buy"`. To enumerate fills for a run: `get_node("PMRun", run_id)` →
  `ancestors(pm_run, max_depth=1, edge_types={"EMITTED_BY"})` → `OrderIntent` nodes (each has
  `ticker` + `action` props) → `get_node("Fill", f"{run_id}:{ticker}:buy")` for each buy
  intent. This is confirmed by `agents/execution/store.py` and the pipeline test
  (`test_p3_execution_slice.py:52`).
- **Position node is the stable unit.** Key: `f"{run_id}:{ticker}"` (matching the fill's run
  scope). A position is "open" if no `CloseDecision` with `decision="close"` has been written
  for it yet. Opening is idempotent: `merge_node` on the same key is a no-op.
- **Stop/target from the graph; horizon from settings.** Traverse
  `Fill -[:EXECUTES]-> OrderIntent` (one hop) to read `stop_pct` and `target_pct` props. The
  analyst's `Recommendation` node does not store `horizon` — use a `default_horizon_days`
  justified tunable in `MonitorSettings` as the time-based exit threshold. If the graph
  traversal for stop/target fails, fall back to settings defaults and record the degraded case.
- **Current prices via provider on the bus.** Call `provider.get_market_data` for each open
  ticker (same bus-call pattern as the analyst and portfolio manager). Use a tunable
  `price_lookback_days` window. In tests, `FakeDataSource` is injected — set prices to trigger
  deterministic exit scenarios.
- **Drive `execute_close` within `check_positions`.** After building the `CloseDecisionSet`,
  bus-call `execution.execute_close(close_decision_set)` for the decisions that include closes.
  Return the `CloseDecisionSet` as the capability response.
- **Money as integer cents in the graph; append-only; faults not silent.** `Fill.price` is
  `Money` in the payload; store `opened_price_cents` as an integer in the `Position` node. Wrap
  the provider call and broker dispatch in `fault_boundary`; a failed price fetch → skip that
  position with a degraded fault, never a crash.
- **Small files, headers, < 200 lines**; justified tunables; no magic numbers.

## Deliverables

1. **`agents/monitor/settings.py`** — `MonitorSettings(AgentSettings)`,
   `env_prefix="MONITOR_"`. Justified tunables: `default_horizon_days` (default 14, why:
   paper-stage default holding window when graph traversal yields no horizon),
   `price_lookback_days` (default 2, why: rolling window to get latest close price from
   provider), `default_stop_pct` / `default_target_pct` (fallback if OrderIntent props absent).

2. **`agents/monitor/domain/positions.py`** — given a `Fill` node and the graph, open a
   `Position` data structure: read `opened_price_cents` from the fill's stored price prop,
   `quantity` from the fill's props, then traverse `Fill -[:EXECUTES]-> OrderIntent` for
   `stop_pct` and `target_pct` (fall back to settings if absent or `None`). The `horizon_days`
   always comes from settings for now. Return a plain dataclass / dict suitable for
   `store.open_position`.

3. **`agents/monitor/domain/exit_rules.py`** — deterministic, pure exit evaluation:
   - `check_stop(current_price_cents, opened_price_cents, stop_pct) -> bool`
   - `check_target(current_price_cents, opened_price_cents, target_pct) -> bool`
   - `check_time(opened_at_iso, default_horizon_days) -> bool` — days since open ≥ horizon
   - `evaluate_position(position_props, current_price_cents, today) -> (decision, trigger)` —
     stop wins over target wins over time; returns `("close", trigger)` or `("hold", "none")`.

4. **`agents/monitor/store.py`** — graph write path:
   - `open_position(graph, run_id, ticker, props) -> Node` — idempotent `merge_node("Position",
     f"{run_id}:{ticker}", {...})` with `opened_price_cents`, `quantity`, `stop_pct`,
     `target_pct`, `horizon_days`, `opened_at`, `status="open"`.
   - Write `Fill -[:OPENS]-> Position` edge (reconstruct Fill key from the execution store
     pattern; skip gracefully if fill node not found).
   - `write_check(graph, monitor_run, position, decision, trigger, current_price_cents) ->
     Node` — `PositionCheck` node (`{run_id, ticker, checked_at, decision, trigger,
     current_price_cents}`) + `PositionCheck -[:CHECKS]-> Position`.
   - `write_close_decision(graph, monitor_run, position, decision, trigger, rationale) -> Node`
     — `CloseDecision` node + `CloseDecision -[:CLOSES]-> Position`.
   - `write_monitor_run(graph, run_id, exec_run_id, ...) -> Provenance` — top-level
     `MonitorRun` node (`{exec_run_id, positions_checked, closes, holds, created_at}`);
     return `Provenance(run_id=monitor_run_id, source_agent="monitor",
     graph_node_id=f"MonitorRun:{monitor_run_id}")`.

5. **`agents/monitor/agent.py`** — `MonitorAgent(AgentBase)` (inject `graph`, `bus`,
   `settings`, `sink`):
   - `check_positions` handler: locate fills via ExecRun traversal → open Position nodes
     (idempotent) → fetch current prices from provider → evaluate exit rules → write
     PositionCheck + CloseDecision nodes → bus-call `execution.execute_close` → return
     `CloseDecisionSet`.
   - `explain_hold` handler: find positions from this run that were held in the latest monitor
     pass → compose an `Explanation` of why each is still open (which rule was closest to
     triggering).

6. **`agents/monitor/__init__.py`** — export `MonitorAgent`. Update
   **`agents/monitor/mission.md`**: replace the stale "Postgres: positions, position_lifecycle_events,
   monitor_configs" data-ownership section with the graph model (ADR-0001).

7. **`agents/monitor/tests/`** — infra-free (`InProcessBus` + `InMemoryGraphStore` +
   `FakeDataSource` + `PaperBroker`):
   - **Position opens idempotently** from a Fill node in the graph; second call to
     `check_positions` with same `run_id` opens no duplicate Position nodes.
   - **Stop rule** triggers `decision="close"`, `trigger="stop"` when current price ≤ opened ×
     (1 − stop_pct). `PositionCheck` and `CloseDecision` written; `CLOSES` edge present.
   - **Target rule** triggers `decision="close"`, `trigger="target"`.
   - **Time rule** triggers `decision="close"`, `trigger="time"` when days held ≥
     `default_horizon_days`.
   - **Hold case**: price within bounds, time not elapsed → `decision="hold"`, `trigger="none"`;
     no `CloseDecision` node written.
   - **Provider failure** → degraded fault recorded, position skipped, no crash.
   - **`explain_hold`** returns a non-empty `Explanation` for a held position.
   - **Full 6-agent pipeline** — wire `provider + scanner + analyst + portfolio_manager +
     execution + monitor` on one bus with `FakeDataSource` + `PaperBroker`; drive
     `run_scan → analyze → evaluate_orders → submit → check_positions`; set `FakeDataSource`
     price below stop threshold so at least one close fires; assert the complete chain:

     ```text
     CloseDecision -[:CLOSES]-> Position -[:OPENED_BY_FILL]->
     Fill -[:EXECUTES]-> OrderIntent -[:APPROVES]-> Recommendation
     -[:DERIVED_FROM]-> Candidate -[:SURVIVED]-> ScanRun
     -[:DERIVED_FROM]-> MarketSnapshot
     ```

     with no agent importing another (boundary meta-test green).

8. **Coverage floor** — re-tune to the new measured value (ratchet from 99.5; never lower).

## Steps

1. Branch `sprint-12-monitor` off `main` (after Sprint 11 is merged).
2. Read `agents/execution/store.py` to confirm `ExecRun` / `Fill` node label and key format
   before writing any graph traversal.
3. `settings.py`; `domain/positions.py`; `domain/exit_rules.py`.
4. `store.py` (Position + PositionCheck + CloseDecision + edges).
5. `agent.py` (two handlers); `__init__.py`; refresh `mission.md`.
6. Write the tests (unit rules + idempotency + provider failure + 6-agent pipeline).
7. Run the gate; re-tune the floor. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- Both capabilities answer over the bus; `import-linter` "agents may not import one another"
  KEPT; boundary meta-test green.
- **Idempotency:** double-call with same `run_id` → no duplicate Position nodes. Stop / target
  / time rules each proven by a dedicated test. Hold case written with no CloseDecision node.
- `CloseDecision -[:CLOSES]-> Position` edge written; `CHECKS` edge from PositionCheck to
  Position written; `OPENS` edge from Fill to Position written.
- Full 6-agent pipeline test asserts the complete chain to `MarketSnapshot`.
- `execute_close` is driven from `check_positions` over the bus (not via import).
- `mission.md` updated: Postgres ownership replaced with graph model.
- All modules headered, < 200 lines; tunables justified; `make ci` green at/above the floor.

## Out of scope (do NOT build this sprint)

The `reporter` (next P3 sprint); regime-based exit (needs forecaster, P4+); `exits_decided`
as real pub/sub (P4 orchestration — record in provenance for now); multi-day position lifecycle
across separate runs (P4+ — one execution run ↔ one monitor pass is sufficient for P3);
forecaster advisory exit signal; MCP (`mcp.py`). Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the ExecRun → Fill traversal approach; how
  stop/target/horizon pcts are sourced from the graph vs settings; the drive-execute_close
  flow.
- New coverage % and the re-tuned floor; confirmation the 6-agent pipeline test passes with
  the full provenance chain.
- Any design decision worth recording or anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`. After this, P3 continues with `reporter`.
