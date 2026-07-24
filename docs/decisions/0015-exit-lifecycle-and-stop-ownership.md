---
type: Architecture Decision
status: amended
closes: "What closes a position — a decision or a fill? Who enforces the stop: our daily loop or the broker? What happens when a sell is refused or partially fills?"
tags: [exits, monitor, execution, alpaca, bracket, oco, stops, dl-58, dl-59, dl-60]
---

# ADR 0015 — A position is closed by a fill; the broker enforces the stop

**Status:** Amended · **Date:** 2026-07-23 · **Amended:** 2026-07-24 · **Decider:** Yury Gurevich (product owner)

> **Read the amendment first (2026-07-24).** Three clauses below describe a design that was
> **not** what shipped, and one of them is **not buildable at all**. The corrections are in
> [What actually shipped](#what-actually-shipped-amendment-2026-07-24) at the end of this file.
> The *decision* — a position is closed by evidence, not by our own intent — stands and is live;
> the prescribed **mechanism** changed. Do not implement §1's `CLOSES`-on-fill or §2's
> position-keyed node from the text above without reading the amendment.

## Context

The system has never sold anything. Across its entire lifetime the broker shows **zero sell
orders** against 33 buys, while the graph believed it had exited a position.

Three defects produced that, found in one day (2026-07-23):

- **DL-58** — `CloseDecision` carried no quantity or price, so execution substituted fixture
  tunables (`close_quantity=1`, `close_reference_price=$1.00`). Fixed in 0.73.01.
- **DL-59** — acceptance scored `execution.submitted`, an *intent* count, so two days on which
  every order was rejected for want of buying power both scored `ACCEPTANCE PASS`. Fixed in
  0.73.02 with the `UNPROVEN` verdict.
- **DL-60** — the fix landed on `s135` and the sell count stayed **0**. `dispatch_closes` is
  called only from the **bus RPC** path; the deployed runtime is **graph-pull**, where
  `monitor_pm_node` writes the decision and stops, and execution's poll consumes `PMRun` buys
  only. **No graph-pull consumer for close decisions exists.** The sell side is unbuilt, not
  broken.

Underneath the plumbing sat a lifecycle that converts a delivery failure into permanent capital
loss. `write_close_decision` adds the `CLOSES` edge at **decision** time and
`is_open_position` excludes anything carrying one, so the graph stops tracking a position the
instant the monitor decides — sold or not. AMD was decided out on 2026-07-20, never sold, and
**no future run will ever look at it again**: 55 shares, ~$30k, stranded silently. The same call
books `pnl_cents` from the decision-time price, so AMD sits in the ledger as a **−$1,530.65
realized loss** while the position is **+$1,277 unrealized** — every reporter metric (profit
factor, expectancy) rests on fills that do not exist.

Buy-only execution then ratcheted the account to `regt_buying_power = 0`; nothing has ever been
freed by a sale.

## Decision

### 1 · A position is closed by a fill, not by a decision

`CloseDecision` records intent only. **Execution** writes the `CLOSES` edge when the sell fill
lands, and realized `pnl_cents` is computed at **fill** price, not decision price. The broker
position snapshot (DL-44 — broker is truth for holdings) is the independent backstop: a holding
the broker no longer reports is closed regardless of our records.

The two readings are deliberately redundant and disagree only when something is wrong, which is
when a second opinion is worth having.

**Consequence, intended:** a close that fails to execute is simply **re-decided next run**.
Retry is default behaviour rather than a feature. AMD would have exited itself on 07-21.

### 2 · The idempotency key derives from the position, not the run

`order_from_close` currently keys on `f"{close_set.run_id}:{ticker}:sell:{position_id}"`, where
`run_id` is the **monitor run** — new every night. Combined with re-decide-until-filled, that key
would place a **fresh sell every night** and oversell the book. A whole-position exit happens
once, so the key is `f"close:{position_id}"`. `CloseDecision`'s node key
(`{monitor_run_id}:{position_id}:close`) carries the same flaw and is keyed on the position for
the same reason.

*This is the single most dangerous detail in the change: the naive fix multiplies sells.*

### 3 · The broker enforces stops and targets

Stops move out of our once-daily loop onto the exchange, where they are enforced continuously.
Verified against Alpaca's order documentation:

| Case | Order class | Notes |
| --- | --- | --- |
| New entry | `bracket` | entry + take-profit + stop-loss in one submission; legs activate when the entry fills |
| Already-held position | `oco` | exit-only pair, explicitly for positions whose entry already filled |

Constraints (documented, must be honoured): `time_in_force` must be `day` or `gtc`; **extended
hours are not supported**; fractional shares are not supported (we trade whole shares); OCO legs
are limit-typed; all apply DNR/DNC automatically.

The `Position` nodes already carry `stop_pct: 0.05` and `target_pct: 0.10`, which map directly
onto the two legs. The **9 existing positions** get `oco` exits attached retroactively — they
are not left to the daily loop.

The monitor keeps **time**, **regime** and **manual** exits, which are policy judgements no
exchange can make. It no longer owns stop and target execution.

### 4 · A refused sell retries a bounded number of runs, then escalates

Default **3** runs. Then an `Escalation` node and stop. Retry-forever on a refusal is the exact
shape of the failure this ADR exists to end; escalate-on-first wakes the operator for transient
broker states.

### 5 · A partial fill reduces the position; it does not create a new one

The remainder keeps its original stop, target, horizon and lineage back to the entry decision,
and the exit re-attempts for the outstanding quantity next run.

## Consequences

- The monitor's charter narrows: it decides *whether* to exit on time/regime, not *how* stops
  execute. `docs/laws/` for monitor and execution need updating to match.
- Exit lineage becomes two-legged — a decision node and the fill that satisfied it — which the
  reporter must read for realized PnL.
- Realized-PnL history is currently **wrong** wherever a decision-time `pnl_cents` was booked
  without a fill. It must be recomputed or invalidated, not carried forward.
- Bracket/OCO submission happens outside regular hours (runs fire 22:30 UTC, after the US
  close). Queuing for the next open is expected, but **this needs a live probe before the
  implementation is trusted** — it is the one assumption here not yet proven against the API.
- AMD self-heals under §1 once closure is fill-keyed; no manual trade.

## Alternatives rejected

- **A `close_state` field (`decided`/`submitted`/`filled`) on CloseDecision** — a third
  bookkeeping of a fact the broker already answers, and one more thing to keep consistent.
- **An intraday exit-only KEDA window** — still polling, so it narrows the gap rather than
  closing it, and adds market-hours compute and provider calls. Broker-native stops remove the
  gap outright.
- **Accepting once-daily exits unchanged** — defensible at a 14-day horizon, but it makes every
  stop a next-open market order with no recourse on a gap-down.
- **Monitor calling execution over the bus from the poll path** — reintroduces a synchronous
  dependency into a graph-pull cascade (DL-08), and the swallowed RPC is what hid this for a
  month.
- **Marking AMD closed in the graph to clear its divergence flag** — DL-44: never edit the graph
  to agree with a story. The flag is correct; the position is real.
- **Flattening the account to re-zero** — destroys the accumulating dataset (DL-44).
- **Wiring the dispatch before settling the lifecycle** — a working dispatch on decision-time
  closure strands a position on every delivery failure; it would strand them faster.


---

## What actually shipped (amendment, 2026-07-24)

The governing decision held: **a position is closed by evidence, not by our own decision.** It is
live and proven — run `check-s138-unstrand` restored four positions that had been invisible since
07-20, and closed ABT only once the broker stopped reporting it. What changed is the *mechanism*.

### §1 — closure is broker-snapshot evidence, not an execution-written `CLOSES` edge

**Written:** "**Execution** writes the `CLOSES` edge when the sell fill lands."
**Shipped (0.74.02):** nothing writes a `CLOSES` edge on fill. `contracts/positions.py` simply
stopped treating a `CloseDecision` as closing anything; a position is active until broker
reconciliation marks it `broker_absent` / `broker_superseded_by`
(`agents/monitor/reconcile.py`), which already existed per DL-44.

**Why the simpler mechanism won.** The prescribed design needed a *second* closure authority
(execution) alongside the one that already worked (reconciliation). Two authorities is how the
original defect arose. One rule, sourced from the broker, cannot disagree with itself.

`CloseDecision` is now pure lineage: it records that an exit was decided and never removes a
position from the book.

### §1 — realized PnL at fill time is **not yet implemented**

**Written:** "realized `pnl_cents` is computed at **fill** price, not decision price."
**Shipped (0.74.03):** the monitor stopped writing `pnl_cents` altogether, and
`scripts/repair_close_pnl.py` marked the seven historical fabricated entries with
`pnl_invalidated_at` (appending, never rewriting — see below). **Nothing yet computes PnL at
fill time.** `realized_pnl_cents()` is retained and unit-tested for that purpose.

This was deliberate sequencing: at the time there had never been a filled sell, so a
fill-time derivation had no real data to be tested against. **That blocker is now gone** —
`ABT 98 @ $101.35` filled on 2026-07-23 — so the derivation is unblocked and outstanding.

### §2 — a position-keyed `CloseDecision` is **not representable**

**Written:** key the node on the position so re-decisions merge into one node "(keep `run_id` in
the props so the latest deciding run is still visible)".
**Reality:** `kernel/graph_support.py` is **append-only at the property level** — merging a node
with a *different* value for an existing property raises
`ValueError: property 'run_id' cannot be overwritten`. A single node carrying a changing
`run_id` cannot exist. The clause prescribes something unbuildable.

