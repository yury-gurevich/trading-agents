# EXP-018 — With boundary fits accepted, does GARCH clear the bar on a history the fleet can supply?

**Status:** PRE-REGISTERED 2026-09-28 (planner). **Nothing has been simulated or scored.** Sections 1–5 are the
pre-registration; they are committed before the first simulated path and not changed in substance after it.
**Decision / origin:** [DL-240](../../design-log.md) · operator, 2026-09-28: *"run EXP-018"* · work-queue **92** ·
follows [EXP-017](EXP-017-block-bootstrap-and-garch-barrier-probabilities.md) · **Cost:** $0 (local simulation;
one read-only Alpaca request for the side measurement).

## 1. Why we needed this experiment

EXP-017 found GARCH(1,1) the only model with skill on the fleet's 203 bars (+1.47 % over climatology; +2.26 %
on full history), but its verdict was INSUFFICIENT: 6.2 % of fits fell back, against a 2 % limit. A check after
scoring showed almost all of them were estimates on the persistence boundary (α + β = 1), which the acceptance
rule rejected by requiring α + β strictly below 1, not optimiser failures. And no model cleared the 2 % bar on
the history production has. Since S238 the provider can fetch SIP bars with a safe `end`, so a longer history
per run is possible. This experiment settles whether GARCH, fitted properly, clears the bar on a depth
production can supply, and what that depth costs to fetch. It decides whether item 92's live ledger is built,
and on which model and depth.

## 2. Hypothesis

For each depth *d* in {**203** bars (today's fleet), **756** bars (~3 years)}:

- **H1(d):** GARCH at depth *d* has Brier skill against climatology of at least **2 %** (1 − Brier ÷
  Brier_climatology), with the 95 % interval's lower bound above zero, **and** at most 2 % failed fits.
- **H2:** GARCH at 756 bars has a lower Brier than at 203 bars, 95 % interval of the difference below zero
  (more history helps).
- **Production candidate:** the shallowest depth for which H1 holds. If neither holds, the full-history result
  is reported for reference only, and the ledger is not built on GARCH as it stands.
- **H0:** H1 fails at both depths.

## 3. Data

The replay cache, exactly as in EXP-016 and EXP-017: `bars.csv.gz` (sha-256 prefix `12374e3e5493`), 263,005
SIP split- and dividend-adjusted daily bars, 98 names, 2016-01-04 → 2026-09-16; `vix.csv.gz` (prefix
`e5d4fe621031`). EXP-011's decisions rebuilt from it (reproduction check: **47,485** cases, realised 0.285 /
0.480 / 0.235, else the run stops).

**Scored set (primary):** decisions dated 2018–2026 that have at least **756** prior daily moves, so every depth
exists for every scored case (from about 2019-01 for most stocks). The same cases for every model.
**Secondary (for comparison with EXP-017):** 203 bars and full history on all 2018–2026 decisions.

**Side measurement (live, read-only):** one fetch through the fleet's own provider code
(`market_source_from_settings`, SIP default, main at the run) of the 99 live universe names plus SPY over a
window ending today that holds 756 sessions: pages, bars, bytes, seconds, and any refusal.

## 4. Tools and setup

As EXP-017: Intel Core i7-7660U (2 cores / 4 threads), 15.9 GB RAM, Windows 10 Pro 19045; Python 3.13.2 through
uv 0.8.14; numpy 2.4.6; arch 8.0.0, scipy 1.17.1, statsmodels 0.15.0 loaded for the run only; 4 worker
processes, one per stock. **Seeds:** paths `default_rng([20260928, stock_index])`; interval resampling
`20260929`, 1,000 resamples of whole decision dates.

## 5. How it was conducted

**Model:** GARCH(1,1), Student-t innovations, filtered historical simulation, exactly as EXP-017's `G` (fitted
per stock and calendar month on the history available at the month's first decision; volatility follows the
recursion; each simulated day's close, high and low are a past day's standardised shape rescaled; 1,000 paths
× 10 sessions per case), with **one change to fit acceptance:**

- A fit is **accepted** when the optimiser converges and ω > 0, α ≥ 0, β ≥ 0, **α + β ≤ 1** (the boundary is
  accepted).
- In the recursion and simulation, persistence is capped: if α + β > 0.999, α and β are scaled in proportion
  so that α + β = 0.999, keeping variance finite. The count of capped fits is reported.
- A **failed** fit is non-convergence or an exception; it reuses the previous month's accepted parameters, and
  more than 2 % failed fits at a depth fails H1 at that depth.

**Depths:** 203, 756 and full, each fitted and simulated separately.

**Scoring:** 3-outcome Brier and skill against climatology with date-resampled 95 % intervals for each depth
on the primary set; H2's difference; calibration buckets (≥ 100 cases) for P(stop first) and P(target first);
Brier by year and by VIX regime; fit counts (accepted, capped, failed) per depth. Secondary: 203 and full on
all 2018–2026 decisions.

**Side measurement:** run once, after the simulation, from the main checkout with `.env`.

## 6. Results

*(Empty until the run.)*

## 7. Conclusions

*(Empty until the run.)*

## 8. Recommended code changes, and how to implement them

*(Empty until the run.)*

## Appendix P — Pre-registration (frozen)

Sections 1–5 above, as committed before any path was simulated (the commit is named here after the run).

## Appendix R — Run record

*(Empty until the run.)*

## Appendix S — Scripts

*(Empty until the run.)*
