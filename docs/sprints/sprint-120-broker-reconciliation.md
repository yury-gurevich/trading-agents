<!-- Agent: planning | Role: sprint handover -->
# Sprint 120 — Broker reconciliation: broker truth for holdings, graph truth for lineage (DL-44)

**Phase:** Production hardening of the self-driving fleet (DL-44; first defect of the standing-run era)
**Branch:** `sprint-120-broker-reconciliation`
**Status:** ready for handover (packaged 2026-07-08; execute after S119 merges)
**Effort:** M

---

## The defect this fixes (observed live, 2026-07-08)

The first unattended scheduled run **re-bought CSCO (89 sh) on top of the 88 sh the paper account
already held**, because live-check teardowns had deleted the `Position`/`Fill` nodes for trades the
broker still holds — the fleet started blind to real holdings. Separately, the 22:34 UTC
after-hours order's `Fill` node says `pending` forever; nothing refreshes broker order status after
a run ends. Root cause is a regime change, not a bug: teardown-to-zero was correct while live runs
were disposable proofs; since S103 the runs are production and the broker account is standing
state. Full analysis: design-log **DL-44**. Policy line to implement, verbatim:
**broker = truth for holdings; graph = truth for lineage.**

## Codex kickoff (paste this)

> Execute **Sprint 120 — broker reconciliation** exactly as specified in this file
> (`docs/sprints/sprint-120-broker-reconciliation.md`). Read first: design-log **DL-44** (policy +
> ruled-out roads), `agents/execution/broker.py` (the `Broker` protocol) + `alpaca.py` +
> `broker_factory.py`, `agents/execution/poll.py` + `stage_flow.py` (where the run-start hook
> belongs), `agents/monitor/store.py` + `domain/positions.py` (Position ownership), and the S102/
> S103 closeouts (how the divergence arose).
>
> - **Start:** from `main` (`git pull` — S119 must already be merged), `git checkout -b
>   sprint-120-broker-reconciliation` (delete any stale local branch first). **Hard gate:**
>   `make ci` green, 100 % coverage, ≤200-line modules, headers. Bump `pyproject.toml`
>   **0.64.00 → 0.65.00** (feat) + `uv lock`. (If S119 landed differently, bump feat from
>   whatever `main` holds.)
> - **Part A — reconciliation (code, CI-tested; islands respected):**
>   1. **Broker port, additive:** read-only `positions()` on the `Broker` protocol returning
>      typed holdings (ticker, qty, avg-entry cents, market-value cents). `AlpacaBroker` → GET
>      `/v2/positions`; `PaperBroker` → its in-memory book. Also an order-status read for
>      refreshing pending fills (reuse `_list_orders`/`fills()` if it already suffices — trace
>      first, don't duplicate).
>   2. **Execution-owned reconciliation step, run-start:** before executing new intents, the
>      execution agent (a) refreshes any graph `Fill` nodes still `pending` from broker order
>      status; (b) fetches broker positions and writes a **`BrokerPositionSnapshot`** node
>      (stamped, append-only) with the holdings; (c) compares against current graph `Position`
>      nodes — any divergence (missing, extra, qty mismatch) is **loud**: write a `Flag` on the
>      supervisor path stating each difference. Fail-open on broker read errors (log + proceed —
>      a dead broker read must not kill the run; the staleness of the snapshot is stated).
>   3. **Monitor adopts broker truth:** monitor's position logic reconciles its `Position` nodes
>      from the latest `BrokerPositionSnapshot` — creating missing positions with provenance
>      `reconciled-from-broker` (broker avg-entry as basis; never fabricate decision lineage) and
>      flagging (not deleting) graph positions the broker doesn't hold. Execution does not touch
>      `Position` nodes; monitor does not touch the broker — the snapshot node is the seam.
>   4. **PM held-position awareness:** verify the PM's sizing/max-positions/sector gates read the
>      reconciled `Position` picture; if they read something else, state what and wire the gap
>      (additive; gate_report already renders the outcomes per DL-41).
>   5. **Teardown discipline (docs):** amend the teardown guidance in
>      `docs/laws/functionality-checks.md` (header note): `Position`/`Fill` rows mirroring real
>      broker holdings are production state — checks that trade must run reconciliation after
>      teardown; stamped test artifacts remain fully torn down. Add a drift-register entry citing
>      the CSCO double-buy with the regression test for the reconciliation step.
> - **Part B — live check = the repair (real paper account, real Neon):**
>   1. Run the reconciliation live: first pass must **detect divergence loudly** (graph holds ~0
>      positions; broker holds AMD/CSCO/HPE/MRVL) — capture the Flag content — and create the
>      four `Position` nodes with `reconciled-from-broker` provenance, quantities/entries equal
>      to the broker's (CSCO will be the combined post-fill quantity; record what the broker
>      reports). Verify from a separate raw connection.
>   2. Second pass immediately after: **no divergence, no new Flag** (idempotence proof).
>   3. Pending-fill refresh proof: the S103-era `pending` CSCO `Fill`
>      (`pm-run-…:CSCO:buy`, broker id `632f0604…`) reflects its real terminal status afterwards.
>   4. **Do NOT tear down the reconciled `Position` nodes or the account** — they are production
>      state (DL-44). Tear down only stamped test extras your check created. Record everything in
>      `docs/laws/functionality-checks.md`. Never print the DSN or API keys.
> - **Out of scope — flag, don't build:** monitor pnl_cents re-point to broker valuations (S43,
>   queued — related but separate); selling/flattening anything at the broker; cash/equity
>   reconciliation; any scheduling change; live-capital anything.
> - **Do NOT merge or push to `main`** — commit on the branch only; fill **Closeout evidence** here.

