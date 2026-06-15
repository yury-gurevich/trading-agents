<!-- Agent: planning | Role: sprint handover -->
# Sprint 40 — Portfolio manager reward/risk gate (P11)

**Status:** shipped · **Branch:** `sprint-40-pm-reward-risk` · **Build phase:** P11 · **Effort: S**

> Implemented directly by the planning agent ("plan next sprint and when happy code it"). Green at the
> full gate; 595 tests, floor 100.00.

## Goal

Add the reference **reward-to-risk gate** to the portfolio manager: reject any order whose reward is
not at least `min_reward_risk_ratio` times its risk. v1 worked in absolute prices
(`risk = entry − SL`, `reward = TP − entry`); v2 carries **percentages** (`stop_pct`, `target_pct`),
so the ratio reduces exactly to `target_pct / stop_pct` (the entry price cancels) — no entry price
needed.

## What shipped

- New PM tunable `min_reward_risk_ratio` (default **1.5**, `ge=0.0 le=10.0`; `0` disables). The default
  passes the regime default setup (`base_take_profit 0.10 / base_stop 0.05 = 2.0`), so no existing
  approved order re-pinned.
- `agents/portfolio_manager/domain/risk.py`:
  - `_effective_pcts(item, default_stop_pct, default_target_pct)` — extracted the stop/target
    derivation (recommendation's suggested values, else the regime defaults) so the gate and the
    order intent share one source of truth.
  - `_reward_risk_rejection(item, stop_pct, target_pct, min_ratio)` — rejects `invalid_stop_loss`
    when `stop_pct ≤ 0` (ratio undefined; `suggested_stop_pct` is contractually `ge=0.0`, so 0 is
    reachable) and `reward_risk_below_min` when `target_pct / stop_pct < min_ratio`.
  - `evaluate_recommendations` gained a `min_reward_risk_ratio` kwarg and runs the gate after the
    sizing/cash/position checks, before building the order intent; `_order_intent` now takes the
    effective pcts directly.
- `agent.py` passes `self._settings.min_reward_risk_ratio` through.

## Decision — one test re-pinned (deliberate)

`test_order_intent_preserves_deliberate_zero_stop_and_target` previously **approved** a `0.0 / 0.0`
stop/target (proving suggested values override defaults). A 0 % stop means no downside bound, so
reward/risk is undefined — the gate now **rejects** it (`invalid_stop_loss`). The test was retargeted
to a valid explicit policy (`0.04 / 0.12`, ratio 3.0) and renamed
`test_order_intent_preserves_deliberate_stop_and_target` — it still proves explicit values are
preserved, not overridden. New `test_reward_risk.py` covers the two rejection branches and the pass
branch. The two direct `evaluate_recommendations` test call sites gained the new kwarg.

## Acceptance

- Orders with `target_pct / stop_pct < min_reward_risk_ratio` → `reward_risk_below_min`; `stop_pct ≤ 0`
  → `invalid_stop_loss`; otherwise approved. **No contract change** (PM 0.x unchanged); no new
  dependency. 595 tests, floor 100.00; full gate green; every module < 200L.

## Out of scope

- **Sector-concentration cap** and explicit `compute_portfolio_value` / cash-ledger — they need a
  `sector` field on positions/recommendations (provider sector data + contract changes), a larger
  separate sprint. Scanner beta + earnings and reporter profit-factor/expectancy remain the other P11
  gaps. Spec: memory `v1-deterministic-port-gaps.md`.
