---
type: Architecture Decision
status: accepted
closes: "What closes a position — a decision or a fill? Who enforces the stop: our daily loop or the broker? What happens when a sell is refused or partially fills?"
tags: [exits, monitor, execution, alpaca, bracket, oco, stops, dl-58, dl-59, dl-60]
---

# ADR 0015 — A position is closed by a fill; the broker enforces the stop

**Status:** Accepted · **Date:** 2026-07-23 · **Decider:** Yury Gurevich (product owner)

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
