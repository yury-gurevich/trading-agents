---
type: Architecture Decision
status: accepted
closes: "Are buy and sell decided together on the same evidence, or by separate mechanisms? How does a sell reach execution?"
tags: [exits, analyst, portfolio-manager, execution, monitor, decisions, dl-60, adr-0015]
amends: ADR-0015
---

# ADR 0016 — One run, one evidence set, both directions

**Status:** Accepted · **Date:** 2026-07-23 · **Decider:** Yury Gurevich (product owner)

## Context

Entries and exits are currently decided by two different systems on two different bodies of
evidence. A **buy** passes the provider's full fact set (OHLCV, fundamentals, news, sentiment,
regime), the analyst's scoring against a regime confidence floor, the PM's risk and
concentration gates, and an LLM challenger-veto. A **sell** is decided by three hardcoded
numbers on the `Position` node — `stop_pct: 0.05`, `target_pct: 0.10`, `horizon_days: 14` —
evaluated by the monitor with prices only, and with no analyst, no PM, and no debate.

The consequence is visible in the book. The same names were re-recommended and re-bought nightly
with nothing ever trimmed:

```
BAC   171 -> 338 -> 503 shares
USB   160 -> 320 -> 478
WFC   116 -> 233 -> 348
```

until `regt_buying_power` reached **0** and every subsequent order was rejected. A four-name
accumulator is not a portfolio, and no amount of exit *plumbing* fixes a system that never
reconsiders what it holds.

DL-60 established that no graph-pull path carries a close decision to execution at all.
ADR-0015 settled the exit *lifecycle* (closed by a fill, broker-enforced stops, bounded retry,
partial-fill semantics) and implied a second, parallel mechanism would be built for delivery:
execution polling `CloseDecision` nodes.

**That second mechanism is unnecessary.** `contracts/common.py` already defines
`Action = Literal["buy", "sell", "hold"]`, `OrderIntent` already carries an `action`, and
`agents/execution/domain/orders.py::_broker_side` already maps a `sell` intent onto a broker
sell order. The rail that carries sells is the rail that already carries buys — proven nightly,
idempotent, reconciled, and covered by the DL-59 acceptance gate.

## Decision

**Buy and sell are decided in the same run, from the same evidence, by the same agents.**

1. **The analyst scores the union of scanner survivors and currently-held tickers.** Held names
   **bypass the scanner** — its filters (`min_average_volume`, `min_relative_strength`,
   `earnings_window`) are entry-selection criteria and are not reasons to hold or exit. Both sets
   are scored against the same `MarketData` snapshot and the same regime in the same cycle.

2. **The analyst emits `buy` / `sell` / `hold` per name** with its confidence and rationale, on
   identical evidence. An exit is a thesis, stated and explained, not a counter reaching zero.

3. **The PM decides both directions in one `OrderIntentSet`** — sizing entries as it does today,
   and sizing exits (full or partial). Its concentration book is already position-aware
   (`concentration.py` seeds held tickers), and its risk gates apply to both directions.

4. **Execution submits both sides on the existing rail.** No new close-dispatch mechanism, no
   new poll source, no second idempotency scheme. DL-60's missing consumer becomes moot rather
   than built.

5. **The monitor narrows to a safety net**: broker-enforced stop/target (ADR-0015 §3 — **not built as of 2026-07-24; nothing is broker-enforced yet**), time and
   regime exits, position bookkeeping, and broker reconciliation. It is no longer the primary
   author of exit decisions. **Narrowed further by [ADR-0017](0017-exit-authority-alpha-proposes-risk-disposes.md) (2026-07-24):** the monitor stops
   authoring exit decisions entirely — the analyst owns discretionary exits and a breached stop
   is forced onto this same rail; `target`/`time` retire into deferred strategy; the monitor
   keeps reconciliation and raises a `Fault` when a stop is breached but not yet exited.

### Foundation now, strategy later

This ADR is explicitly **plumbing, not strategy**. The exit *rule* stays deliberately minimal
and conservative at first — a tunable exit-confidence floor, defaulted low enough that it does
not churn a book that has never sold anything. Building genuine exit models (trailing logic,
time-in-trade, MAE/MFE, trim policy, champion–challenger against the mechanical rules) is
sequenced **after** this foundation exists, because until both directions flow through one
evidence path there is nowhere for that work to live.

The asymmetry that **stays**: a stop is a risk control, not an opinion. It remains unconditional
and exchange-enforced (ADR-0015). Deliberation belongs in front of conviction exits, never in
front of a stop.

## Consequences

- **The conservation invariant changes.** `_conserves("analyst", "scored", "scanner",
  "survived")` in `trading_boundaries.py` is now false by construction: the analyst legitimately
  scores more names than the scanner passed. The bound becomes
  `analyst.scored <= scanner.survived + held_count`, and the held count must be observable on
  the analyst stage view. **Missing this turns every run FAIL.**
- Held names now consume analyst and deliberation budget every night — LLM spend scales with
  positions held, not just candidates.
- The reporter's "positions opened / closed" becomes meaningful for the first time, since sells
  will actually reach the broker.
- Exit lineage flows through `OrderIntent` → `Fill` like any buy, which satisfies ADR-0015's
  fill-keyed closure without a bespoke edge: the position closes when its sell fills.
- `CloseDecision` remains for the monitor's safety-net exits (time/regime) and keeps ADR-0015's
  position-derived idempotency key.
- A name can be both held and re-recommended; the PM must not pyramid into it. Making the
  analyst's `hold` verdict explicit is what prevents the accumulator behaviour above.

## Alternatives rejected

- **Execution polls `CloseDecision` nodes (ADR-0015's implied delivery)** — builds a second
  order path with its own idempotency, reconciliation and acceptance semantics, all of which the
  buy rail already has and has proven in production. Two rails is how the sell side got left
  behind in the first place.
- **Keeping exits on hardcoded rules and only fixing delivery** — would have shipped a working
  dispatch for a decision made on three constants while entries get the full evidence set. It
  fixes the plumbing and preserves the actual defect.
- **Putting deliberation in front of stops** — converts a risk control into a slow opinion;
  ADR-0015 deliberately moved stops to the exchange to make them unconditional.
- **Building exit strategy now** — the operator's call: the foundation is not ready for it, and
  strategy without a unified evidence path has nowhere to attach.
