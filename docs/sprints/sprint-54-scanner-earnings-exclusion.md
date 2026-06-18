<!-- Agent: planning | Role: sprint handover -->
# Sprint 54 — Scanner earnings-window exclusion (P11, consumes the S42 feed)

**Status:** ✅ shipped (2026-06-18, branch `sprint-54-scanner-earnings-exclusion`) · **Build phase:** P11 · **Effort: S** · executed directly (no coding agent this cycle)

> **Handback (shipped).** The consumer half of the earnings two-sprint pair (S42 = provider feed).
> The scanner now requests the `"earnings_calendar"` field and **drops candidates whose next earnings
> date is within `earnings_exclusion_days` (5) of the scan as-of**. Pure `_days_to_earnings` (whole
> days to the next report; `None` when unknown or already past) + a gate appended **after** the beta
> cap in `apply_filters`; `_survivor` records `days_to_earnings` in metrics and `earnings_window` in
> `survived_filters` **only when earnings data is present** — exactly mirroring the beta cap, so the
> gate is **additive + dormant**: with no earnings data (`MarketData.earnings == {}`) nothing changes
> and every existing scanner + pipeline test stayed green. `request_market_data` now asks for
> `("ohlcv", "earnings_calendar")`; the agent captures the window once and threads `market.earnings` +
> `window.end` into `apply_filters`. **No contract change** (Candidate already carries `metrics`); **no
> boundary-map change**; provider already serves the field (S42). `feat` → **version `0.1.0 → 0.2.0`**
> (MINOR bump, the project's HARD RULE). `make ci` green: **733 passed, 4 skipped, 100.00% coverage**;
> every module < 200L (filters 127, agent 170, settings 74).

## Goal

Close the named P11 scanner item "earnings-window exclusion." An earnings date is market reference
data, so it arrives from the provider (`MarketData.earnings`, shipped S42), and the scanner applies
the **deterministic event-risk gate**: a name reporting earnings in the next few days carries gap
risk the deterministic scan should sidestep before the analyst spends work on it.

## Parts (all shipped)

- **`settings.py`** — `earnings_exclusion_days` tunable (5, ge 0 le 60, unit days).
- **`domain/filters.py`** — `apply_filters` gains `earnings: dict[str, date]` + `as_of: date`; new pure
  `_days_to_earnings(ticker, earnings, as_of) -> int | None` (`None` when unknown or past); gate runs
  after the beta cap (`drops["earnings_window"]`); `_survivor` gains `days_to_earnings` and records the
  metric + `earnings_window` survived-filter only when present (dormant otherwise).
- **`provider_client.py`** — `request_market_data` requests `("ohlcv", "earnings_calendar")`.
- **`agent.py`** — compute the window once; pass `market.earnings` + `window.end`; explanations mention
  the earnings filter.
- **Tests** — `test_scanner_earnings.py` (6 filter-branch cases: within-window drop, boundary drop,
  beyond-window keep+metric, no-data dormant, past-date no-exclude, `_days_to_earnings` unit; + 1
  agent end-to-end over the bus). `test_scanner_beta.py` updated for the new `apply_filters` arity.
- **`pyproject.toml`** — `version 0.1.0 → 0.2.0` (feat → MINOR, HARD RULE).

## Acceptance criteria (met)

- The scanner drops candidates with earnings within `earnings_exclusion_days` of the scan as-of,
  attributing `earnings_window` in the filter trace; survivors with known earnings carry a
  `days_to_earnings` metric; missing earnings → gate dormant (no re-pin).
- No contract / boundary change; provider serves the field (S42). `make ci` green at floor 100.00;
  every module < 200L.

## Out of scope

- A **live earnings probe** (DEP-FEED) — optional follow-up.
- Using the earnings date anywhere downstream of the scanner (analyst/PM) — not requested.
