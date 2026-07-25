<!-- Agent: planning | Role: sprint handover -->
# Sprint 138 — Broker-native stops (ADR-0015 §3, stop-only)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-138-broker-native-stops`
**Status:** ready for handover (packaged 2026-07-25)
**Effort:** L
**Decisions:** [ADR-0015 §3](../decisions/0015-exit-lifecycle-and-stop-ownership.md) ·
[ADR-0017](../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md) · design-log **DL-61**

---

## Why this sprint

ADR-0017 shipped (S137) and made the analyst the sole exit decider, forcing a breached stop onto
the daily rail as the **interim** floor — and named ADR-0015 §3 (a stop resting at the broker) as
its **durable** home. That home does not exist yet. Until it does, a stop is only re-evaluated once
a night at 22:30 UTC, so a gap-down between the run and the next open goes uncaught.

This sprint builds the durable floor: a **resting sell stop at the broker** for every held position.
The design, options weighed, and the append-only handling are worked out in full in **DL-61** — read
it first; this doc is the implementation handover.

**The one assumption is already proven.** ADR-0015 §3 flagged "does Alpaca paper accept an
after-hours `gtc` stop and rest it?" as its single unverified point. Probed 2026-07-25 (market
closed): an `AMD` `gtc` sell stop 30% below market returned `status=accepted, type=stop, tif=gtc`,
rested, and cancelled clean. Build to `gtc` stops; do not re-probe, and do not fire live orders.

**Two design points that are NOT the original §3 (both in DL-61):**

- **Stop-only, no take-profit leg.** ADR-0017 retired `target`; a `bracket`/`oco` take-profit leg
  would re-introduce the mechanical profit-taking we just deleted. A resting **sell stop** only.
- **The S137 forced-stop becomes a gated fallback, not a peer** — the analyst defers to a live
  broker stop, so the two can never double-sell.

---

## Spec

### Part A — a stop on the broker port

