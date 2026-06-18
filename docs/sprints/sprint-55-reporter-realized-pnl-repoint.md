<!-- Agent: planning | Role: sprint handover -->
# Sprint 55 — Reporter re-point to real $ PnL (closes P11)

**Status:** ✅ shipped (2026-06-18, branch `sprint-55-reporter-realized-pnl-repoint`) · **Build phase:** P11 (final slice) · **Effort: S** · executed directly (no coding agent this cycle)

> **Handback (shipped).** Re-points the reporter's trade-outcome metrics from S41's trigger-derived
> **percentage approximation** to the **real realized `pnl_cents`** the monitor records on every
> `CloseDecision` (S43). `collect_trade_outcomes` now takes **only** `close_decisions`, reads each
> close's `pnl_cents` (skipping any with none — legacy nodes or holds), and computes dollar-based
> `profit_factor` (gross wins ÷ gross losses by **sign**) and **`expectancy_cents`** (mean realized
> PnL) across **all** triggers — **including time exits**, which the % approximation had to drop. The
> `_implied_pnl_pct`/`_pct` trigger derivation and the Position↔CloseDecision pairing are gone (the
> PnL lives directly on the close node). `result.py` call sites updated (one arg). **Key rename:**
> `expectancy_pct → expectancy_cents` (unit changed; `portfolio_metrics` is a free-form dict → no
> contract change). `feat` → **project version `0.3.0 → 0.4.0`** (MINOR, HARD RULE). `make ci` green:
> **735 passed, 4 skipped, 100.00% coverage**; every module < 200L. **P11 (deterministic-logic depth)
> is now complete.**

## Goal

Replace the S41 stop/target-only percentage metrics with dollar-based profit-factor and expectancy
computed from the monitor's realized `pnl_cents` (S43), so the reporter reflects **actual** realized
outcomes across every exit trigger.

## Parts (all shipped)

- **`agents/reporter/domain/trade_outcomes.py`** — rewritten: `collect_trade_outcomes(close_decisions)`
  reads `pnl_cents` per close (pure `_pnl_cents` guards non-int/None), buckets by sign, returns
  `profit_factor` / `expectancy_cents` / `closed_trades_with_pnl`. Zero-denominator/empty sentinel
  preserved (`0.0`). Never raises.
- **`agents/reporter/result.py`** — `build_snapshot` and `degraded_snapshot` call
  `collect_trade_outcomes(lineage.close_decisions)` / `collect_trade_outcomes(())` (positions arg
  dropped).
- **Tests** — `test_trade_outcomes.py` rewritten for the $-based behaviour (incl. a **time-exit now
  contributes** case and a break-even case); `test_reporter_agent.py` fixture seeds `pnl_cents` on the
  close decisions and asserts `expectancy_cents`.
- **`pyproject.toml`** — version `0.3.0 → 0.4.0`.

## Acceptance criteria (met)

- Metrics derive from real `pnl_cents` off close-decision nodes, across stop/target/**time**; a close
  with no pnl is skipped; never raises. No contract change; `make ci` green at floor 100.00; modules
  < 200L.

## Out of scope

- Short positions; fees/slippage; per-ticker PnL attribution; surfacing `expectancy_cents` in the CLI
  render (the metric rides in `portfolio_metrics`, already queryable).