---

## Notes for the coding agent

- Alpaca paper endpoint + key aliases are in `agents/execution/settings.py`; the account currently
  holds AMD 19 / CSCO 88(+89 pending fill) / HPE 229 / MRVL 44 — your live check's expected input.
- The broker read is read-only throughout; this sprint must not place, cancel, or modify any
  order. (`cancel()` exists on the port — do not call it.)
- Money is integer cents everywhere in the graph (house convention) — convert Alpaca's decimal
  strings once at the adapter edge.
- Execution's laws (`agents/execution/laws/laws.md`) are LOCKED — the reconciliation step must fit
  within existing clauses; if any clause needs reinterpretation, cite it in the test docstring per
  the law convention, and if text must change, stop and flag instead.
- The fleet is standing (KEDA windows) — after merge, the next 22:30 UTC run picks up the new
  images automatically; no redeploy step beyond the normal merge trigger.

---

## Closeout evidence

Branch-only closeout on `sprint-120-broker-reconciliation`; **not merged or pushed to `main`**.

Files changed:

- Execution: `agents/execution/broker.py`, `agents/execution/alpaca.py`,
  `agents/execution/alpaca_positions.py`, `agents/execution/order_status_store.py`,
  `agents/execution/reconciliation.py`, `agents/execution/reconciliation_store.py`,
  `agents/execution/poll.py`, `contracts/execution.py`.
- Monitor/PM: `agents/monitor/position_book.py`, `agents/monitor/reconcile.py`,
  `agents/monitor/run.py`, `agents/portfolio_manager/graph_portfolio.py`,
  `agents/portfolio_manager/poll.py`.
- Tests/docs/version: S120 execution, monitor, and PM regression tests; `pyproject.toml`,
  `uv.lock`, `docs/laws/functionality-checks.md`, `docs/laws/drift-register.md`.

Version/deps:

- `pyproject.toml` bumped `0.64.00 -> 0.65.00`; `uv lock` updated the root package entry
  from `0.64.0` to `0.65.0`.

Hard gate:

- `make ci` exited 0.
- Pytest summary: `1436 passed, 5 skipped in 89.35s`.
- Coverage: `TOTAL 9943 0 2016 0 100.00%`; required `100.0%` reached.
- `detect-secrets` passed. `pip-audit` still reports known optional `diskcache 5.6.3 /
  CVE-2025-69872`; the Makefile ignored that non-runtime advisory as before.

Part A regression evidence:

- Divergence Flag + pending order refresh:
  `agents/execution/tests/test_reconciliation.py::test_reconcile_run_start_snapshots_flags_and_refreshes_pending_fills`.