`agents/execution/broker.py::Broker` is market-only:
`submit(idempotency_key, ticker, side, quantity, limit_price)`. Add a **new method** (do not change
`submit`'s signature — three call sites depend on it):

```text
submit_stop(idempotency_key, ticker, side, quantity, stop_price: Money, tif="gtc") -> BrokerFill
```

- **AlpacaBroker.submit_stop** — order body `{symbol, qty, side, type:"stop", stop_price,
  time_in_force:"gtc", client_order_id}`; reuse `_submit_or_get` (422 → GET-by-client replay) and
  `_fill_from_order`. A resting stop returns a **pending** BrokerFill (`accepted`/`new`/`held` →
  `pending`), not filled.
- **PaperBroker.submit_stop** — a resting stop does **not** fill immediately (unlike `submit`):
  record a `pending` BrokerFill under the key, replay on dupe. A pending stop must not move the
  implied book in `_positions_from_fills` (only `filled`/`partial` do — confirm).
- Direct unit tests on both implementations.

### Part B — place a resting sell stop on every active held position each run (execution)

In execution's graph-pull path, **after reconciliation**, for each active held ticker
(`contracts/positions.py::open_position_stop_thresholds` — already returns quantity-weighted-avg
`opened_price_cents` + `stop_pct`, raising on lot disagreement):

- **Skip if it is being exited this run** — there is a `sell` `OrderIntent` for that ticker in the
  run's `OrderIntentSet`. Do not put a stop under an order that is closing the position.
- **Skip if a live `BrokerStopOrder` already exists** for its `stop:{position_ref}:{ticker}` key
  (idempotent; the immutable node is the guard, and the same string as `client_order_id` makes the
  broker replay too — double idempotency, like the S135 exit key).
- Otherwise `submit_stop(side="sell", quantity=full held qty, stop_price=<threshold as Money>,
  tif="gtc")` and write an **immutable** `BrokerStopOrder` node
  `{ticker, position_ref, stop_price_cents, broker_order_id, placed_at}` with an edge from the
  Position(s) it protects. Whole shares only.

**Stop price** in cents is `opened_price_cents*(10000 - round(stop_pct*10000)) // 10000` — mirror
`contracts/stop_rule.py::check_stop`'s own arithmetic (extract/reuse so the numbers cannot drift).

Define `BrokerStopOrder` as a shared read-model + accessors in `contracts` (label owned by execution
in its contract's `owns_graph`), so the analyst reads it without importing execution — the same
pattern as `contracts/positions.py` defining `OpenPosition` while agents write `Position` nodes.
Provide `contracts` accessor `active_broker_stop_refs(graph) -> frozenset[str]` (position_refs of
BrokerStopOrder nodes with no `cancelled_at`) for Part C, plus whatever Part D needs.

### Part C — the analyst forced-stop defers to a live broker stop (no double-sell)

Gate the S137 short-circuit in `agents/analyst/domain/recommend.py::decide(held=True)`: the analyst
forces a stop-sell **only when the held position has no live broker stop**. Thread
`active_broker_stop_refs(graph)` to the analyst the same way S137 threads held stop thresholds; apply
`stop_breached` **only if the position's `position_ref` is not in that set**. When a live broker stop
exists the broker owns the floor and the analyst does not force a sell (thesis `sell`/`hold` still
apply normally). Do **not** delete or weaken the S137 forced-stop — it stays fully tested as the
gated fallback.

Intended one-run transition (fine — do not "fix"): on the first run after deploy no stops exist yet,
so the analyst still force-sells breached names that run; execution then places stops on the
survivors; from the next run the analyst defers. That is the fallback working as designed.

### Part D — cancel a stop that no longer protects a live position (execution, in reconciliation)

A resting stop must not dangle after its position is gone (thesis exit filled, stop filled, or a
re-basis changed the `position_ref`). After reconciliation, for each `BrokerStopOrder` with no
`cancelled_at` whose `position_ref` is **no longer an active position**: `cancel(broker_order_id)`
(the method already exists on `AlpacaBroker`) and append `cancelled_at` (UTC ISO) to the node (new
key — append-only safe). One pass covers thesis-exit cleanup and re-basis cleanup; a re-based
position gets a fresh `stop:{new_ref}` from Part B next run.

---

## Required tests (prove behaviour on the GRAPH-PULL path, not only the bus path)

- `submit_stop` unit tests: `PaperBroker` (pending, not filled; pending ignored by the implied
  book) and `AlpacaBroker` (body has `type=stop, stop_price, tif=gtc`; 422 replay).
- Held position with no existing stop → one `BrokerStopOrder` at the weighted-avg threshold price,
  full qty, gtc, with `broker_order_id`. Re-run is idempotent (no second stop for that `position_ref`).
- A ticker **sold this run** gets **no** stop placed under it.
- Analyst **defers**: a breached held name **with** a live broker stop returns `hold`/thesis, **not**
  a forced `exit_trigger="stop"`; the **same** name **without** a broker stop still force-sells
  (S137 behaviour preserved).
- A stop **fill** closes the position through the **existing** reconciliation + books realized PnL
  from the fill price (assert **no new closure path** was added).
- Part D: a `BrokerStopOrder` whose position is gone is cancelled and marked `cancelled_at`; a
  second pass is a no-op.

---

## Hard constraints (CLAUDE.md)

- `make ci` must pass: 9 steps, **100% coverage floor** — every new line needs a test.
- Module size: **200 hard block / 150 warn** — split rather than grow.
- Layering: `kernel <- contracts <- agents <- orchestration/surfaces`; agents never import agents.
- Version in `pyproject.toml`: **feat** (new capability: broker-native stops) → `0.76.00` → `0.77.00`.
  Bump the execution (and analyst, if its inputs change) contract version on a payload/`owns_graph` change.
- **The graph records facts; it does not hold mutable records.** Stop liveness is the broker's truth
  (DL-44) + an appended `cancelled_at` marker — never a mutable `status` field.
- No `# noqa` to bypass any gate.

## Do not

- Do not commit, push, merge, or touch `main`. Work only in this worktree.
- Do not build a take-profit/`bracket`/`oco` leg, trailing logic, or any profit-taking (ADR-0017
  retired it).
- Do not build a monitor→execution close-dispatch path (DL-60). One rail.
- Do not fire live orders against the production broker/graph — the human deploys and verifies.
- Do not modify `docs/STATE.md`, the ADRs, `docs/design-log.md` DL-61 (already written), `infra/`, or `.env`.
- Do not delete or weaken the S137 analyst forced-stop — it becomes the gated fallback, still fully tested.
- If you hit an append-only conflict, an ordering hazard you cannot sequence cleanly, or a boundary
  violation, **STOP and report** — do not guess.

---

## Closeout — evidence (coding agent fills at handback; never leave this placeholder)

- **Files changed:**
  - `agents/analyst/domain/analyze.py`
  - `agents/analyst/run.py`
  - `agents/analyst/tests/test_broker_stop_deferral.py` (new)
  - `agents/execution/agent.py`
  - `agents/execution/alpaca.py`
  - `agents/execution/alpaca_orders.py` (new)
  - `agents/execution/broker.py`
  - `agents/execution/broker_factory.py`
  - `agents/execution/broker_stop_actions.py` (new)
  - `agents/execution/broker_stops.py` (new)
  - `agents/execution/paper_broker.py` (new)
  - `agents/execution/poll.py`
  - `agents/execution/realized_pnl.py`
  - `agents/execution/tests/broker_protocol_helpers.py` (new)
  - `agents/execution/tests/broker_stop_helpers.py` (new)
  - `agents/execution/tests/test_broker_stop_edges.py` (new)
  - `agents/execution/tests/helpers.py`
  - `agents/execution/tests/test_alpaca_broker.py`
  - `agents/execution/tests/test_alpaca_stop_orders.py` (new)
  - `agents/execution/tests/test_broker_positions.py`
  - `agents/execution/tests/test_broker_stops.py` (new)
  - `agents/execution/tests/test_execution_agent.py`
  - `agents/execution/tests/test_execution_poll.py`
  - `agents/execution/tests/test_reconciliation.py`
  - `agents/monitor/tests/helpers.py`
  - `agents/monitor/tests/test_p3_monitor_slice.py`
  - `agents/reporter/tests/p3_helpers.py`
  - `agents/reporter/tests/test_p3_reporter_slice.py`
  - `contracts/analyst.py`
  - `contracts/broker_stops.py` (new)
  - `contracts/execution.py`
  - `contracts/positions.py`
  - `contracts/stop_rule.py`
  - `docs/sprints/sprint-138-broker-native-stops.md`
  - `orchestration/tests/test_adr0015_graph_pull.py`
  - `orchestration/tests/test_batch_trace.py`
  - `orchestration/tests/test_dispatcher_unit.py`
  - `orchestration/tests/test_forecaster_stage.py`
  - `orchestration/tests/test_graph_pull_e2e.py`
  - `orchestration/tests/test_p4_celery_parity.py`
  - `orchestration/tests/test_p4_daily_loop.py`
  - `orchestration/tests/test_p4_scheduler.py`
  - `orchestration/tests/test_realized_pnl_graph_pull.py`
  - `orchestration/tests/test_resume.py`
  - `orchestration/tests/test_trading_acceptance.py`
  - `orchestration/tests/test_trading_acceptance_outcomes.py`
  - `orchestration/tests/test_trading_observatory.py`
  - `orchestration/tests/test_unified_decision_run.py`
  - `orchestration/tests/test_veto_stage.py`
  - `pyproject.toml`
  - `scripts/run_local.py`
  - `surfaces/context.py`
  - `surfaces/tests/test_context.py`
  - `surfaces/tests/test_dashboard_projections.py`
  - `surfaces/tests/test_p9_exit.py`
  - `tests/test_broker_stops_contract.py` (new)
  - `tests/test_contract_values.py`
  - `tests/test_positions_contract.py`
  - `tests/test_stop_rule.py`
  - `uv.lock`
  - Pre-existing unrelated local change retained and not used for Sprint 138:
    `docs/sprints/sprint-136-realized-pnl-and-gate-integrity.md`
- **`make ci` verbatim result:** exit code `0`.

  ```text
  TOTAL                                                12079      0   2520      0  100.00%
  Coverage HTML written to dir htmlcov
  Required test coverage of 100.0% reached. Total coverage: 100.00%
  =========================== short test summary info ===========================
  SKIPPED [1] tests\test_bus_azure.py:133: AZURE_SERVICEBUS_CONNECTION_STRING is not set
  SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
  SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
  SKIPPED [1] agents\provider\tests\test_sources.py:134: FINNHUB_TEST_NETWORK=1 is not set
  SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
  ================= 1809 passed, 5 skipped in 153.85s (0:02:33) =================
  uv run pip-audit
  No known vulnerabilities found
  uv run pre-commit run detect-secrets --all-files
  Detect secrets...........................................................Passed
  uv run python scripts/check_untracked_secrets.py
  Detect secrets...........................................................Passed
  detect-secrets (untracked): scanning 12 new file(s)
  ```
  Post-evidence sanity: `git diff --check` exit code `0`; `uv run pre-commit run
  detect-secrets --files docs/sprints/sprint-138-broker-native-stops.md` exit code `0`.
- **Stop-price formula + where extracted from:** extracted into
  `contracts/stop_rule.py::stop_price_cents`:

  ```text
  opened_price_cents*(10000 - round(stop_pct*10000)) // 10000
  ```

  `contracts/stop_rule.py::check_stop` now calls that helper, and execution imports the same helper
  in `agents/execution/broker_stop_actions.py`, so the analyst fallback and broker-native stop
  placement cannot drift on cents arithmetic.
- **`BrokerStopOrder` liveness under append-only:** execution writes immutable
  `BrokerStopOrder` facts keyed as `stop:{position_ref}:{ticker}` with `{ticker, position_ref,
  stop_price_cents, broker_order_id, placed_at}`. Liveness is derived by contracts accessors:
  active stops are `BrokerStopOrder` nodes with no `cancelled_at`. Reconciliation never mutates a
  status field; it calls `broker.cancel(broker_order_id)` for stops whose `position_ref` no longer
  appears in active positions, then appends `cancelled_at`. Placement also requires a fresh broker
  position snapshot with matching ticker quantity, so a graph-active but broker-absent holding does
  not receive a new stop while monitor reconciliation catches up.
- **Part B sequencing vs a same-run thesis sell:** execution now reconciles broker positions first,
  cancels stale broker stops, then places missing stops before submitting the run's market orders.
  `agents/execution/broker_stops.py::place_broker_stops` derives the post-veto same-run sell ticker
  set from the `OrderIntentSet` and skips those tickers, so execution never puts a protective stop
  under a position that the same run is already selling. The immutable graph key and broker
  `client_order_id` provide double idempotency on rerun.
- **Anything not done, and why:** no commit, push, merge, deploy, or live order was performed. No
  take-profit, bracket, OCO, trailing-stop, monitor-to-execution close-dispatch, infra, `.env`,
  `docs/STATE.md`, ADR, or DL-61/design-log change was made because the sprint explicitly excludes
  those paths.
