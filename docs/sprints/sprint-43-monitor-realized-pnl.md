<!-- Agent: planning | Role: sprint handover -->
# Sprint 43 — Monitor: realized PnL on close (accuracy upgrade for reporter metrics)

**Status:** queued · **Branch:** `sprint-43-monitor-realized-pnl` · **Build phase:** P11 · **Effort: S–M**

> **DO NOT START until Sprint 41 (reporter profit-factor/expectancy) is shipped and merged.** This
> sprint is the *accuracy upgrade* to the metrics S41 ships, decided 2026-06-16: S41 derives PnL from
> the trigger (stop → `−stop_pct`, target → `+target_pct`, **time exits excluded**, percent-based).
> This sprint records the **actual** realized PnL at close so a follow-up can re-point the reporter to
> dollar-based metrics that include **every** trigger.

## Goal

When the monitor closes a position, compute its **realized PnL in integer cents** and record it on the
`CloseDecision` (contract field + graph node): `pnl_cents = (exit_price_cents − entry_price_cents) ×
quantity` (long-only, gross). This is the foundational "realized outcome" record the build-plan's
*decision-evidence & calibration* workstream calls for, and it lets the reporter replace S41's
trigger-derived `%` approximation with **actual dollar PnL across stop, target, and time exits**.

**Why the monitor and not the reporter:** v2 carries no realized PnL anywhere — `CloseDecision` has only
`ticker/position_id/decision/trigger/rationale`. S41 worked around that by inferring PnL from the
trigger + stop/target pcts (so it must drop time exits and assume exit-at-threshold). The monitor owns
the close and already has every input at the close branch, so the real PnL is computed here.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/sprints/sprint-41-reporter-trade-outcomes.md` (the
  %-based metrics this upgrades — note its time-exit exclusion and `closed_trades_with_pnl` counter).
  Monitor-only plus one additive contract field — keep to the one-agent rule.
- **Shipped code you extend (read it):**
  - `contracts/monitor.py` — `CloseDecision` (line ~22). Add `pnl_cents: int | None = None`. Bump
    `CONTRACT.version` `0.1.0 → 0.2.0`; `owns_graph` is **unchanged** (`CloseDecision` already owned).
  - `agents/monitor/agent.py::_evaluate_positions` — the close loop already has every input at the
    close branch: `current_price_cents` (exit), `position.props["opened_price_cents"]` (entry),
    `position.props["quantity"]` (shares). Compute PnL for **close** decisions only; set it on the
    `CloseDecision` and pass to `write_close_decision`. Holds carry `pnl_cents=None`.
  - `agents/monitor/domain/exit_rules.py` — add the pure PnL helper here (integer-cents idiom,
    alongside `check_stop`/`check_target`; `PCT_SCALE` lives here).
  - `agents/monitor/store.py::write_close_decision` — add `pnl_cents` to the merged node props.

### The rule (port this)

`realized_pnl_cents(exit_price_cents: int, entry_price_cents: int, quantity: int) -> int`:

- Return `(exit_price_cents − entry_price_cents) * quantity`. **Pure integer arithmetic — no float**
  (money is never a float here). Long-only: positive above entry, negative below, zero at break-even.
  Gross — no fees/slippage (v1 parity). Never raises.

## Part A — Contract

`contracts/monitor.py`: add `pnl_cents: int | None = None` to `CloseDecision`; bump `version` to
`0.2.0`. Run the boundary meta-test — `owns_graph` unchanged, so single-writer parity holds.

## Part B — Domain

`agents/monitor/domain/exit_rules.py`: add `realized_pnl_cents` exactly as specified.

## Part C — Agent wiring

`agents/monitor/agent.py::_evaluate_positions`: in the `if decision == "close":` branch, compute
`pnl = realized_pnl_cents(current_price_cents, int(position.props["opened_price_cents"]),
int(position.props["quantity"]))`. Set `pnl_cents=pnl` on the `CloseDecision` for that position (holds
keep the `None` default) and pass `pnl_cents=pnl` into `write_close_decision`.

## Part D — Store

`agents/monitor/store.py::write_close_decision`: accept a `pnl_cents: int` parameter and add
`"pnl_cents": pnl_cents` to the node props.

## Part E — Tests

- `agents/monitor/tests/test_realized_pnl.py` (≤ 80L): `realized_pnl_cents` win / loss / break-even /
  multi-share quantity (hand-computed); never raises.
- Agent + store: a close decision → `CloseDecision.pnl_cents` equals the hand-computed value and the
  persisted node has the `pnl_cents` prop; a hold → `pnl_cents is None`.
- Pipeline regression: the P3 monitor + reporter slices assert `(decision, trigger)` tuples — adding
  `pnl_cents` is **additive**, so they stay green; add a `pnl_cents` assertion where natural (the AAPL
  stop: entry 11600c, exit 10000c, sized quantity → negative). Run the whole suite.

## Steps

1. Branch off `main` **after S41 reporter is merged**. **A** contract → **B** helper (+ test) →
   **C** agent → **D** store. `make ci`. Add the agent/store/pipeline tests; full-suite green at floor.
   `wc -l agents/monitor/*.py agents/monitor/domain/*.py` (agent.py ~198 — extract the close-decision
   construction into a helper if the branch pushes it over 200). Push; hand back.

## Acceptance criteria

- `realized_pnl_cents` is exact integer cents (hand-verified); never raises.
- Every **close** `CloseDecision` carries `pnl_cents` (contract field **and** node prop); holds carry
  `None`. Contract bumped to **0.2.0**, `owns_graph` untouched; boundary meta-test green.
- `make ci` green at/above floor; existing `(decision, trigger)` slice assertions unchanged.

## Out of scope (the follow-up after this)

- **Reporter re-point** — once `pnl_cents` exists, update `domain/trade_outcomes.py` (from S41) to read
  the **real** `pnl_cents` off close-decision nodes: profit-factor/expectancy in **dollars** over
  **all** triggers (stop, target, **and time**), replacing the trigger-derived `%` approximation and its
  time-exit exclusion. A `None` pnl (legacy/holds) is skipped. Separate sprint.
- Short positions; fees/slippage; enriching the `Position` node with a closed/realized-PnL status. Any
  change outside the monitor package + the one `CloseDecision` field.

The planning agent reviews and merges, then writes the reporter re-point sprint against this field.
