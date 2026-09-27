# EXP-015 — Does a price-only ensemble rank names better than the analyst's technical score, out of sample?

**Status:** PRE-REGISTERED 2026-09-27 (planner). **No model has been fitted.** Everything under
*Purpose* and *Process* is fixed before the first fit. A change after the first fit is a new
experiment, not an edit to this one.
**Decision:** [DL-236](../../design-log.md) (operator, 2026-09-27) · work-queue **90** · runs beside
E17.4 ([S237](../../sprints/sprint-237-on-the-fleets-own-inputs-the-replay-decides-what-the-fleet-decided.md)).
**LLM cost:** $0.

## Purpose

**Question.** On the survivorship-free S&P 500 cache (S235), does a small ensemble built from price
and volume alone rank the names that pass the scanner better than the analyst's technical score
does? The test is out of sample and net of costs.

**Why it matters.** The analyst's technical score is a hand-built rule set (`score_technical`,
`agents/analyst/domain/technical_rules.py:91`), and the replay is price-only (DL-232), so it carries
most of the price-only pipeline's ranking. If a fitted ensemble ranks clearly better, it enters the
forecaster's existing shadow loop (`shadow=True`, never gates; promotion through the registry,
ADR-0010). If it does not, nothing is built. Either answer informs G-EDGE.

**Hypothesis (H1).** Over the walk-forward test folds, the ensemble's mean daily rank IC against the
10-session forward excess return exceeds the technical score's by at least **0.01**. The 95 %
confidence interval of the difference lies above zero. On the untouched holdout, the ensemble's
long-only top decile, net of **25 bps** per side, beats the technical score's.

**H0.** Any of the above fails.

## Process

Everything below is fixed now.

**Data.** The S235 cache (OneDrive `trading-agents-data`, never the repo): point-in-time members,
split-adjusted SIP OHLCV, SPY and VIX, 2016-01-04 → the last cached session. Sector labels are
today's Finnhub industries (a mild look-ahead, named in DL-236; 13 % of symbols have none). No
fundamentals, news or earnings dates.

**Universe per session (primary).** Point-in-time members that pass the scanner's filters on that
session, computed by the fleet's own `apply_filters` with the pack's settings and SIP volume. This
is the set the technical score actually ranks. **Secondary, descriptive only:** every member with
at least 253 bars.

**Target.** The forward excess return over SPY from session *d+1*'s open to session *d+10*'s close:
entry at the next open, which matches the fleet's after-close day orders. Horizons 5 and 20 are
reported for decay only.

**Baseline.** The analyst's technical score for each name on each session, computed by the fleet's
own code (`score_technical` through the analyst domain, as the S235 replay computes it). It is not
re-implemented.

**Features (fixed list, all computed only from bars up to and including *d*).** Returns over 5, 20,
60 and 120 sessions, and 252 skipping the latest 21; distance from the 252-session high; 20- and
60-session realised volatility; ATR %; 60-session beta and residual volatility to SPY; volume
ratios 5/60 and 20/120; dollar-volume rank; relative strength over 120 sessions vs SPY; and the
same five return features ranked within today's sector. Every feature is cross-sectionally ranked
per session to [0, 1].

**Models (exactly three, fixed hyper-parameters, no tuning):**

1. **Rank composite.** Sign each feature by its train-fold IC; take the equal-weight mean. Nothing
   else is fitted.
2. **Ridge** (closed form, numpy) on the ranked features, λ = 1.0, target the cross-sectionally
   ranked forward return.
3. **LightGBM regressor** (the forecaster extra's): 200 trees, depth 3, learning rate 0.05, 31
   leaves maximum, `min_data_in_leaf` 500, `feature_fraction` 0.8, seed 0.

**The ensemble** is the equal-weight mean of the three models' per-session ranks. **Only the
ensemble is tested against the bar.** The three components are reported, never promoted on their
own.

**Walk-forward.** Expanding train window from 2016-01-04. Seven annual test folds, 2018 → 2024.
Before each test fold, **purge 10 sessions** (the horizon) and **embargo 5**. Models are refitted per
fold.

**Holdout.** 2025-01-02 → the last cached session. It is touched **once**, after the walk-forward
result is recorded here.

**Metrics.** Per-session Spearman rank IC of the prediction vs the target, averaged per fold and
overall. Inference uses non-overlapping sessions (every 10th) with a stationary block bootstrap
(block 20, 10,000 resamples, seed 0) on the IC difference. The decile spread is top minus bottom.
The **long-only top decile** is equal-weight, rebalanced every 10 sessions, with a turnover cost of
25 bps per side; the baseline's top decile is built the same way.

**The pass bar (all three required).**

1. Walk-forward mean IC difference (ensemble − baseline) **≥ 0.01**, bootstrap 95 % CI lower bound
   **> 0**.
2. The ensemble's IC beats the baseline's in **≥ 5 of the 7** folds.
3. On the holdout, the IC difference is **> 0** and the ensemble's net long-only top decile beats the
   baseline's.

**Reported, not barred:** IC at 5 and 20 sessions (decay), the secondary universe, the three
components, per-year results, and the feature importances of the LightGBM model.

**Controls.** A shuffled-target run of the same pipeline must return an IC difference within its own
bootstrap noise. If it does not, there is leakage and the experiment stops. The walk-forward records
the train and test date ranges per fold, and a test asserts that no feature reads a bar after *d*.

## Delivery

*Pending.* Outputs go to OneDrive `trading-agents-data\experiments\EXP-015\`: per-fold IC tables, the
bootstrap, the holdout line, and the control. None of them go in the repo (the SIP bars are
licensed). Code goes under `scripts/` with tests on synthetic bars.

## Interpretation

*Pending — written only from the recorded results.* Pass: a spec that feeds the ensemble to the
forecaster's shadow loop, with live shadowing waiting on work-queue item 89 (IEX volume). Fail: the
record says so, and nothing is built.
