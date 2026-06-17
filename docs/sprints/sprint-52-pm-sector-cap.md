<!-- Agent: planning | Role: sprint handover -->
# Sprint 52 — Portfolio-manager sector-concentration cap (P11)

**Status:** in progress · **Branch:** `sprint-52-pm-sector-cap` · **Build phase:** P11 (decision-logic depth — the PM's second risk gate, twin of S40) · **Effort: M**

## Goal

Add the PM's **sector-concentration cap**: while approving sized orders, track per-sector deployed value and
**reject an order that would push its sector over `max_sector_pct` of portfolio value** (reason
`sector_concentration`). This completes the PM risk-gate pair S40 started (reward/risk) — and the
`max_positions` tunable literally says it bounds concentration *"before sector caps exist"*. It consumes the
**`MarketData.sectors`** feed shipped in S51.

**Additive + dormant on unknown sectors** (the beta-cap pattern): a ticker with no sector → the cap is
skipped for it. Existing PM + pipeline tests provide no sector fixture → `market.sectors == {}` → no sector
rejections → they stay green untouched.

## Why (context)

- Read: `docs/sprints/sprint-51-provider-sector-feed.md` (the `MarketData.sectors` this consumes);
  `agents/portfolio_manager/domain/risk.py::evaluate_recommendations` (the deterministic approve/reject loop
  the cap joins — mirror how `reserved_cash` is accumulated as orders are approved); the S40 reward/risk
  gate (`_reward_risk_rejection`) for the rejection-helper shape.
- Scope note: like `reserved_cash`, the cap governs **this run's batch** deployment against
  `portfolio.value` (the slice's empty-start paper portfolio). Folding in existing-position sector value is
  a later extension (needs live position state + their sectors) — note it, don't build it.

## Parts

- **A — `agents/portfolio_manager/settings.py`**: add `max_sector_pct: Decimal` tunable (default
  `Decimal("0.30")`, `why="Cap total deployment into any one sector as a fraction of portfolio value; 1.0
  disables."`, `ge 0 le 1`).
- **B — `agents/portfolio_manager/domain/risk.py`**: `evaluate_recommendations` gains **defaulted** kwargs
  `sectors: dict[str, str] | None = None` and `max_sector_pct: Decimal = Decimal("1")` (defaults keep the 3
  existing direct-caller tests untouched). Inside: `sectors_map = sectors or {}`; track
  `sector_deployed: dict[str, Decimal]`. After the reward/risk check passes, compute
  `cost = Decimal(quantity) * price.amount`, look up `sector = sectors_map.get(item.ticker)`, and call a new
  `_sector_rejection(item, sector, cost, sector_deployed, max_sector_pct, portfolio.value)` →
  `RejectedOrder(reason="sector_concentration")` when `sector is not None and deployed.get(sector,0) + cost >
  max_sector_pct * portfolio_value`, else `None` (None sector → skip). On approval: `reserved_cash += cost`
  and, when `sector is not None`, `sector_deployed[sector] = sector_deployed.get(sector,0) + cost`. (Order:
  precheck → size → cash/positions → reward/risk → **sector** → approve.)
- **C — `agents/portfolio_manager/agent.py`**: pass `sectors=market.sectors,
  max_sector_pct=self._settings.max_sector_pct` into `evaluate_recommendations`.
- **D — `agents/portfolio_manager/provider_client.py`**: request both fields —
  `DataRequest(..., fields=("ohlcv", "sectors"))` (a missing sector fixture returns `{}` with no
  degradation, so existing tests are unaffected).
- **E — `agents/portfolio_manager/tests/helpers.py`**: `wire_pm(..., sectors: dict[str, str] | None = None)`
  → `FakeDataSource(sectors=sectors)`.
- **F — `agent.py::_explain_decision`**: append a sector-cap clause (keep existing substrings so the
  explain test still matches).

## Part T — Tests (every branch; 100% floor holds)

- `test_sector_cap.py` (unit, direct `evaluate_recommendations`): given two same-sector buys whose combined
  cost exceeds `max_sector_pct * value`, the second is rejected `sector_concentration` and the first
  approved; a within-cap pair both approved; a ticker with **no sector** is approved even when it would
  breach (cap skipped); `max_sector_pct=Decimal("1")` approves regardless (disabled).
- Agent end-to-end: `wire_pm(source_bars=…, sectors={"AAPL":"Tech","MSFT":"Tech", …}, settings=…)` with a
  `max_sector_pct` low enough that the second same-sector order is rejected; assert the rejection reason and
  that the approved set respects the cap.
- Regression: existing PM unit + agent + pipeline tests are unchanged (no sector fixture → `{}` → dormant;
  the 3 direct `evaluate_recommendations` callers rely on the new defaults). Run the whole suite.

## Acceptance criteria

- The PM rejects orders that would breach `max_sector_pct` for their sector, attributed
  `sector_concentration`; unknown-sector orders are unaffected; the cap is deterministic and order-stable
  (recommendations processed in confidence order, as today).
- No contract change (`RejectedOrder.reason` is a free string; PM stays `0.1.0`); no boundary-map change.
  `make ci` green at floor 100.00; every module < 200L.

## Out of scope

- Folding **existing open positions'** sector value into the cap (needs live position state) — a later
  extension; note it.
- Scanner earnings-window exclusion / reporter profit-factor (other P11 items).

## Handback report (paste into PR / reply)

- Confirm no contract/boundary change; defaults kept the 3 direct `evaluate_recommendations` callers
  untouched; the cap is dormant without sector data. New/changed module line counts; coverage % + floor;
  total test count.
