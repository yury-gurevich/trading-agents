# Sprint 87 — Staleness gate counts trading sessions, not calendar days (DL-10)

**Phase:** P15 / trading-pack correctness
**Branch:** `sprint-87-staleness-trading-sessions`
**Status:** shipped (0.23.04)

---

## Goal

Fix the bug that made the first live Aura run produce **zero trades**. The provider's staleness gate
(`integrity._stale_tickers`) measured **calendar days** while its own intent was **trading sessions**:
Jun-18 data on Jun-22 read as 4 calendar days > `max_staleness_days(3)` and the whole batch was flagged
degraded — so the analyst rejected every candidate before scoring. But Jun-19 was Juneteenth and Jun-20/21
the weekend, so Jun-18 was the freshest data that could exist (1 trading session old). DL-10.

## What shipped

- **`agents/provider/domain/market_calendar.py`** — `trading_sessions_between(after, through)` counts
  NYSE sessions in `(after, through]` (weekends + a static NYSE holiday set excluded), plus
  `is_trading_session(day)`. Dependency-free; holidays cover 2024–2027 (observed dates), documented with
  the market-calendar-library upgrade path.
- **`integrity._stale_tickers`** now flags a ticker when `trading_sessions_between(latest_bar, end) >
  max_staleness_days` — sessions, not `(end - latest).days`.
- **`ProviderSettings.max_staleness_days`** `why` clarified (trading sessions, weekend+holiday aware;
  unit `sessions`).

## Design decision (DL-10 option b)

Counted **trading sessions via a static NYSE holiday set + weekend exclusion**, not a market-calendar
library (option a). Dependency-free, deterministic, testable; fixes the Juneteenth case exactly. A date
past the holiday window falls back to weekday counting (slightly conservative). Swap in
`exchange_calendars` / `pandas-market-calendars` when the window needs extending or per-exchange precision.

## Proof

`test_market_calendar.py`: every holiday is a weekday (catches data-entry errors); weekend + Juneteenth
excluded; **Jun-18 → Jun-22 2026 = 1 session** (was 4 calendar days); fresh-across-holiday-weekend data is
**not** flagged stale. The existing `test_domain` stale case (Jan-1 data on Jan-10 = 6 sessions > 2) still
flags. A `test_batch_trace` degraded case was re-aged to ~24 calendar days (> 7 sessions) to stay stale.

## Exit criteria

- [x] Staleness measured in trading sessions; weekend/holiday does not flag current data.
- [x] The live-run failure case (Jun-18 on Jun-22) is no longer stale; a genuinely old bar still is.
- [x] `make ci` green; 100 % coverage; modules ≤ 200 lines; import-linter unchanged.

## Version bump

Bug fix → **PATCH** (last two digits). 0.23.03 → 0.23.04.

## Follow-on

DL-09 (filter decisions as a labeled training source) now has real signal to collect: with the staleness
gate fixed, the analyst scores, the PM sizes, and trades actually flow on live data.