**Shipped:** the `CloseDecision` key stays **monitor-run scoped**. Under evidence-based closure
the same exit is legitimately re-decided every run, and in an append-only store each decision is
its own immutable fact rather than a mutation of the last one.

**The general rule this exposes, which binds every future design here:** *this graph records
facts, it does not hold mutable records.* "Update X to reflect the latest Y" is not expressible;
append a new fact, or append a marker that supersedes an old one. The PnL repair follows the same
shape — it **appends** `pnl_invalidated_at` and leaves the wrong `pnl_cents` visible, which is
also the better audit trail.

§2's *purpose* — preventing repeated broker orders for one exit — was met a different way, in
0.74.01: `order_from_intent` keys sells on `f"exit:{position_ref}:{ticker}:sell"`, a digest of the
open `Position` node keys. Note `order_from_close` still carries the original run-scoped key; it
is harmless only because those closes reach no broker (DL-60), and it must be fixed if that path
is ever wired.

### §3 — broker-native stops are still **not built**

`bracket` at entry and `oco` for held positions remain designed-only. Until they exist, no stop is
broker-enforced, and ADR-0016 §5's "the monitor narrows to a safety net **of broker-enforced
stop/target**" describes an end state rather than the current system.

### The consequence nobody predicted

With closure no longer stranding positions, the monitor's stop/target/time closes are
**re-decided every single run, forever**, because they reach no broker (DL-60) — while the
analyst, scoring the same names on full evidence, returns `hold`. Two deciders, opposite answers,
and only one of them is wired to the broker.

**Which decider wins is not settled by this ADR or by ADR-0016.** It is the open question this
work surfaced, and it needs an operator decision before either exit path is wired further.
