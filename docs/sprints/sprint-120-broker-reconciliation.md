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

<!-- Coding agent: replace this comment. Required: files changed; version/deps; exact `make ci`
summary (counts + coverage); Part A test evidence incl. the divergence-Flag and idempotence tests;
live evidence — first-pass Flag content verbatim, the four reconciled Position nodes (label/key/
qty/provenance) verified raw, second-pass no-divergence proof, pending-Fill terminal-status proof;
statement that no order was placed/canceled and no Position teardown occurred; the
functionality-checks.md amendment + drift-register entry; the functionality-checks.md row. State
any deviation from spec explicitly. Do not merge. -->
