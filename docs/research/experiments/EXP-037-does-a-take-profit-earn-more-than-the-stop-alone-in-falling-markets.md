# EXP-037 — Does a take-profit earn more than the stop alone in falling markets?

**Status:** PRE-REGISTERED 2026-10-27 (planner)
**Decision / origin:** the operator, 2026-10-27, on the caveat that EXP-022's window was mostly a
rising market: *"that wud be great if we run an experiment"*; [DL-320](../../design-log.md) ·
**Cost:** $0 (EXP-022's sealed arms, read on this laptop)

## 1. Why we needed this experiment

[EXP-022](EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md) (final 2026-10-27) found
every exit besides the stop behind it over 2017–2026: the take-profit by −10.90 pts a year
[−21.72, −0.89] at 25 bps. The book earns from a few long holds, and a take-profit sells them early.
That window is mostly a rising market, which rewards holding. In a falling market there are few long
winners to cut, and a take-profit banks the rallies, so the sign could turn. ADR-0033 keeps the stop
alone until an experiment shows otherwise; this asks whether falling markets are that case.

A stock-level test of 2000–02 and 2007–09 was ruled out (DL-320): the replay cache starts
2016-01-04, and Tiingo serves no prices for the names that failed then (LEH, BSC, ENRNQ answer with
no dates; `WM` now means Waste Management), so that test would drop the worst losers.

## 2. Hypothesis

On **falling sessions**, a session whose previous SPY close sits below the mean of SPY's 200 closes
up to and including that one:

- **H1:** `target-25` (take-profit, 25 bps a side) earns more than `stops-25` (the stop alone, same
  cost): dR, the difference in annualised return on falling sessions, has a 95 % interval wholly
  above 0.
- **BEHIND:** the interval is wholly below 0. **H0:** otherwise (indistinguishable).
- **Reported, no bar:** the same dR for `target-10`, `time10-25`, `trail-25`, `target-time10-25`,
  `cool5-25` (each against the stops arm of its cost); the primary pair on rising sessions; each
  arm's mean exposure and SPY's annualised return on falling and rising sessions.

**What follows, fixed now:** on H1, the planner specs a regime-switched arm (take-profit only while
SPY sits below its 200-session mean) for the S281 harness, and the operator decides whether to build
it; nothing in the fleet changes on this result alone, because every cached session has been read.
On H0 or BEHIND, the stop alone stays (ADR-0033), and the question reopens only with survivorship-free
stock data before 2016.

## 3. Data

- **EXP-022's twelve sealed arms**, OneDrive `exp022-2026-10-21/arms/`: each `equity.csv` (date,
  `equity_cents`, `long_cents`), 2017-01-03 → 2026-09-25, from the real pipeline at `v0.128.06` on
  the survivorship-free S&P 500 cache. Seal `seal.txt` SHA-256 `020ebb5e…`, re-hashed before scoring.
- **SPY closes**, `sp500_benchmark.csv.gz` (SHA-256 `f40b8b60…`), 2016-01-04 →, so the 200-session
  mean exists from the first scored session.
- **The split, measured from SPY alone before any arm is read:** 2,445 session pairs; **404 falling**
  (2018: 43, 2019: 28, 2020: 59, 2022: 203, 2023: 17, 2025: 42, 2026: 12), 2,041 rising.
- **Seen before:** EXP-022's verdict (read 2026-10-26) gave each arm's whole-window and half-window
  dR, and its report has a per-year table; 2022 holds half the falling sessions. So this is a
  fixed-rule reading of arms already scored, not a blind test, and it cannot confirm anything alone.

## 4. Tools and setup

Intel i7-7660U, Windows 10, Python 3.12 (`python -I`, standard library only). Script
`exp037_score.py` in OneDrive `exp037-2026-10-27/`, SHA-256 `8a4f2096…` (Appendix S). Stationary
bootstrap as EXP-022's: 10,000 resamples, mean block 20, seed 0, one draw for every pair in a
family, percentile interval. Annualised return = exp(mean daily log return × 252) − 1, in points.

## 5. How it was conducted

1. `count` mode reads SPY only and prints the split (section 3). Done before this commit.
2. This record is committed: the pre-registration.
3. The EXP-022 seal is re-hashed (72 of 72 lines must match), then `score` runs once. It refuses if
   any arm lacks a window session.
4. Each arm's daily log return on session *t* is log(equity *t* / equity *t−1*); exposure is
   `long_cents / equity_cents` at *t−1*. The falling sessions are bootstrapped as one sequence.
5. Sections 6–8 are written from the output, with no change to the rule.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

Primary: dR = annualised return of `target-25` minus `stops-25` over EXP-022's falling sessions (the
previous SPY close below the mean of its last 200 closes), 404 sessions; stationary bootstrap 10,000,
mean block 20, seed 0. H1 if the 95 % interval's lower bound > 0, BEHIND if its upper bound < 0, H0
otherwise. Secondaries reported without a bar. H1 → a regime-switched arm is specced, the operator
decides on building; H0 or BEHIND → the stop alone stays. Script SHA-256
`8a4f20962f8118c81b902a2795eb833dcc0b6d3168162cfb0d3fb16e6e7076b5`.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

`exp037_score.py`, OneDrive `exp037-2026-10-27/`; run from that folder:
`python -I exp037_score.py count --spy ../sp500_benchmark.csv.gz`, then
`python -I exp037_score.py score --spy ../sp500_benchmark.csv.gz --arms ../exp022-2026-10-21/arms --out exp037.json`.
Verbatim copy to follow with the results.
