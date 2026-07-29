---
type: Architecture Decision
status: accepted
closes: "How long is a trading decision valid? What happens to an order that does not fill in the session it was decided for — does it carry to the next open, or is it dropped?"
tags: [execution, exits, entries, orders, slippage, stops, alpaca, decisions, adr-0015, adr-0017]
---

# ADR 0018 — A decision is valid for one session: fill it or drop it

**Status:** Accepted · **Date:** 2026-07-29 · **Decider:** Yury Gurevich (product owner)

## Context

The daily run fires at **22:30 UTC**, after the US close (13:30–20:00 UTC). It scores a complete
daily bar, decides, and submits **market** orders. Those orders cannot fill that session, so they
queue and execute at the **next open — roughly 15 hours later, at a price nobody decided on.**

That gap has now cost real money twice:

| Exit | Decided at | Filled at | Realized | Gap component |
| --- | --- | --- | --- | --- |
| MRVL (forced stop, 07-27) | — | `$195.98` | **−$1,330.12** | overnight |
| AMD (discretionary sell, 07-28) | `est $494.90` | `$467.35` | **−$3,515.60** | **≈ −$1,515** |

Two data points are not a trend, but the mechanism is structural rather than unlucky: **every
decision the system makes is executed at a price the decider never saw.** DL-62 named this exposure
when broker-native stops were designed; ADR-0015 §3 addressed it for *risk*, and left *alpha*
untouched.

There is a second, less obvious cost. An unfilled order does not merely wait — it **persists as
live broker state and interferes**:

- `ABT buy 95` sat `accepted` for a full day; that stale opposite-side order is exactly what made
  Alpaca refuse ABT's protective stop as a **wash trade** (`code 40310000`) for two days, leaving
  96 shares with no floor (S146, DRIFT-024's trigger).
- The same class of stale order produced the orphaned fills that S145 and S146 both had to build
  adoption and repair machinery for.

So carrying decisions across sessions is not only a pricing problem. It is a **safety and
complexity** problem.

## Decision

**A trading decision is valid only for the session it was made for.**

1. Orders are submitted with a **bounded price tolerance** around the decision price, not as
   unconditional market orders. The tolerance is a `kernel.tunable(..., why=...)` with declared
   bounds, not a literal.
2. Any order **not filled by the end of that session is cancelled**, and the decision is
   **dropped**. It is never carried into a later session, and never left resting.
3. A dropped decision is **recorded and visible** — a `Fault` naming the ticker, the decided price,
   and the reason (outside tolerance / unfilled at session end). Silence is forbidden (DL-57: intent
   is not outcome).
4. Tomorrow's run re-decides from tomorrow's evidence. A decision that did not execute is not
   a debt to be settled later; it is simply gone.

**This applies to entries and to discretionary exits alike.** The operator's ruling, 2026-07-29:
*"Drop it if it is not filled."*

### The one exemption

**Broker-native resting stops (ADR-0015 §3) are exempt.** A resting `gtc` sell stop is **not a
decision** — it is a standing risk instrument that lives at the broker between runs and fires
intraday on a price event. It is precisely the mechanism that makes dropping alpha decisions safe.
Cancelling stops at session end would remove the floor this ADR relies on.

The distinction is the ADR-0017 line: **alpha proposes, risk disposes.** Alpha decisions expire.
Risk instruments persist.

## Consequences

**Accepted, eyes open:**

- **Some decisions will not execute.** On a gapping open, the system does nothing rather than
  transacting at a price it never evaluated. That is the point.
- **ADR-0017's forced daily-rail stop becomes best-effort within tolerance.** When a stop is
  breached and the analyst forces a sell onto the daily rail, that sell is now droppable. If it
  does not fill, the position stays held for another session. **This is only safe because the
  resting broker stop is the real floor** — which makes S146's audit check `A2` (every held
  position carries a live stop at the right quantity) load-bearing rather than nice-to-have. A
  position with no broker stop **and** a dropped forced exit has no protection at all that day.
- **Fill rates drop; measurement changes.** Approval count and execution count diverge, and the
  reporter's metrics must not read a dropped decision as a rejection or a loss.

**Gained:**

- No decision executes at an unevaluated price.
- **Stale live orders stop existing**, which removes the wash-trade stop blocker, the orphaned-fill
  class, and much of the adopt-vs-fabricate complexity built in S145/S146.
- Idempotency gets simpler: an order keyed to a session that has ended cannot be replayed into a
  later one.

## Alternatives ruled out

- **Move the run inside the session so orders fill same-day.** Directly satisfies "filled during the
  run", and was the operator's first framing. Rejected because the analyst's 15 deterministic
  pillars are computed on **completed daily bars**; running intraday means scoring an unclosed bar
  and degrading every signal to buy execution certainty. Trading signal quality for fill timing is
  the wrong side of that exchange.
- **Keep market orders, accept the gap.** The status quo. Rejected: measured at ≈ −$2,850 over two
  exits, with no mechanism that improves it over time.
- **Carry orders GTC until filled.** Worst of both — it maximises the window in which a stale order
  can block a protective stop, and lets a decision execute days after the evidence that produced it
  expired.
- **Re-validate at the open instead of dropping.** A second decision point at the open, using
  opening prices. Rejected as scope: it needs an intraday decision path that does not exist, and it
  reintroduces "decide now, execute later" one layer up. Reconsider only if drop rates prove
  unacceptably high.

## Open, deliberately

The **tolerance width** is not fixed here. It is a tunable with bounds, and its value is an
experiment (ADR-0013): too tight and nothing trades, too wide and the ADR buys nothing. Start
conservative, measure the drop rate against realized slippage, and move it on evidence — not by
argument.
