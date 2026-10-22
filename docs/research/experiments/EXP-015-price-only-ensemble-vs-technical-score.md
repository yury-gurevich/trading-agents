# EXP-015 — Does a price-only ensemble rank names better than the analyst's technical score, out of sample?

**Status:** PRE-REGISTERED 2026-09-27 (planner). **CLOSED 2026-10-23: FAIL (H0).** The
walk-forward was recorded first (`3eac394d`) with bars 1 and 2 failing; the holdout was then
touched once and bar 3 held, which cannot change the verdict. Everything under *Purpose* and
*Process* was fixed before the first fit and is unchanged. A change after the first fit is a new
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

Outputs go to OneDrive `trading-agents-data\experiments\EXP-015\`: per-fold IC tables, the
bootstrap, the holdout line, and the control. None of them go in the repo (the SIP bars are
licensed). Code goes under `scripts/` with tests on synthetic bars.

**Tooling:** [S289](../../sprints/sprint-289-exp-015-has-the-tooling-its-pre-registration-fixes.md), merged 2026-10-22 at `1c91c21e`. Where *Process* is silent, [DL-313](../../design-log.md) decides, before any fit (feature windows, missing values, the four adjustment errors, the folds' gap, the bootstrap's sessions, the top decile's costs).

### Run record

- **Code:** `1c91c21e` (clean), from a detached worktree; Python 3.13.2, numpy 2.5.3, LightGBM 4.7.0;
  Windows 10, i7-7660U; one job at a time, BelowNormal priority. Seeds as *Process* fixes them
  (LightGBM 0, bootstrap 0, the control's shuffle 0).
- **`panel`:** 2026-10-22 11:43 → 13:38 UTC. 1,209,946 rows over 2,698 sessions; 715,852 primary
  (scanner survivors), 1,185,447 secondary; 139,294 member-sessions not offered; 55,782 rows without
  a sector. The first session with a row is **2016-10-17**: the expanding window starts at the
  cache's first session, and no name has the history the scanner and features need before then.
  Panel SHA-256 `aff1a727b1c0e9d1e9ccef3577d0aa2143150e7396702da3023693bccee52b52`; cache file
  checksums in `panel.json`.
- **`walk-forward`:** 13:38 → 13:48 UTC. **`walk_forward.json` SHA-256
  `d375dbb9b17fff5e453d44e0cf70e0c3699bd1c3e49e033872fa1afc60ed63ff`** (re-hashed independently).
  This is the digest the holdout stage must be given.

### Walk-forward result (recorded 2026-10-23, before the holdout was touched)

| Bar | Reading | Holds |
| --- | --- | --- |
| 1: mean IC difference ≥ 0.01, 95 % CI lower bound > 0 | **+0.0123** over 1,761 test sessions; the bootstrap on every 10th session (177): mean +0.0048, **[−0.0219, +0.0313]** | **no** |
| 2: the ensemble's IC ahead in ≥ 5 of 7 folds | **3 of 7** (2018, 2019, 2021) | **no** |
| Control: shuffled target, the IC difference's CI contains 0 | mean −0.0023, [−0.0119, +0.0062] | yes: no leakage seen |

Mean daily rank IC against the 10-session forward excess return, primary universe:

| Fold (test year) | Train rows / test rows | Technical score | Ensemble | Composite | Ridge | LightGBM |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | 99,726 / 72,570 | +0.0018 | +0.0303 | +0.0385 | +0.0199 | +0.0108 |
| 2019 | 174,974 / 72,107 | −0.0638 | −0.0041 | −0.0097 | −0.0068 | +0.0074 |
| 2020 | 244,141 / 56,694 | +0.0085 | +0.0068 | −0.0020 | +0.0041 | +0.0141 |
| 2021 | 300,547 / 104,596 | −0.0392 | +0.0274 | +0.0300 | +0.0153 | +0.0256 |
| 2022 | 405,538 / 46,922 | −0.0116 | −0.0217 | −0.0074 | −0.0388 | −0.0120 |
| 2023 | 454,842 / 58,043 | +0.0145 | −0.0153 | −0.0096 | −0.0084 | −0.0150 |
| 2024 | 511,553 / 82,082 | +0.0206 | −0.0069 | −0.0077 | −0.0040 | −0.0037 |
| **All 1,761 sessions** | | **−0.0099** | **+0.0024** | +0.0046 | −0.0027 | +0.0039 |

**Reported, not barred.**

- **The difference is the baseline's, not the ensemble's.** Over the seven years the ensemble's
  mean IC is +0.0024 and the technical score's is −0.0099: neither ranks the survivors; the
  technical score sits slightly below zero, worst in 2019 (−0.064) and 2021 (−0.039).
- **Decay**, all sessions: the technical score −0.0046 at 5 sessions, −0.0126 at 20; the ensemble
  +0.0013 and +0.0034.
- **Net long-only top decile** (25 bps a side, rebalanced every 10 sessions, compounded per fold): the
  ensemble ahead in 4 of 7 folds (2018, 2019, 2021, 2023), the technical score in 3 (2020, 2022,
  2024). Costs take about 8 to 13 points a year from either.
- **Secondary universe** (every member with 253 bars; descriptive): technical score −0.0044, ensemble
  +0.0077 over all sessions; the ensemble ahead in 5 of 7 folds (behind in 2020 and 2024). Not
  barred: the bar reads the primary universe only.
- **LightGBM's gain**, share averaged over the folds: dollar-volume rank 0.124, 60-session beta
  0.111, 252-skip-21 return 0.093, residual volatility 0.071, volume ratio 20/120 0.066; every
  sector-ranked return 0.032 or less.
- **The control** reads about zero for every model (all sessions: technical score +0.0010, ensemble
  −0.0001).

Files: `panel.json`, `panel.npz`, `walk_forward.json`, `walk_forward.md` in the OneDrive folder.

### Holdout result (touched once, 2026-10-22 13:51 → 13:53 UTC, after `3eac394d` recorded the above)

`holdout --walk-forward-sha256 d375dbb9…` from the same tree and Python. One fit on 2016-10-17 →
2024-12-09 (593,535 primary rows; the 15-session gap before the test), tested on 2025-01-02 →
2026-09-25 (434 sessions, 424 with a 10-session target; 118,027 rows). `holdout.json` SHA-256
`fd8bb0ccdd5676fcc2ca474be280db49eb4bb38fdb167946a1cf692a481a562c`.

| Bar | Reading | Holds |
| --- | --- | --- |
| 3: holdout IC difference > 0, and the ensemble's net top decile ahead | **+0.0345** over 424 sessions; net top decile, 43 rebalances: ensemble **+28.6 %**, technical score **−3.1 %** (gross +48.3 % and +16.3 %) | yes |
| **Verdict** (all three required) | bars 1 and 2 failed in the walk-forward | **FAIL** |

Holdout, reported: mean IC technical score −0.0070, ensemble +0.0275 (composite +0.0452, ridge
+0.0099, LightGBM +0.0113); decay, technical score −0.0061 at 5 sessions and −0.0054 at 20,
ensemble +0.0186 and +0.0344; secondary universe technical score −0.0011, ensemble +0.0204, net top
decile +13.9 % against +1.1 %.

Files: `holdout.json`, `verdict.md`. 🪤 The pages (`walk_forward.md`, `verdict.md`) print the
secondary universe's rows with no header of their own (in `verdict.md` both rows read `holdout`; the
second is the secondary universe). The JSON is the record; the stage refuses a second touch, so the
pages are never rendered again.

## Interpretation

*Written 2026-10-23 from the recorded results only.* The plan said: pass, a spec that feeds the
ensemble to the forecaster's shadow loop, with live shadowing waiting on work-queue item 89 (IEX
volume); fail, the record says so, and nothing is built.

**FAIL: nothing is built.** Out of sample, a price-only ensemble does not rank the scanner's
survivors better than the technical score by the pre-registered bar. Over seven walk-forward
years its lead is +0.0123 in mean IC, but the interval runs from −0.0219 to +0.0313 and it leads
in only 3 of 7 years. The holdout's clear lead (+0.0345, and a net top decile 32 points ahead)
is one 21-month stretch. The walk-forward has years like it (2018, 2021) and years that reverse
it (2022 to 2024), so it is not evidence of a lasting edge.

**What the record shows about the baseline, which *Purpose* says carries most of the price-only
pipeline's ranking:** over 1,761 walk-forward sessions the analyst's technical score has a mean rank
IC of **−0.0099** against the 10-session forward excess return (−0.0126 at 20 sessions), and
**−0.0070** on the holdout. By year it is positive in four of seven (at most +0.0206, in 2024) and
negative in three (down to −0.0638, in 2019). Taken whole, it ranks the survivors no better than
chance. EXP-015 was not built to test that: its bar compares two rankers and says nothing about
either one's absolute skill. This is a reported reading, not a verdict on the technical score.
*Purpose* says either answer informs G-EDGE, and this is the part that does.