- Fail-open broker-read behavior:
  `agents/execution/tests/test_reconciliation.py::test_reconcile_run_start_fail_open_on_broker_positions_error`.
- Idempotent monitor adoption:
  `agents/monitor/tests/test_broker_reconcile.py::test_reconcile_positions_from_snapshot_creates_broker_positions_once`.
- Graph-vs-broker mismatch marking:
  `agents/monitor/tests/test_broker_reconcile.py::test_reconcile_positions_marks_absent_and_superseded_positions`.
- PM held-position awareness:
  `agents/portfolio_manager/tests/test_graph_portfolio.py::test_evaluate_analyst_node_uses_graph_positions_for_max_positions_gate`.

Live check (real Alpaca paper + real Neon via `POSTGRES_DSN`; secrets not printed):

- **Deviation from the planned first-pass shape:** the production graph no longer held ~0 positions
  at the start of this branch's live check. A stale S120 live repair had already created the
  production `reconciled-from-broker` Position nodes and the loud divergence Flag. Per DL-44, those
  rows mirror real broker holdings, so they were not deleted to recreate the missing-positions state.
- Retained first-pass divergence Flag content, verified on Neon:

```text
Broker position divergence detected:
- missing graph Position for AMD: broker_qty=19
- missing graph Position for CSCO: broker_qty=88
- missing graph Position for HPE: broker_qty=229
- missing graph Position for MRVL: broker_qty=44
```

- Broker holdings reported during the branch live check:
  `AMD qty=19 avg_entry_cents=51235 market_value_cents=976600`,
  `CSCO qty=88 avg_entry_cents=11277 market_value_cents=985600`,
  `HPE qty=229 avg_entry_cents=4355 market_value_cents=997753`,
  `MRVL qty=44 avg_entry_cents=22621 market_value_cents=1001000`.
- Raw Neon verification found the four active reconciled Position nodes:
  `Position/broker-reconciled:AMD qty=19 opened_price_cents=51235 provenance=reconciled-from-broker`;
  `Position/broker-reconciled:CSCO qty=88 opened_price_cents=11277 provenance=reconciled-from-broker`;
  `Position/broker-reconciled:HPE qty=229 opened_price_cents=4355 provenance=reconciled-from-broker`;
  `Position/broker-reconciled:MRVL qty=44 opened_price_cents=22621 provenance=reconciled-from-broker`.
- Current-branch first run-start pass appended fresh snapshot
  `broker-position-snapshot:s120-livecheck-20260708T054129Z:first:2026-07-08T05:41:31.136978+00:00`;
  new divergence Flag delta was `0` because the repaired Positions already matched broker truth.
- Current-branch second run-start pass appended fresh snapshot
  `broker-position-snapshot:s120-livecheck-20260708T054129Z:second:2026-07-08T05:41:33.045903+00:00`;
  new divergence Flag delta was again `0` (idempotence proof).
- Pending-fill refresh live proof: Fill
  `pm-run-b4e1cd7618b14bdbb7ecc98ee4d0a370:CSCO:buy`, broker id
  `632f0604-d36a-4f82-9c19-d621f19710ad`, still has graph `status=pending`; Alpaca also still
  reports that broker order as `pending`. The branch appended two `BrokerOrderStatus` evidence nodes
  with `status=pending`. **Deviation:** the requested terminal-status mutation could not be truthfully
  proven live because the real broker still reports non-terminal status, so no terminal status was
  fabricated. The terminal mutation path is covered by the execution regression test above.

Teardown and scope:

- No order was placed, canceled, sold, or flattened.
- No Position nodes and no account holdings were torn down; the reconciled Position rows are
  production state under DL-44.
- No disposable stamped extras were created beyond append-only reconciliation audit evidence
  (`BrokerPositionSnapshot` and `BrokerOrderStatus`).
- Out of scope stayed out of scope: no monitor `pnl_cents` valuation re-point, no cash/equity
  reconciliation, no scheduling change, no broker-side sell/flatten.

Docs:

- `docs/laws/functionality-checks.md` now has the S120 standing broker-state teardown note and the
  S120 live-check row.
- `docs/laws/drift-register.md` now has `DRIFT-020` for the CSCO double-buy, corrected by S120.
